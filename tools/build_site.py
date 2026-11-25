#!/usr/bin/env python3
"""Build the micro-robot project guide site (rule_md education-html standard)."""
import os, re, json, html, base64, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hwp3
from assets import Assets

ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw')
SITE = os.path.join(ROOT, 'site')
RULE = os.path.join(ROOT, 'yuul-jung/rule_md/web/education-html')
IMGDIR = os.path.join(SITE, 'assets', 'img')

COURSE = {
    'site_title': '라인 마이크로 로봇 제작하기',
    'course_code': 'MICRO ROBOT PROJECT',
    'version': 'v01',
    'site_description': 'Z80 원보드 컴퓨터, DC 모터 제어회로, 센서 신호 검출회로, 프레임 제작과 제어 프로그램을 차례로 완성해 라인 트레이싱 마이크로 로봇을 만드는 프로젝트 지도서입니다.',
}

# (id, number, title, nav subtitle, slug, tags, [(doc, mode, section title)])
CHAPTERS = [
    ('ch01', 1, '프로젝트 개요', '조립도 → 과제 계획 → 지도 절차 → 기능 설명 → 작업 분담', 'ch01_project_overview',
     ['조립도', '과제계획', '재료'],
     [('과제조립도면', 'whole', '로봇 조립도'), ('과제계획서', 'whole', '과제계획서'),
      ('훈련-지도방법적절차계획', 'whole', '훈련·지도 방법적 절차계획'),
      ('과제기능(동작)설명서', 'whole', '과제 기능(동작) 설명서'), ('작업분담표', 'whole', '작업분담표'),
      ('재료 목록', 'whole', '재료 목록')]),
    ('ch02', 2, 'Z80 원보드 컴퓨터', '디지털 시스템 → Z80 CPU → 주변소자 IC', 'ch02_z80_one_board_computer',
     ['Z80', '8255', '8253', '8251'],
     [('관련이론(원보드컴퓨터)', 'split', None)]),
    ('ch03', 3, '8251 시리얼 통신', '핀 배치 → 모드 설정 → 커맨드 → 프로그램 흐름', 'ch03_8251_serial',
     ['8251', 'USART', 'RS-232'],
     [('관련이론(시리얼통신)', 'whole', '8251의 구조와 기능')]),
    ('ch04', 4, 'DC 모터 제어', '개념 → 토크 → On/Off → 가변속(PWM) → PID', 'ch04_dc_motor_control',
     ['DC 모터', 'H 브리지', 'PWM', 'PID'],
     [('이론(모터)', 'split', None)]),
    ('ch05', 5, '센서와 신호 검출', '센서 정의 → 신호 검출 → 센서별 원리 → 릴레이', 'ch05_sensors',
     ['센서', '광전센서', '근접센서', '릴레이'],
     [('이론(센서1)', 'split', None), ('관련이론(센서제어)', 'split_num', '센서와 자동화 시스템')]),
    ('ch06', 6, '프레임과 바퀴 제작', '프레임 도면 → 바퀴·축 가공 → 조립', 'ch06_frame_and_wheels',
     ['기구 제작', '도면'],
     [('프레임 및 바퀴제작', 'whole', '프레임 및 바퀴 제작 도면')]),
    ('ch07', 7, '운용 프로그램 제작', 'Z80 어셈블리 개론 → 명령어', 'ch07_z80_assembly',
     ['Z80 어셈블리', '명령어'],
     [('관련이론(운용프로그램)', 'split', None)]),
    ('ch08', 8, '학습활동 안내', '안내 질문 → 기술·기능 학습활동 → 새로운 관련지식', 'ch08_learning_activities',
     ['학습활동', '안내질문'],
     [('학습활동을위한안내질문', 'whole', '학습활동을 위한 안내 질문'),
      ('기술기능학습활동', 'whole', '기술·기능 학습활동 안내 질문·지시문'),
      ('새로운관련지식', 'whole', '새로운 관련지식')]),
    ('ch09', 9, '계획·보고·평가', '작업계획서 → 실습결과보고서 → 평가표 → 작업분석표 → 연습과제', 'ch09_plan_report_evaluation',
     ['작업계획', '보고서', '평가'],
     [('작업계획서', 'whole', '작업계획서'), ('보고서', 'whole', '실습결과보고서'), ('평   가   표', 'whole', '평가표'),
      ('작업분석표', 'whole', '작업분석표'), ('연습과제', 'whole', '연습과제')]),
]

