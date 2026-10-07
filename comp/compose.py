"""Assemble one WODDI v2 video: demo clips + narration + overlays + captions + music.
Usage: python3 compose.py <course> <module> <lang> <outdir>
Needs: scripts/<course>/<module>[.<lang>].json, voice/<lang>/<course>/<module>/s<shot>_<k>.wav,
       clips/<demo>-v<n>.mp4, music.wav. Writes <outdir>/<module>.mp4, .vtt, .jpg"""
import json, os, sys, subprocess, random, shutil, glob, wave, contextlib, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24; W, H = 854, 480; XF = 0.4          # cross-dissolve between shots (s)
LEAD, GAP, TAIL = 0.45, 0.38, 0.55            # narration timing inside a shot (s)
WORD = {
 'step': {'en': 'Step', 'fr': 'Étape', 'pt': 'Passo', 'ar': 'الخطوة', 'yo': 'Ìgbésẹ̀', 'ha': 'Mataki', 'ig': 'Nzọụkwụ', 'sw': 'Hatua'},
 'module': {'en': 'Module', 'fr': 'Module', 'pt': 'Módulo', 'ar': 'الوحدة', 'yo': 'Ìpín', 'ha': 'Babi', 'ig': 'Nkebi', 'sw': 'Moduli'},
 'next': {'en': 'Continue with the lessons below', 'fr': 'Continuez avec les leçons ci-dessous', 'pt': 'Continue com as lições abaixo',
          'ar': 'تابعي الدروس في الأسفل', 'yo': 'Ẹ tẹ̀síwájú pẹ̀lú àwọn ẹ̀kọ́ ní ìsàlẹ̀', 'ha': 'Ci gaba da darussan da ke ƙasa',
          'ig': 'Gaa n\'ihu na nkuzi ndị dị n\'okpuru', 'sw': 'Endelea na masomo yaliyo hapa chini'},
 'photo': {'en': 'Real photo', 'fr': 'Vraie photo', 'pt': 'Foto real', 'ar': 'صورة حقيقية', 'yo': 'Fọ́tò gidi', 'ha': 'Hoto na gaske', 'ig': 'Foto n\'ezie', 'sw': 'Picha halisi'},
}
COURSE_TITLE = {
 'soap-making-laundry-bath-soap': {'en': 'Soap Making (Laundry & Bath Soap)', 'fr': 'Fabrication de savon', 'pt': 'Fabrico de sabão', 'ar': 'صناعة الصابون', 'yo': 'Ṣíṣe Ọṣẹ', 'ha': 'Haɗa Sabulu', 'ig': 'Ime Ncha', 'sw': 'Kutengeneza Sabuni'},
 'liquid-soap-shampoo-disinfectants': {'en': 'Liquid Soap, Shampoo & Disinfectants', 'fr': 'Savon liquide, shampoing et désinfectants', 'pt': 'Sabão líquido, champô e desinfectantes', 'ar': 'الصابون السائل والشامبو والمطهرات', 'yo': 'Ọṣẹ Olómi, Ṣámpù àti Apakòkòrò', 'ha': 'Sabulun Ruwa, Shamfu da Maganin Kashe Ƙwayoyi', 'ig': 'Ncha Mmiri, Shampoo na Ọgwụ Nje', 'sw': 'Sabuni ya Maji, Shampuu na Viuatilifu'},
 'detergent-cleaning-products-production': {'en': 'Detergent & Cleaning Products', 'fr': 'Détergents et produits d\'entretien', 'pt': 'Detergentes e produtos de limpeza', 'ar': 'المنظفات ومواد التنظيف', 'yo': 'Ọṣẹ Ìfọṣọ àti Ohun Ìmọ́tótó', 'ha': 'Sabulun Wanki da Kayan Tsabta', 'ig': 'Ncha Ịsa Ákwà na Ihe Nhicha', 'sw': 'Sabuni na Bidhaa za Usafi'},
}
# real photos shown as a small framed insert on some shots (public domain / CC0 / CC BY, credited)
PHOTOS = json.load(open(os.path.join(ROOT, 'comp', 'photos.json'))) if os.path.exists(os.path.join(ROOT, 'comp', 'photos.json')) else {}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit('FAILED: ' + ' '.join(cmd[:6]) + '\n' + r.stderr[-1500:])
    return r.stdout


def wav_dur(p):
    with contextlib.closing(wave.open(p)) as w: return w.getnframes() / w.getframerate()


def probe_dur(p):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).strip())


