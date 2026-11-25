# 변환 도구

한글 97(HWP 3.0) 원고를 웹 교재로 바꾸는 도구입니다.

| 파일 | 역할 |
|---|---|
| `hwp3.py` | HWP 3.0 파서: 문단·표·그림·각주를 구조로 읽음 (조합형 한글, 한자, 특수기호 대응) |
| `symmap.json` | 한글 97 특수기호 코드 → 유니코드 대응표 (`mkmap.py`로 생성) |
| `extract_blocks.py` | 문서 끝 추가 정보 블록에서 내장 그림·OLE 개체 추출 |
| `assets.py` | WMF·OLE 그림 → PNG/JPG 변환(LibreOffice, pdftoppm). 큰 회로도는 600dpi |
| `drawsvg.py` | 한글 그리기 개체(선·사각형·타원·곡선·글상자) → SVG |
| `build_site.py` | 장 구성에 따라 HTML 생성 (rule_md 교육용 표준 디자인) |
| `zoom.js` | 그림 확대 보기(휠·버튼·키보드·두 손가락 확대, 끌어서 이동) |

```bash
# 작업 폴더 구성: raw/(원고), emb/(추출 그림), scripts/(이 도구), yuul-jung/rule_md(표준 저장소)
python3 scripts/extract_blocks.py raw emb   # 내장 그림 추출
python3 scripts/build_site.py               # site/ 에 HTML 생성
```

필요 도구: Python 3, Pillow, olefile, LibreOffice, poppler-utils(pdftoppm)