SENSOR_HEADS = {'센서의 개요': '센서의 개요와 정의', '센서의 종류': '센서의 종류', '센서 재료': '센서 재료와 신호',
                '유도형 센서(Inductive Sensor)': '유도형 센서', '용량형 센서': '용량형 센서와 광전센서',
                '리드 스위치': '리드 스위치', '자기센서': '자기센서', '초음파센서': '초음파센서', '릴레이(Relay)': '릴레이의 기초'}

EQUATIONS = {
    'DELTAh_1overDELTAT_1=DELTAh_2overDELTAT_2': '<span class="frac"><span>Δh<sub>1</sub></span><span>ΔT<sub>1</sub></span></span> = <span class="frac"><span>Δh<sub>2</sub></span><span>ΔT<sub>2</sub></span></span>',
    'C=epsilonSoverd': 'C = <span class="frac"><span>εS</span><span>d</span></span>',
    'epsilon': 'ε', 'rho': 'ρ', 'OMEGA': 'Ω', 'lambda': 'λ',
    'epsilon_0·epsilon_s': 'ε<sub>0</sub>·ε<sub>s</sub>',
    'Vout=R_2over{R_1+R_2}Vin': 'V<sub>out</sub> = <span class="frac"><span>R<sub>2</sub></span><span>R<sub>1</sub> + R<sub>2</sub></span></span> V<sub>in</sub>',
    '{D}_{7}': 'D<sub>7</sub>', '{D}_{0}': 'D<sub>0</sub>', '{A}_{1}': 'A<sub>1</sub>', '{A}_{0}': 'A<sub>0</sub>',
}

esc = lambda s: html.escape(s, quote=True)


def para_text(p):
    return ''.join(x for x in p['items'] if isinstance(x, str))


def fmt_text(s):
    s = s.replace('\t', '   ')
    s = esc(s)
    s = re.sub(r' {3,}', '<span class="gap"></span>', s)
    return s