def vtt_time(s):
    return '%02d:%02d:%06.3f' % (s // 3600, s % 3600 // 60, s % 60)


def main(course, mod, lang, out):
    sp = os.path.join(ROOT, 'scripts', course, mod + ('' if lang == 'en' else '.' + lang) + '.json')
    S = json.load(open(sp))
    rtl = lang == 'ar'
    work = os.path.join(out, '_w_' + mod + '_' + lang); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
    vdir = os.path.join(ROOT, 'voice', lang, course, mod)
    avail = {}
    for f in glob.glob(os.path.join(ROOT, 'clips', '*.mp4')):
        n = os.path.basename(f)[:-4]; d, v = n.rsplit('-v', 1); avail.setdefault(d, []).append(int(v))
    seed = int(hashlib.md5((course + mod).encode()).hexdigest()[:6], 16)
    random.seed(seed)
    used = {}
    shots = S['shots']; n = len(shots)
    # 1) narration per shot, timings, captions
    cues = []; durs = []; t = 0.0; aparts = []
    for i, sh in enumerate(shots):
        files = sorted(glob.glob(os.path.join(vdir, 's%02d_*.wav' % i)) + glob.glob(os.path.join(vdir, 's%02d_*.opus' % i)), key=lambda p: int(p.rsplit('_', 1)[1].split('.')[0]))
        if len(files) != len(sh['say']): raise SystemExit('voice missing for shot %d (%d of %d)' % (i, len(files), len(sh['say'])))
        lt = LEAD if i else 1.2
        st = t + lt; seg = [('sil', lt)]
        for k, (f, txt) in enumerate(zip(files, sh['say'])):
            d = wav_dur(f) if f.endswith('.wav') else probe_dur(f); cues.append((st, st + d, txt)); seg.append(('wav', f))
            st += d
            if k < len(files) - 1:
                g = GAP + random.uniform(-0.06, 0.12); seg.append(('sil', g)); st += g
        tail = TAIL + (2.8 if i == n - 1 else 0.0)
        seg.append(('sil', tail)); st += tail
        durs.append(st - t); aparts.append(seg); t = st
    total = t
    # narration track
    lst = os.path.join(work, 'alist.txt')
    with open(lst, 'w') as fh:
        k = 0
        for seg in aparts:
            for kind, v in seg:
                if kind == 'sil':
                    p = os.path.join(work, 'sil%04d.wav' % k); k += 1
                    run(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', '%.3f' % v, '-c:a', 'pcm_s16le', p])
                    fh.write("file '%s'\n" % p)
                else:
                    p = os.path.join(work, 'v%04d.wav' % k); k += 1
                    run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-ar', '24000', '-ac', '1', '-c:a', 'pcm_s16le', p]); fh.write("file '%s'\n" % p)
    narr = os.path.join(work, 'narr.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'pcm_s16le', narr])
    # 2) overlays
    items = []; plan = []
    title = S['title']; ctitle = COURSE_TITLE.get(course, {}).get(lang, '')
    mnum = mod.lstrip('m')
    for i, sh in enumerate(shots):
        ov = []
        if i == 0:
            items.append({'id': 'title', 'kind': 'title', 'kicker': '%s %s' % (WORD['module'][lang], mnum), 'text': title, 'course': ctitle}); ov.append(('title', 0.6, durs[0] - 0.3))
        if sh.get('label'):
            items.append({'id': 'l%d' % i, 'kind': 'label', 'text': sh['label']}); ov.append(('l%d' % i, 0.7, durs[i] + XF))
        if sh.get('banner'):
            items.append({'id': 'b%d' % i, 'kind': 'banner', 'text': sh['banner']}); ov.append(('b%d' % i, 1.0, durs[i] + XF))
        if sh.get('step') is not None:
            items.append({'id': 's%d' % i, 'kind': 'step', 'text': '%s %d' % (WORD['step'][lang], sh['step'])}); ov.append(('s%d' % i, 0.4, durs[i] + XF))
        if sh.get('card'):
            c = sh['card']; items.append({'id': 'c%d' % i, 'kind': 'card', 'title': c['title'], 'rows': c['rows'], 'note': c.get('note')}); ov.append(('c%d' % i, 1.4, durs[i] + XF))
        ph = PHOTOS.get(sh['demo'])
        if ph and not sh.get('card') and used.get('photo_' + sh['demo']) is None:
            used['photo_' + sh['demo']] = 1
            items.append({'id': 'p%d' % i, 'kind': 'photo', 'src': os.path.join(ROOT, ph['file']), 'title': WORD['photo'][lang], 'credit': ph['credit']})
            ov.append(('p%d' % i, 2.2, min(durs[i] - 0.3, 9.0)))
        if i == n - 1:
            items.append({'id': 'end', 'kind': 'end', 'text': WORD['next'][lang]}); ov.append(('end', durs[i] - 3.0, durs[i] + 1))
        plan.append(ov)
    items.append({'id': 'bug', 'kind': 'bug'})
    jf = os.path.join(work, 'ov.json'); json.dump({'lang': lang, 'rtl': rtl, 'items': items}, open(jf, 'w'), ensure_ascii=False)
    run(['node', os.path.join(ROOT, 'comp', 'overlays.js'), jf, os.path.join(work, 'ov')])
    # 3) one video segment per shot
    segs = []
    for i, sh in enumerate(shots):
        d = sh['demo']
        if d not in avail and d.startswith('outro_'):      # the outro reuses its title scene
            d = {'outro_bars': 'title_soap', 'outro_bottles': 'title_liquid', 'outro_workshop': 'title_workshop'}[d]
        vs = sorted(avail.get(d, [0]))
        occ = used.get(d, 0); used[d] = occ + 1
        v = vs[(occ + seed) % len(vs)] if d in avail else 0
        clip = os.path.join(ROOT, 'clips', '%s-v%d.mp4' % (d, v))
        if not os.path.exists(clip): raise SystemExit('missing clip ' + clip)
        L = probe_dur(clip); need = durs[i] + (XF if i < n - 1 else 0)
        sp_ = min(max(need / L, 1.0), 1.35)        # slow the action a little if the narration is longer
        hold = max(0.0, need - L * sp_)
        zoom_rate = 0.00035 + (0.0002 if hold > 2 else 0)
        fx = ('setpts=%.4f*PTS,fps=%d,scale=%d:%d:flags=lanczos,tpad=stop_mode=clone:stop_duration=%.3f,'
              "zoompan=z='min(1+%.5f*on,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=%d,"
              'eq=saturation=1.06:contrast=1.03,vignette=PI/6,trim=duration=%.3f,setpts=PTS-STARTPTS' % (sp_, FPS, W, H, hold + 0.1, zoom_rate, W, H, FPS, need))
        inputs = ['-i', clip]; fc = '[0:v]' + fx + '[v0]'; last = 'v0'
        ovs = plan[i] + ([('bug', 0, need)] if i not in (0, n - 1) else [])
        for j, (oid, a, b) in enumerate(ovs):
            inputs += ['-loop', '1', '-t', '%.3f' % need, '-i', os.path.join(work, 'ov', oid + '.png')]
            fd = 0.35
            fc += ';[%d:v]format=rgba,fade=in:st=%.3f:d=%.2f:alpha=1,fade=out:st=%.3f:d=%.2f:alpha=1[o%d]' % (j + 1, max(0, a), fd, max(a + fd, b - fd), fd, j)
            fc += ';[%s][o%d]overlay=0:0:shortest=1[v%d]' % (last, j, j + 1); last = 'v%d' % (j + 1)
        sf = os.path.join(work, 'seg%02d.mp4' % i)
        run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', fc, '-map', '[%s]' % last, '-t', '%.3f' % need, '-r', str(FPS),
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', sf])
        segs.append((sf, need))
    # 4) join with cross-dissolves
    inputs = []; fc = ''; prev = '0:v'; off = 0.0
    for j, (f, d) in enumerate(segs): inputs += ['-i', f]
    for j in range(1, len(segs)):
        off += segs[j - 1][1] - XF
        fc += ('' if j == 1 else ';') + '[%s][%d:v]xfade=transition=fade:duration=%.2f:offset=%.3f[x%d]' % (prev, j, XF, off, j); prev = 'x%d' % j
    vid = os.path.join(work, 'video.mp4')
    run(['ffmpeg', '-v', 'error', '-y'] + inputs + ['-filter_complex', fc, '-map', '[%s]' % prev, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-pix_fmt', 'yuv420p', vid])
    # 5) audio: narration (warm EQ, gentle compression) over a quiet original music bed
    music = os.path.join(ROOT, 'comp', 'music.wav')
    mix = os.path.join(work, 'mix.wav')
    run(['ffmpeg', '-v', 'error', '-y', '-i', narr, '-stream_loop', '-1', '-i', music, '-filter_complex',
         '[0:a]highpass=f=80,equalizer=f=200:t=q:w=1:g=1.5,equalizer=f=3500:t=q:w=1.2:g=2,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,loudnorm=I=-17:TP=-2:LRA=9[n];'
         '[1:a]volume=0.10,afade=t=in:d=2,afade=t=out:st=%.2f:d=3[m];[n][m]amix=inputs=2:duration=first:normalize=0[a]' % max(0, total - 3),
         '-map', '[a]', '-t', '%.3f' % total, '-ar', '44100', '-ac', '1', mix])
    os.makedirs(out, exist_ok=True)
    final = os.path.join(out, mod + '.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', mix, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '26', '-tune', 'film',
         '-g', '96', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', '-shortest', final + '.part.mp4'])
    os.replace(final + '.part.mp4', final)
    with open(os.path.join(out, mod + '.vtt'), 'w') as fh:
        fh.write('WEBVTT\n\n')
        for k, (a, b, txt) in enumerate(cues): fh.write('%d\n%s --> %s\n%s\n\n' % (k + 1, vtt_time(a), vtt_time(b), txt))
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '2.5', '-i', final, '-frames:v', '1', '-q:v', '4', os.path.join(out, mod + '.jpg')])
    shutil.rmtree(work, ignore_errors=True)
    print('OK', course, mod, lang, '%.1fs' % total, '%.1f MB' % (os.path.getsize(final) / 1e6))


if __name__ == '__main__':
    main(*sys.argv[1:5])
