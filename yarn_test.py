import json, time, os, sys, glob, torch, soundfile as sf
torch.set_num_threads(4)
sys.path.insert(0, 'yarngpt')
from yarngpt.audiotokenizer import AudioTokenizerV2
from transformers import AutoModelForCausalLM
at = AudioTokenizerV2('saheedniyi/YarnGPT2', 'wavtokenizer_large_speech_320_24k.ckpt', 'wavtokenizer_mediumdata_frame75_3s_nq1_code4096_dim512_kmeans200_attn.yaml')
model = AutoModelForCausalLM.from_pretrained('saheedniyi/YarnGPT2', torch_dtype='auto').to(at.device)
print('speakers dir', sorted(os.listdir('yarngpt/default_speakers')) if os.path.isdir('yarngpt/default_speakers') else glob.glob('yarngpt/**/*.json', recursive=True)[:50], flush=True)
S = json.load(open('samples.json'))
tests = [('yoruba', 'yoruba_female2', S['yo'][1]), ('igbo', 'igbo_female2', S['ig'][1]), ('hausa', 'hausa_female1', S['ha'][1]),
         ('english', 'idera', 'Now look closely. This white, flaky material is sodium hydroxide, which the market calls caustic soda.')]
os.makedirs('out', exist_ok=True)
for lang, spk, text in tests:
    try:
        t0 = time.time()
        prompt = at.create_prompt(text, lang=lang, speaker_name=spk)
        ids = at.tokenize_prompt(prompt)
        out = model.generate(input_ids=ids, temperature=0.1, repetition_penalty=1.1, max_length=4000)
        audio = at.get_audio(at.get_codes(out))
        a = audio.squeeze().cpu().numpy(); sf.write('out/%s_%s.wav' % (lang, spk), a, 24000)
        print('OK', lang, spk, 'audio', round(len(a) / 24000, 1), 's', 'took', round(time.time() - t0, 1), 's', flush=True)
    except Exception as e:
        print('FAIL', lang, spk, repr(e)[:300], flush=True)