class Renderer:
    def __init__(self, stem, doc, assets):
        self.stem, self.doc, self.assets = stem, doc, assets
        self.styles = doc['styles']
        self.mode = ''

    def style_name(self, p):
        return self.styles[p['style']] if p['style'] < len(self.styles) else ''

    # ---- inline/blocks --------------------------------------------------
    def items_html(self, p, in_cell=False):
        """Return list of html chunks: ('inline', s) or ('block', s)."""
        out = []
        for it in p['items']:
            if isinstance(it, str):
                out.append(('inline', fmt_text(it) if it.strip() else (' ' if it else '')))
            elif it['type'] == 'box':
                out.append(('block', self.box(it)))
            elif it['type'] == 'picture':
                out.append(('block', self.picture(it)))
            elif it['type'] == 'footnote':
                t = ' '.join(para_text(q).strip() for q in it['paras'])
                if t.strip():
                    out.append(('inline', '<span class="fn">(주: %s)</span>' % fmt_text(t)))
        return out

    def paras_html(self, paras, in_cell=False):
        """One <p> per paragraph; objects anchored before the text go first,
        objects anchored mid-sentence go right after the paragraph so sentences stay whole."""
        h = []
        for p in paras:
            chunks = self.items_html(p, in_cell)
            before, line, after = [], [], []
            for kind, s in chunks:
                if kind == 'inline':
                    line.append(s)
                elif ''.join(line).strip():
                    after.append(s)
                else:
                    before.append(s)
            h.extend(before)
            txt = re.sub(r'^(?:\s|<span class="gap"></span>)+|(?:\s|<span class="gap"></span>)+$', '', ''.join(line))
            if txt:
                bold = p['bold'] and len(txt) < 140 and not in_cell
                h.append('<p>%s</p>' % ('<strong>%s</strong>' % txt if bold else txt))
            h.extend(after)
        return '\n'.join(x for x in h if x)

    def picture(self, pic):
        cap = self.paras_html(pic['caption'], True)
        name, dtext = self.assets.picture(self.stem, pic)
        if name is None:
            if dtext:
                return '<p%s>%s</p>' % ('' if len(dtext) > 80 else ' class="figcap"', esc(dtext))
            return ''
        wpx = max(60, min(int(pic['w'] / 18.75), 860))
        cap_html = '<figcaption>%s</figcaption>' % re.sub(r'</?p>', ' ', cap) if cap.strip() else ''
        return ('<figure class="fig"><img src="assets/img/@@IMG:%s@@" alt="%s" loading="lazy" decoding="async" style="width:%dpx">%s</figure>'
                % (name, esc(re.sub('<[^>]+>', '', cap).strip() or '본문 그림'), wpx, cap_html))

    def box(self, b):
        if b['kind'] == 2:
            src = ''.join(para_text(p) for c in b['cells'] for p in c['paras'])
            key = re.sub(r'\s+', '', src)
            key = re.sub(r'\{BJb\}$', '', key)
            if key.startswith('1over{ne}'):
                return '<span class="eq"><span class="frac"><span>1</span><span>ne</span></span></span>'
            return '<span class="eq">%s</span>' % EQUATIONS.get(key, esc(src.strip()))
        cells = b['cells']
        cap = self.paras_html(b['caption'], True)
        if len(cells) == 1:
            inner = self.paras_html(cells[0]['paras'], True)
            if not re.sub('<[^>]+>', '', inner).strip() and '<img' not in inner:
                return ''
            return '<div class="frame">%s</div>' % inner
        return self.table(cells, cap)

    def table(self, cells, cap):
        def bounds(vals):
            vals = sorted(set(vals)); out = []
            for v in vals:
                if not out or v - out[-1] > 40:
                    out.append(v)
            return out
        xs = bounds([c['x'] for c in cells] + [c['x'] + c['w'] for c in cells])
        ys = bounds([c['y'] for c in cells] + [c['y'] + c['h'] for c in cells])
        def idx(arr, v):
            return min(range(len(arr)), key=lambda i: abs(arr[i] - v))
        grid = {}
        for c in cells:
            r0, r1 = idx(ys, c['y']), idx(ys, c['y'] + c['h'])
            c0, c1 = idx(xs, c['x']), idx(xs, c['x'] + c['w'])
            grid.setdefault(r0, []).append((c0, max(1, r1 - r0), max(1, c1 - c0), c))
        rows = []
        for r in range(len(ys) - 1):
            tds = []
            for c0, rs, cs, c in sorted(grid.get(r, []), key=lambda t: t[0]):
                inner = self.paras_html(c['paras'], True)
                attrs = (' rowspan="%d"' % rs if rs > 1 else '') + (' colspan="%d"' % cs if cs > 1 else '')
                tds.append('<td%s>%s</td>' % (attrs, inner))
            rows.append('<tr>%s</tr>' % ''.join(tds))
        caption = '<caption>%s</caption>' % re.sub(r'</?p>', ' ', cap) if cap.strip() else ''
        return '<div class="table-wrap" tabindex="0"><table class="hwp">%s%s</table></div>' % (caption, ''.join(rows))

    # ---- sectioning -----------------------------------------------------
    def heading_level(self, p):
        name = self.style_name(p)
        t = para_text(p).strip()
        if not t:
            return 0
        if '대단원' in name:
            return 1
        if re.match(r'^제\s*\d+\s*절', t) or ('중단원' in name and not re.match(r'^\d', t)):
            return 2
        if '중단원' in name and re.match(r'^\d+\s*\.', t) and len(t) < 60:
            return 3
        if name.startswith('세단원( 1.') and re.match(r'^\d+\s*\.', t) and len(t) < 60:
            return 3
        return 0

    def sections(self, mode, title):
        self.mode = mode
        paras = self.doc['paras']
        if mode == 'whole':
            body = self.render_flat(paras)
            return [(title, body)]
        secs = []
        cur_t, cur = None, []
        for p in paras:
            t = para_text(p).strip()
            lvl = self.heading_level(p)
            if mode == 'split_num':
                key = re.sub(r'^[\dIV]+\s*\.\s*', '', t)
                if key in SENSOR_HEADS:
                    lvl = 2
                    t = SENSOR_HEADS[key]
                elif re.match(r'^\d+(\s*-\s*\d+)?\s*\.\s*\S', t) and len(t) < 45 and '[V]' not in t:
                    lvl = 3
                elif re.match(r'^I+\s*\.', t):
                    lvl = 1
                else:
                    lvl = 0
            if lvl == 1:
                continue
            if lvl == 2:
                if cur_t is not None or any(para_text(q).strip() for q in cur):
                    secs.append((cur_t, cur))
                cur_t, cur = re.sub(r'^제\s*\d+\s*절\s*', '', t).strip(), []
                continue
            cur.append(p)
        secs.append((cur_t, cur))
        out = []
        for t, ps in secs:
            body = self.render_flat(ps)
            if not re.sub('<[^>]+>', '', body).strip() and '<img' not in body:
                continue
            if t is None:
                plain = re.sub('<[^>]+>', '', body).strip()
                if len(plain) < 40 and '<img' not in body and '<table' not in body:
                    continue
                t = title or '도입'
            out.append((t, body))
        return out

    def render_flat(self, paras):
        h = []
        for p in paras:
            lvl = self.heading_level(p)
            t = para_text(p).strip()
            if self.mode == 'split_num' and re.match(r'^\d+(\s*-\s*\d+)?\s*\.\s*\S', t) and len(t) < 45 and '[V]' not in t:
                lvl = 3
            if lvl == 3 and not any(isinstance(x, dict) for x in p['items']):
                h.append('<h3>%s</h3>' % fmt_text(t))
            elif (t in ('관련이론 학습활동 안내질문 및 지시문',)):
                continue
            else:
                h.append(self.paras_html([p]))
        return '\n'.join(x for x in h if x)


