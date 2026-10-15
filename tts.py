import asyncio, json, os, sys, edge_tts
L = json.load(open('lines.json'))['lines']
os.makedirs('out', exist_ok=True)
log = []
async def one(l):
    for k in range(4):
        try:
            c = edge_tts.Communicate(l['voice'], 'en-NG-EzinneNeural', rate='-6%')
            await c.save(f"out/{l['id']}.mp3")
            if os.path.getsize(f"out/{l['id']}.mp3") > 2000: return 'ok'
        except Exception as e:
            err = str(e)[:150]; await asyncio.sleep(2)
    return 'fail ' + err
async def main():
    for l in L:
        r = await one(l); log.append(f"{l['id']} {r}"); print(log[-1], flush=True)
    open('out/log.txt', 'w').write('\n'.join(log))
asyncio.run(main())
