#!/usr/bin/env python3
"""detail-page.html → 플랫폼별 내보내기 (Pillow + Playwright(pip install playwright pillow; playwright install chromium) 필요. ego-browser가 있으면 그것도 쓴다).
사용: python3 export.py <detail-page.html> <출력폴더> [--platforms smartstore,coupang,gmarket,11st,html] [--max-h 1500]
출력: <출력폴더>/<플랫폼>/01.jpg 02.jpg ...  (섹션 경계에서 잘라 글자·카드가 중간에 끊기지 않게)
      <출력폴더>/html/detail-page.single.html (이미지 base64 포함 단일 파일), html/ (assets 상대경로 그대로)
HTML은 480px 기준으로 디자인되어 있고, 이미지 내보내기는 같은 화면을 목표 폭으로 확대 렌더한다 (벡터 렌더, 흐려지지 않음).
컷 위치 = .page 의 직계 자식과 그 자식의 윗선(카드·행 중간에서 끊기지 않게). 이미지에 넣지 않을 요소(하단 고정 구매 바 등)는 position:fixed 이거나 data-export="skip".
"""
import sys, os, json, base64, re, shutil, subprocess
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
WIDTH = {'smartstore': 860, 'coupang': 780, 'gmarket': 860, '11st': 860}  # 일반 권장 폭. 플랫폼 최신 가이드 확인

def render_playwright(html, W):
    from playwright.sync_api import sync_playwright
    import io
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={'width': 480, 'height': 900}, device_scale_factor=W / 480)
        pg.goto('file://' + html); pg.wait_for_timeout(1500)
        info = pg.evaluate("""()=>{
          document.querySelectorAll('[data-export="skip"]').forEach(e=>e.style.display='none');
          document.querySelectorAll('*').forEach(e=>{ if(getComputedStyle(e).position==='fixed') e.style.display='none'; });
          const p=document.querySelector('.page')||document.body; p.style.paddingBottom='0px'; document.body.style.background='#fff';
          const pr=p.getBoundingClientRect();
          const kids=[...p.children]; const all=[...kids,...kids.flatMap(k=>[...k.children])];
          const cuts=all.filter(c=>c.getBoundingClientRect().height>0).map(c=>Math.round(c.getBoundingClientRect().top+scrollY));
          return {h:Math.ceil(document.documentElement.scrollHeight), cuts, left:Math.round(pr.left)};
        }""")
        pg.wait_for_timeout(500)
        png = pg.screenshot(full_page=True, clip=None)
        br.close()
    full = Image.open(io.BytesIO(png)).convert('RGB')
    left = round(info['left'] * W / 480)
    full = full.crop((left, 0, left + W, full.height))
    return full, info