EXTRA_CSS = '''
/* ===== HWP 원고 변환 보조 스타일 ===== */
/* 그림 확대 보기 */
figure.zoomable{position:relative}
figure.zoomable img{cursor:zoom-in}
figure.zoomable img:focus-visible{outline:3px solid #4635B1;outline-offset:3px}
.fig.zoomable::before{content:"🔍 확대";position:absolute;right:6px;top:6px;z-index:1;font-size:.72rem;padding:2px 7px;border-radius:10px;background:rgba(21,23,28,.72);color:#fff;pointer-events:none}
.zv{position:fixed;inset:0;z-index:2147483000;background:rgba(14,15,19,.94);display:flex;flex-direction:column}
.zv[hidden]{display:none}
.zv-bar{display:flex;align-items:center;gap:6px;padding:8px 12px;background:#15171C;color:#fff;flex-wrap:wrap}
.zv-title{flex:1 1 200px;font-size:.9rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.zv-bar button,.zv-orig{background:#2A2D36;color:#fff;border:1px solid #444;border-radius:6px;padding:5px 11px;font:inherit;font-size:.88rem;cursor:pointer;text-decoration:none}
.zv-bar button:hover,.zv-orig:hover{background:#4635B1}
.zv-bar button:focus-visible,.zv-orig:focus-visible{outline:3px solid #FFD24A;outline-offset:2px}
.zv-pct{min-width:3.4em;text-align:center;font-family:"IBM Plex Mono",monospace;font-size:.85rem}
.zv-stage{flex:1;position:relative;overflow:hidden;touch-action:none;cursor:grab;background:#fff}
.zv-stage:active{cursor:grabbing}
.zv-stage img{position:absolute;left:0;top:0;transform-origin:0 0;max-width:none;user-select:none;-webkit-user-drag:none}
.zv-help{margin:0;padding:6px 12px;color:#C9CBC4;font-size:.8rem;background:#15171C}
html.zv-lock,html.zv-lock body{overflow:hidden}
@media print{.zv,.fig.zoomable::before{display:none}}
.content{min-width:0}
@media screen{.table-wrap{overflow-x:auto;max-width:100%;-webkit-overflow-scrolling:touch}}
@media (max-width:860px){table.hwp{font-size:.82rem}table.hwp td{padding:.3em .4em}}
.section p{margin:.45em 0;line-height:1.8}
.section h3{margin:1.6em 0 .6em;font-size:1.05rem;color:#4635B1}
.gap{display:inline-block;width:2.2em}
.fig{margin:1.2em auto;text-align:center}
.fig img{max-width:100%;height:auto;border:1px solid #E3E4DE;border-radius:6px;background:#fff}
.fig figcaption,.figcap{font-size:.88rem;color:#5B5F69;text-align:center;margin:.4em 0 1em}
.frame{border:1px solid #D9DAD4;border-radius:8px;padding:.8em 1.1em;margin:1em 0;background:#FBFBF9}
table.hwp{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6em 0}
table.hwp td{border:1px solid #C9CBC4;padding:.4em .55em;vertical-align:middle}
table.hwp td p{margin:.15em 0;line-height:1.55}
table.hwp caption{caption-side:bottom;font-size:.88rem;color:#5B5F69;padding:.4em}
table.hwp .fig{margin:.4em auto}
.eq{font-family:"Times New Roman",serif;font-style:italic;white-space:nowrap;padding:0 .15em}
.frac{display:inline-flex;flex-direction:column;vertical-align:middle;text-align:center;margin:0 .15em}
.frac>span:first-child{border-bottom:1px solid currentColor;padding:0 .2em}
.fn{font-size:.85rem;color:#5B5F69}
.dl-list{list-style:none;padding:0}.dl-list li{margin:.3em 0}
.slide-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}
.slide-grid figure{margin:0}
.slide-grid img{width:100%;height:auto;border:1px solid #E3E4DE;border-radius:6px}
'''


