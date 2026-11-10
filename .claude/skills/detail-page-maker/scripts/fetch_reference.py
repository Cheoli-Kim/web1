#!/usr/bin/env python3
"""참고 상세페이지 URL → 이미지·본문 텍스트 수집 (ego-browser 필요. 없으면 클로드의 웹 검색·페이지 읽기로 참고 구조를 직접 뜯는다).
사용: python3 fetch_reference.py <url> <출력폴더> [--min-width 300]
결과: <출력폴더>/images/NN.ext, slices/NN.jpg(긴 이미지를 2000px씩), page.txt, manifest.json
"""
import sys, os, json, subprocess, tempfile, urllib.request, urllib.parse
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    url, out = a[0], os.path.abspath(a[1])
    minw = int(a[a.index('--min-width')+1]) if '--min-width' in a else 300
    os.makedirs(out + '/images', exist_ok=True); os.makedirs(out + '/slices', exist_ok=True)
    js = f'''
const task = await taskSpace("detail-page reference");
let page; try {{ page = task.page("p1"); }} catch(e) {{ page = await task.newPage(); }}
await page.goto({json.dumps(url)});
await new Promise(r=>setTimeout(r,2500));
const H = await page.evaluate(()=>document.documentElement.scrollHeight);
for (let y=0;y<Math.min(H,60000);y+=900){{ await page.evaluate((y)=>window.scrollTo(0,y), y); await new Promise(r=>setTimeout(r,250)); }}
await new Promise(r=>setTimeout(r,1200));
const data = await page.evaluate(()=>{{
  const imgs=[...document.images].map(i=>({{src:i.currentSrc||i.src,w:i.naturalWidth,h:i.naturalHeight}})).filter(i=>i.src&&i.w>0);
  return {{title:document.title, imgs, text:document.body.innerText.slice(0,30000)}};
}});
const fs = await import("node:fs/promises");
await fs.writeFile({json.dumps(out + '/_raw.json')}, JSON.stringify(data));
console.log("ok", data.imgs.length);
'''
    r = subprocess.run(['ego-browser', 'nodejs'], input=js, text=True, capture_output=True)
    if not os.path.exists(out + '/_raw.json'):
        sys.exit('수집 실패(로그인/봇 차단 가능):\n' + r.stdout + r.stderr)
    d = json.load(open(out + '/_raw.json'))
    open(out + '/page.txt', 'w').write(d['text'])
    seen, man, n = set(), [], 0
    for i in d['imgs']:
        s = i['src']
        if s in seen or s.startswith('data:') or i['w'] < minw: continue
        seen.add(s); n += 1
        ext = os.path.splitext(urllib.parse.urlparse(s).path)[1].lower()
        if ext not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'): ext = '.img'
        fp = f'{out}/images/{n:02d}{ext}'
        try:
            req = urllib.request.Request(s, headers={'User-Agent': 'Mozilla/5.0', 'Referer': url})
            open(fp, 'wb').write(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            man.append({'n': n, 'src': s, 'error': str(e)}); continue
        row = {'n': n, 'src': s, 'file': fp, 'w': i['w'], 'h': i['h']}
        try:
            im = Image.open(fp).convert('RGB')
            if im.height >= 1800:  # 긴 상세 이미지 → 2000px 조각 (눈으로 읽기용, y오프셋 = 조각번호*2000)
                for k, y in enumerate(range(0, im.height, 2000)):
                    im.crop((0, y, im.width, min(y + 2000, im.height))).save(f'{out}/slices/{n:02d}-{k:02d}.jpg', quality=82)
                row['slices'] = (im.height + 1999) // 2000
        except Exception: pass
        man.append(row)
    json.dump({'url': url, 'title': d['title'], 'images': man}, open(out + '/manifest.json', 'w'), ensure_ascii=False, indent=1)
    os.remove(out + '/_raw.json')
    print(f"{d['title']}\n이미지 {len(man)}개, 긴 이미지 조각은 slices/ 에서 확인")
    for m in man: print(m.get('n'), m.get('w'), m.get('h'), m.get('slices', ''), m.get('error', ''))
main()
