# 플랫폼별 내보내기 (scripts/export.py)

| 플랫폼 | 값 | 폭 | 형식 |
|---|---|---|---|
| 스마트스토어 | `smartstore` | 860px | 섹션 경계에서 자른 JPG 여러 장 (장당 높이 ≤1500) |
| 쿠팡 | `coupang` | 780px | 같음 |
| G마켓·옥션 | `gmarket` | 860px | 같음 |
| 11번가 | `11st` | 860px | 같음 |
| 자사몰·카페24·웹 | `html` | 가변(최대 480px 중앙) | 단일 파일 HTML(이미지 base64 포함) + assets 폴더판 |

- 위 폭은 일반적으로 알려진 권장값이다. 올리기 전에 해당 판매자센터의 현재 이미지 규격(폭·장당 용량·장수)을 확인한다. 확인하지 못한 값은 최종 보고에 '미확인'으로 쓴다.
- 이미지로 내보내면 글꼴·간격이 그림에 고정되고 플랫폼이 스타일을 지워도 안 깨진다. 단점: 글자 검색·복사 불가, 이미지 안 글자는 수정하려면 HTML에서 다시 내보내야 한다. 그래서 원본은 항상 HTML.
- 하단 고정 구매 바(`position:fixed`)와 `data-export="skip"` 요소는 이미지에서 자동으로 뺀다. 판매처 안에서는 판매처 구매 버튼이 있으므로 필요 없다.
- 조각은 `.page` 직계 섹션과 그 자식 윗선에서 자른다. 섹션 구조(`.page > section`)를 유지해야 깔끔하게 잘린다.
- 명령: `python3 scripts/export.py <out/vNN/detail-page.html> <out/vNN/export> --platforms smartstore,coupang,html [--max-h 1500]`