def page(title, kicker, desc, chips, body, chapter_id, css, script, chapters):
    manifest = {'title': COURSE['site_title'], 'short_title': COURSE['course_code'], 'home_label': '전체 학습 안내서',
                'chapters': [{'id': c['id'], 'number': c['number'], 'title': c['title'], 'file': c['file']} for c in chapters]}
    chips_html = ''.join('<span class="chip">%s</span>' % esc(c) for c in chips)
    data = json.dumps(manifest, ensure_ascii=False).replace('<', '\\u003c')
    return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="{esc(desc)}"><title>{esc(title)} · {esc(COURSE['site_title'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%234635B1'/%3E%3Ctext x='16' y='22' font-size='14' text-anchor='middle' fill='%23FFD24A' font-family='monospace'%3EZ80%3C/text%3E%3C/svg%3E"><link rel="stylesheet" href="assets/site.css"></head><body data-chapter="{esc(chapter_id)}">
<button type="button" class="mobile-menu" id="mobile-menu" aria-controls="course-nav" aria-expanded="false">☰ 장·목차</button><div class="shade" id="shade"></div>
<header class="hero"><div class="hero-inner"><p class="kicker">{esc(kicker)}</p><h1>{esc(title)}</h1><p>{esc(desc)}</p><div class="chips">{chips_html}</div></div></header>
<div class="wrap"><nav class="toc" id="course-nav" aria-label="장과 절 탐색"></nav><main class="content" id="main-content">{body}<div class="chapter-links" id="chapter-links"></div></main></div>
<footer class="footer">{esc(COURSE['site_title'])} · {esc(COURSE['version'])} · 프로젝트지도서 99-36 (대한상공회의소 직업교육훈련사업단) 웹 변환본</footer>
<script>window.COURSE={data};</script><script src="assets/site.js"></script><script src="assets/zoom.js"></script></body></html>'''


def section_html(n, title, body):
    return f'<section class="section" id="s{n:02d}"><h2><span class="num">{n:02d}</span>{esc(title)}</h2>{body}</section>'


SLIDE_SETS = [('Z80하드웨어.ppt', 'Z80 하드웨어 발표 자료', 'z80hw'), ('시스템구성도.ppt', '시스템 구성도', 'system')]
EXTRA_FIGS = [('8253.gif', '8253 카운터/타이머 핀 배치'), ('8253ord.gif', '8253 컨트롤 워드 구성'), ('rs232rcv.gif', 'RS-232 수신 회로')]
DOWNLOADS = [
    ('한글 원고 (HWP 3.0)', [f for f in sorted(os.listdir(RAW)) if f.endswith('.hwp')]),
    ('회로도 (OrCAD Capture)', ['8051COMPUTER.DSN', 'Z80하드웨어.DSN', 'Z80하드웨어.opj', 'Z80하드웨어 회로도 진짜.DSN', 'Z80하드웨어 회로도 진짜.opj', 'STEPMOT.DSN', 'STEPMOT.opj']),
    ('발표 자료 (PowerPoint)', ['Z80하드웨어.ppt', '시스템구성도.ppt']),
]


def resources_chapter():
    import subprocess, shutil, glob
    from urllib.parse import quote
    from PIL import Image
    secs = []
    sdir = os.path.join(SITE, 'assets', 'slides'); os.makedirs(sdir, exist_ok=True)
    tmp = os.path.join(ROOT, 'work_img', 'ppt'); os.makedirs(tmp, exist_ok=True)
    for src, title, key in SLIDE_SETS:
        shutil.copy(os.path.join(RAW, src), os.path.join(tmp, key + '.ppt'))
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', tmp, os.path.join(tmp, key + '.ppt')],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
        subprocess.run(['pdftoppm', '-r', '200', '-png', os.path.join(tmp, key + '.pdf'), os.path.join(tmp, key)], check=True)
        figs = []
        for i, f in enumerate(sorted(glob.glob(os.path.join(tmp, key + '-*.png'))), 1):
            im = Image.open(f).convert('RGB')
            im.thumbnail((2200, 1650))
            name = '%s_%02d.jpg' % (key, i)
            im.save(os.path.join(sdir, name), quality=85)
            figs.append('<figure class="fig"><a href="assets/slides/%s"><img src="assets/slides/%s" alt="%s %d쪽"></a><figcaption>%d쪽</figcaption></figure>' % (name, name, esc(title), i, i))
        secs.append((title, '<p>원본 PowerPoint 슬라이드를 그림으로 옮겼습니다. 그림을 누르면 크게 볼 수 있습니다.</p><div class="slide-grid">%s</div>' % ''.join(figs)))
    figs = []
    for f, cap in EXTRA_FIGS:
        shutil.copy(os.path.join(RAW, f), os.path.join(IMGDIR, 'extra_' + f))
        figs.append('<figure class="fig"><img src="assets/img/extra_%s" alt="%s"><figcaption>%s</figcaption></figure>' % (f, esc(cap), esc(cap)))
    secs.append(('보충 그림', '<p>원고 폴더에 함께 들어 있던 그림입니다. 8253과 RS-232 수신 회로는 제02장·제03장과 함께 보면 좋습니다.</p>' + ''.join(figs)))
    ddir = os.path.join(SITE, 'source'); os.makedirs(ddir, exist_ok=True)
    blocks = []
    for title, files in DOWNLOADS:
        items = []
        for f in files:
            shutil.copy(os.path.join(RAW, f), os.path.join(ddir, f))
            size = os.path.getsize(os.path.join(RAW, f))
            items.append('<li><a href="source/%s" download>%s</a> <span class="fn">(%s KB)</span></li>' % (quote(f), esc(f.replace('         ', ' ').replace('   ', ' ')), format(round(size / 1024), ',')))
        blocks.append('<h3>%s</h3><ul class="dl-list">%s</ul>' % (esc(title), ''.join(items)))
    note = ('<p>원고는 한글 97(HWP 3.0) 형식이라 최신 한글에서 열 수 있습니다. 회로도는 OrCAD Capture 설계 파일(.DSN)이며 '
            '「관련이론(모터제어회로).hwp」는 제04장 원고의 초안입니다.</p>')
    secs.append(('원본 파일 내려받기', note + ''.join(blocks)))
    return {'id': 'ch10', 'number': 10, 'title': '회로도·발표 자료', 'subtitle': 'Z80 하드웨어 슬라이드 → 시스템 구성도 → 원본 파일',
            'tags': ['슬라이드', 'OrCAD', '원본'], 'file': 'ch10_resources_%s.html' % COURSE['version'], 'secs': secs}


def build():
    os.makedirs(IMGDIR, exist_ok=True)
    css = open(os.path.join(RULE, 'assets/site.css'), encoding='utf-8').read() + EXTRA_CSS
    open(os.path.join(SITE, 'assets/site.css'), 'w', encoding='utf-8').write(css)
    open(os.path.join(SITE, 'assets/site.js'), 'w', encoding='utf-8').write(open(os.path.join(RULE, 'assets/site.js'), encoding='utf-8').read())
    shutil.copy(os.path.join(HERE, 'zoom.js'), os.path.join(SITE, 'assets/zoom.js'))
    shutil.copy(os.path.join(RULE, 'assets/hero-bookshelf.jpg'), os.path.join(SITE, 'assets/hero-bookshelf.jpg'))

    assets = Assets(IMGDIR)
    chapters = []
    pages = {}
    for cid, num, title, sub, slug, tags, docs in CHAPTERS:
        secs = []
        for stem, mode, stitle in docs:
            doc = hwp3.load(os.path.join(RAW, stem + '.hwp'))
            r = Renderer(stem.replace(' ', ''), doc, assets)
            secs.extend(r.sections(mode, stitle))
        chapters.append({'id': cid, 'number': num, 'title': title, 'subtitle': sub, 'tags': tags,
                         'file': f'{slug}_{COURSE["version"]}.html', 'secs': secs})
    chapters.append(resources_chapter())
    assets.convert()

    from PIL import Image as _I
    _dims = {}
    def dims(rel):
        if rel not in _dims:
            path = os.path.join(SITE, rel)
            if rel.endswith('.svg'):
                t = open(path, encoding='utf-8').read(600)
                m = re.search(r'width="(\d+)" height="(\d+)"', t)
                _dims[rel] = (int(m.group(1)), int(m.group(2))) if m else None
            else:
                _dims[rel] = _I.open(path).size
        return _dims[rel]
    def add_dims(m):
        d = dims(m.group(1))
        return m.group(0) + (' width="%d" height="%d"' % d if d else '')
    def fix(s):
        s = re.sub(r'@@IMG:([^@]+)@@', lambda m: assets.rename.get(m.group(1), m.group(1)), s)
        return re.sub(r'<img src="(assets/(?:img|slides)/[^"]+)"', add_dims, s)

    for ch in chapters:
        body = ''.join(section_html(i, t, b) for i, (t, b) in enumerate(ch['secs']))
        html_page = page(f"제{ch['number']:02d}장 · {ch['title']}", f"{COURSE['course_code']} · CHAPTER {ch['number']:02d}",
                         ch['subtitle'], ch['tags'], body, ch['id'], css, None, chapters)
        open(os.path.join(SITE, ch['file']), 'w', encoding='utf-8').write(fix(html_page))

    cards = ''.join(f'<a class="chapter-card" href="{esc(c["file"])}"><span>CHAPTER {c["number"]:02d}</span><b>{esc(c["title"])}</b><span>{esc(c["subtitle"])}</span></a>' for c in chapters)
    flow = '<div class="flow">' + ''.join(('<div class="down">↓</div>' if i else '') + f'<div class="step"><strong>{c["number"]:02d} · {esc(c["title"])}</strong> — {esc(c["subtitle"])}</div>' for i, c in enumerate(chapters)) + '</div>'
    intro = (f'<p>{esc(COURSE["site_description"])}</p>'
             '<p>직종은 전기계측제어, 소요시간은 이론 80시간·실기 200시간입니다. 각 과제는 관련지식 학습 → 작업도면 → 기능(동작) 설명 → 기술·기능 학습활동 → 작업계획 → 실습결과 보고 → 평가 순서로 진행합니다.</p>'
             '<p>이 사이트는 1999년 대한상공회의소 직업교육훈련사업단 프로젝트지도서 99-36 「라인 마이크로 로봇 제작하기」(집필 정병우, 검토 안상채)의 한글 97 원고를 웹 문서로 옮긴 것입니다.</p>')
    index_body = (section_html(0, '과정 개요', intro) + section_html(1, '전체 학습 테크트리', flow) +
                  section_html(2, '장별 목차', f'<div class="chapter-grid">{cards}</div>') +
                  section_html(3, '학습 방법', '<p>각 장의 관련 이론을 읽고 절 끝의 연습문제에 답한 뒤, 작업도면과 작업계획서에 따라 회로를 제작합니다. 제작 후에는 실습결과보고서를 작성하고 평가표로 스스로 점검합니다.</p><p>원본 한글 파일과 회로도(OrCAD), 발표 자료는 제10장에서 내려받을 수 있습니다.</p>'))
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(
        fix(page(COURSE['site_title'], COURSE['course_code'], COURSE['site_description'], ['Z80', '모터 제어', '센서', '라인 트레이서'], index_body, '', css, None, chapters)))
    return chapters, assets


if __name__ == '__main__':
    chs, a = build()
    for c in chs:
        print(c['file'], [t for t, _ in c['secs']])
