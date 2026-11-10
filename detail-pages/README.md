# 상세페이지 만들기 (detail-page-maker 스킬)

출처: [오완 · 상세페이지 만드는 클로드·코덱스 스킬](https://oaiwan.kr/g/detail-page-skill) 의 `detail-page-maker.zip`
스킬 파일은 이 저장소의 `.claude/skills/detail-page-maker/` 에 들어 있어서, 이 저장소에서 Claude Code를 열면 바로 쓸 수 있습니다.

## 이 스킬이 하는 일
- 잘 팔리는 상세페이지의 섹션 순서·제목 모양을 따라 상품 정보로 채움
- 480px 모바일 상세페이지(HTML)를 한 번에 생성 (풀블리드 사진·큰 글자·하단 고정 구매 바)
- 스마트스토어(860px)·쿠팡(780px)·G마켓·11번가 폭에 맞춰 섹션 경계에서 잘린 JPG로 내보내기
- 말 한마디로 해당 섹션만 수정 (이전 버전은 그대로 두고 v02, v03… 으로 새로 생성)

## 처음 한 번만: 준비
```bash
pip install playwright pillow
playwright install chromium
```
Claude Code에서 `/skills` 를 입력해 `detail-page-maker` 가 보이면 준비 끝.
(다른 프로젝트에서도 쓰려면 `.claude/skills/detail-page-maker` 폴더를 `~/.claude/skills/` 로 복사하세요.)

## 사용법
1. 템플릿 복사
   ```bash
   cp -r detail-pages/_template detail-pages/my-product
   ```
2. `detail-pages/my-product/product-info.md` 채우기 (모르는 칸은 비워 두기)
3. 상품 사진을 `detail-pages/my-product/assets/` 에 넣기
4. Claude Code에 아래 요청문 붙여 넣기
   ```
   detail-page-maker 스킬로 detail-pages/my-product 폴더의 상품 상세페이지를 만들어 줘.
   상품 설명은 product-info.md, 사진은 assets 폴더에 있어.
   스마트스토어와 쿠팡용 이미지까지 내보내 줘.
   ```
   - 참고하고 싶은 잘 팔리는 페이지가 있으면 한 줄 추가: `참고 페이지: https://...`
   - 없으면 같은 카테고리 상위 판매 페이지를 알아서 찾아 구조를 참고합니다.

## 결과물
```
detail-pages/my-product/out/v01/
  detail-page.html        원본 상세페이지 (브라우저로 열어 확인)
  structure.md            섹션 구조표 · 카피 근거
  open-items.md           가격·후기 등 받지 못해 뺀 정보 (채우면 좋아지는 것)
  export/smartstore/      01.jpg, 02.jpg …  (860px)
  export/coupang/         01.jpg, 02.jpg …  (780px)
  export/html/            단일 파일 HTML (자사몰·카페24용)
```

## 수정하기
말로 시키면 해당 섹션만 고쳐서 `out/v02/` 로 새로 만듭니다.
```
첫 화면 제목을 '당김은 빼고 촉촉함만'으로 바꾸고 색은 피치로 바꿔 줘.
```
```
가격이 29,900원으로 정해졌어. 가격 섹션 추가해 줘.
```

## 알아 둘 것
- 가격·후기·수치처럼 주지 않은 정보는 지어내지 않고 `open-items.md` 에 빈칸 목록으로 남깁니다.
- 860px/780px 은 일반 권장값입니다. 올리기 전에 판매자센터의 현재 이미지 규격을 확인하세요.
- 참고 페이지의 로고·상표·원본 이미지·문장은 쓰지 마세요. 내 상품 이름과 내 사진으로 바꿔 써야 합니다.
- 화장품·건강식품은 "최고·1위·유일·완치" 같은 단정·과장 표현을 쓰지 않습니다.
- 사진 없는 연출컷은 이미지 생성 도구(ChatGPT·Codex)가 있을 때만 만들고, 없으면 표·칩·큰 숫자 같은 그래픽으로 채웁니다.
- `scripts/fetch_reference.py` (참고 페이지 자동 수집)는 `ego-browser` 가 있어야 동작합니다. 없으면 Claude가 웹 검색·페이지 읽기로 대신합니다.