def render(html, W):
    if not shutil.which('ego-browser'):
        return render_playwright(html, W)
    tmp = os.path.join(os.path.dirname(html), '_export.json')
    js = f'''
const task = await taskSpace("detail-page export");
let page; try {{ page = task.page("p1"); }} catch(e) {{ page = await task.newPage(); }}
await page.cdp("Emulation.setDeviceMetricsOverride",{{width:480,height:900,deviceScaleFactor:1,mobile:true}});
await page.goto("file://{html}");
await new Promise(r=>setTimeout(r,2000));
const info = await page.evaluate(()=>{{
  document.querySelectorAll('[data-export="skip"]').forEach(e=>e.style.display='none');
  document.querySelectorAll('*').forEach(e=>{{ if(getComputedStyle(e).position==='fixed') e.style.display='none'; }});
  const p=document.querySelector('.page')||document.body; p.style.paddingBottom='0px'; document.body.style.background='#fff';
  const pr=p.getBoundingClientRect();
  const kids=[...p.children]; const all=[...kids,...kids.flatMap(k=>[...k.children])];
  const cuts=all.filter(c=>c.getBoundingClientRect().height>0).map(c=>Math.round(c.getBoundingClientRect().top+scrollY));
  return {{h:Math.ceil(document.documentElement.scrollHeight), cuts, left:Math.round(pr.left)}};
}});
await new Promise(r=>setTimeout(r,600));
const fs = await import("node:fs/promises");
const dir = "{os.path.dirname(html)}/_cap";
await fs.mkdir(dir,{{recursive:true}});
let i=0;
for (let y=0;y<info.h;y+=1800){{
  const r = await page.cdp("Page.captureScreenshot",{{format:"png",captureBeyondViewport:true,clip:{{x:info.left,y,width:480,height:Math.min(1800,info.h-y),scale:{W}/480}}}});
  await fs.writeFile(dir+"/c"+String(i++).padStart(3,"0")+".png", Buffer.from(r.data,"base64"));
}}
await fs.writeFile("{tmp}", JSON.stringify({{...info, n:i}}));
console.log("ok", info.h, i);
'''
    r = subprocess.run(['ego-browser', 'nodejs'], input=js, text=True, capture_output=True)
    if not os.path.exists(tmp): sys.exit('렌더 실패:\n' + r.stdout + r.stderr)
    info = json.load(open(tmp)); os.remove(tmp)
    d = os.path.join(os.path.dirname(html), '_cap')
    parts = [Image.open(f'{d}/c{k:03d}.png').convert('RGB') for k in range(info['n'])]
    full = Image.new('RGB', (parts[0].width, sum(p.height for p in parts)), 'white'); y = 0
    for p in parts: full.paste(p, (0, y)); y += p.height
    shutil.rmtree(d)
    return full, info

def slices(full, info, W, maxh):
    s = W / 480
    cuts = sorted(set(int(c * s) for c in info['cuts'] if 0 < c * s < full.height)) + [full.height]
    out, start = [], 0
    while start < full.height:
        end = max([c for c in cuts if start < c <= start + maxh], default=None)
        if end is None or full.height - start <= maxh:
            end = min(start + maxh, full.height) if full.height - start > maxh else full.height
            if end == start + maxh and full.height - start > maxh:  # 한 섹션이 maxh 보다 크면 강제 컷
                pass
        out.append((start, end)); start = end
    return out

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    html, out = os.path.abspath(a[0]), os.path.abspath(a[1])
    plats = (a[a.index('--platforms')+1] if '--platforms' in a else 'smartstore,coupang,html').split(',')
    maxh = int(a[a.index('--max-h')+1]) if '--max-h' in a else 1500
    os.makedirs(out, exist_ok=True)
    for pf in plats:
        if pf == 'html':
            d = out + '/html'; os.makedirs(d, exist_ok=True)
            src = open(html, encoding='utf-8').read(); base = os.path.dirname(html)
            def inline(m):
                p = os.path.join(base, m.group(2))
                if not os.path.exists(p): return m.group(0)
                mime = 'image/png' if p.endswith('.png') else 'image/jpeg'
                return m.group(1) + 'data:%s;base64,%s' % (mime, base64.b64encode(open(p, 'rb').read()).decode()) + m.group(3)
            open(d + '/detail-page.single.html', 'w', encoding='utf-8').write(re.sub(r'(src=")([^"]+\.(?:jpg|jpeg|png))(")', inline, src))
            shutil.copy(html, d + '/detail-page.html')
            if os.path.isdir(base + '/assets'): shutil.copytree(base + '/assets', d + '/assets', dirs_exist_ok=True)
            print('html', d); continue
        W = WIDTH.get(pf)
        if not W: print('모르는 플랫폼', pf); continue
        full, info = render(html, W)
        d = f'{out}/{pf}'; shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
        sl = slices(full, info, W, int(maxh * W / 860))
        for k, (s, e) in enumerate(sl, 1):
            full.crop((0, s, W, e)).save(f'{d}/{k:02d}.jpg', quality=88, optimize=True)
        tot = sum(os.path.getsize(f'{d}/{f}') for f in os.listdir(d)) / 1e6
        print(f'{pf}: 폭 {W}px, {len(sl)}장, 전체높이 {full.height}px, {tot:.1f}MB -> {d}')
main()
