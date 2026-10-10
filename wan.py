import sys, time, os, torch
from diffusers import AutoencoderKLWan, WanPipeline
from diffusers.utils import export_to_video
torch.set_num_threads(os.cpu_count())
P = {
 'nitrosol': 'Close-up handheld phone video in a clean bright small workshop. An African woman wearing clear safety goggles, blue nitrile gloves and a white apron slowly sprinkles white powder from a small bowl into a white plastic bucket of water while stirring with a long wooden stick. White tiled table, daylight, realistic.',
 'ph': 'Macro close-up phone video. A hand in a blue nitrile glove dips a paper pH test strip into a small cup of green liquid soap, lifts it and holds it beside a colour chart. Clean white table, daylight, realistic.',
}
NEG = 'cartoon, 3d render, blurry, distorted hands, extra fingers, text, watermark, low quality'
shot = sys.argv[1]; os.makedirs('out', exist_ok=True)
mid = 'Wan-AI/Wan2.1-T2V-1.3B-Diffusers'
t = time.time()
vae = AutoencoderKLWan.from_pretrained(mid, subfolder='vae', torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(mid, vae=vae, torch_dtype=torch.bfloat16)
print('loaded', round(time.time() - t)); t = time.time()
with torch.no_grad():
    pe, ne = pipe.encode_prompt(prompt=P[shot], negative_prompt=NEG, do_classifier_free_guidance=True, device='cpu')
pipe.text_encoder = None; import gc; gc.collect()
print('encoded', round(time.time() - t)); t = time.time()
frames = pipe(prompt_embeds=pe, negative_prompt_embeds=ne, height=320, width=576, num_frames=33, num_inference_steps=20, guidance_scale=5.0,
              generator=torch.Generator().manual_seed(7), callback_on_step_end=lambda p, i, ts, kw: (print('step', i, round(time.time() - t), flush=True), kw)[1]).frames[0]
export_to_video(frames, 'out/wan_%s.mp4' % shot, fps=16)
print('done', round(time.time() - t))
