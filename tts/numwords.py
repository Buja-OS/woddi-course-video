"""Spell numbers as words for TTS voices that cannot read digits (Hausa, Igbo, Swahili, Yoruba, Arabic).
Handles integers up to 999,999, decimals (165.8), thousands separators (1,658), percents and ratios (1:19)."""
import re

# ── Swahili ──
SW1 = ['', 'moja', 'mbili', 'tatu', 'nne', 'tano', 'sita', 'saba', 'nane', 'tisa']
SW10 = ['', 'kumi', 'ishirini', 'thelathini', 'arobaini', 'hamsini', 'sitini', 'sabini', 'themanini', 'tisini']
def sw(n):
    if n == 0: return 'sifuri'
    p = []
    if n >= 1000: p.append('elfu ' + sw(n // 1000)); n %= 1000
    if n >= 100: p.append('mia ' + SW1[n // 100]); n %= 100
    tail = ''
    if n >= 10:
        tail = SW10[n // 10] + (' na ' + SW1[n % 10] if n % 10 else '')
    elif n: tail = SW1[n]
    if tail: p.append(('na ' if p else '') + tail)
    return ' '.join(p)

# ── Hausa ──
HA1 = ['', 'ɗaya', 'biyu', 'uku', 'huɗu', 'biyar', 'shida', 'bakwai', 'takwas', 'tara']
HA10 = ['', 'goma', 'ashirin', 'talatin', "arba'in", 'hamsin', 'sittin', "saba'in", 'tamanin', "casa'in"]
def ha(n):
    if n == 0: return 'sifili'
    p = []
    if n >= 1000:
        k = n // 1000; p.append('dubu' + ('' if k == 1 else ' ' + ha(k))); n %= 1000
    if n >= 100:
        h = n // 100; p.append('ɗari' + ('' if h == 1 else ' ' + HA1[h])); n %= 100
    if n >= 10:
        t, u = divmod(n, 10)
        if t == 1: p.append('goma' + (' sha ' + HA1[u] if u else ''))
        else: p.append(HA10[t] + (' da ' + HA1[u] if u else ''))
        n = 0
    if n: p.append(HA1[n])
    return ' da '.join(p)

# ── Igbo ──
IG1 = ['', 'otu', 'abụọ', 'atọ', 'anọ', 'ise', 'isii', 'asaa', 'asatọ', 'itoolu']
def ig(n):
    if n == 0: return 'efu'
    p = []
    if n >= 1000:
        k = n // 1000; p.append('puku ' + ig(k) if k > 1 else 'otu puku'); n %= 1000
    if n >= 100:
        h = n // 100; p.append('narị ' + IG1[h] if h > 1 else 'otu narị'); n %= 100
    if n >= 10:
        t, u = divmod(n, 10)
        p.append(('iri' if t == 1 else 'iri ' + IG1[t]) + (' na ' + IG1[u] if u else '')); n = 0
    if n: p.append(IG1[n])
    return ' na '.join(p)

# ── Yoruba (standard counting forms; subtractive vigesimal system) ──
YO_UNITS = {1: 'ọ̀kan', 2: 'méjì', 3: 'mẹ́ta', 4: 'mẹ́rin', 5: 'márùn-ún', 6: 'mẹ́fà', 7: 'méje', 8: 'mẹ́jọ', 9: 'mẹ́sàn-án', 10: 'mẹ́wàá'}
YO_ADD = {1: 'mọ́kàn', 2: 'méjì', 3: 'mẹ́tà', 4: 'mẹ́rìn'}       # forms used in "X lé" (added)
YO_SUB = {1: 'mọ́kàn', 2: 'méjì', 3: 'mẹ́tà', 4: 'mẹ́rìn', 5: 'márùn'}  # forms used in "X dín" (subtracted)
YO_TENS = {20: 'ogún', 30: 'ọgbọ̀n', 40: 'ogójì', 50: 'àádọ́ta', 60: 'ọgọ́ta', 70: 'àádọ́rin', 80: 'ọgọ́rin', 90: 'àádọ́rùn-ún', 100: 'ọgọ́rùn-ún'}
YO_TENS_OBJ = {20: 'lógún', 30: 'lọ́gbọ̀n', 40: 'lógójì', 50: 'láàádọ́ta', 60: 'lọ́gọ́ta', 70: 'láàádọ́rin', 80: 'lọ́gọ́rin', 90: 'láàádọ́rùn-ún', 100: 'lọ́gọ́rùn-ún'}
YO_TEEN = {11: 'mọ́kànlá', 12: 'méjìlá', 13: 'mẹ́tàlá', 14: 'mẹ́rìnlá', 15: 'mẹ́ẹ̀ẹ́dógún', 16: 'mẹ́rìndínlógún', 17: 'mẹ́tàdínlógún', 18: 'méjìdínlógún', 19: 'mọ́kàndínlógún'}
def yo_lt100(n):
    if n <= 10: return YO_UNITS[n]
    if n in YO_TEEN: return YO_TEEN[n]
    if n in YO_TENS: return YO_TENS[n]
    t = (n // 10) * 10; u = n % 10
    if u <= 4: return YO_ADD[u] + 'lé' + YO_TENS_OBJ[t]
    nxt = t + 10
    return YO_SUB[10 - u] + 'dín' + YO_TENS_OBJ[nxt]
def yo(n):
    """Large numbers are read with ẹgbẹ̀rún (thousand) and ọgọ́rùn-ún (hundred) groups, the way trainers count aloud."""
    if n == 0: return 'òdo'
    p = []
    if n >= 1000:
        k = n // 1000; p.append('ẹgbẹ̀rún' + ('' if k == 1 else ' ' + yo(k))); n %= 1000
    if n >= 100:
        h = n // 100; p.append('ọgọ́rùn-ún' + ('' if h == 1 else ' ' + YO_UNITS[h])); n %= 100
    if n: p.append(yo_lt100(n))
    return ' ó lé '.join(p) if len(p) > 1 else p[0]

POINT = {'sw': 'nukta', 'ha': 'digo', 'ig': 'ntụpọ', 'yo': 'kọ́mà', 'ar': 'فاصلة'}
TO = {'sw': 'kwa', 'ha': 'zuwa', 'ig': 'ruo', 'yo': 'sí', 'ar': 'إلى'}
FN = {'sw': sw, 'ha': ha, 'ig': ig, 'yo': yo}


def ar(n):
    try:
        from num2words import num2words
        return num2words(n, lang='ar')
    except Exception:
        return str(n)
FN['ar'] = ar


def spell(text, lang):
    f = FN[lang]
    t = re.sub(r'(\d),(\d{3})\b', r'\1\2', text); t = re.sub(r'(\d),(\d{3})\b', r'\1\2', t)
    t = re.sub(r'(\d+):(\d+)', lambda m: f(int(m.group(1))) + ' ' + TO[lang] + ' ' + f(int(m.group(2))), t)
    t = re.sub(r'(\d+)\.(\d+)', lambda m: f(int(m.group(1))) + ' ' + POINT[lang] + ' ' + ' '.join(f(int(c)) for c in m.group(2)), t)
    t = re.sub(r'\d+', lambda m: f(int(m.group(0))) if int(m.group(0)) < 1000000 else m.group(0), t)
    return t


if __name__ == '__main__':
    for L in ('sw', 'ha', 'ig', 'yo'):
        print(L, [spell(x, L) for x in ['1', '5', '15', '25', '158', '1658', '165.8', '1:19', '2500']])
