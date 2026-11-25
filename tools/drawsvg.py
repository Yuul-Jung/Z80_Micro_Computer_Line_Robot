"""Render HWP 3.0 drawing objects (picture type 3) to SVG."""
import struct, html, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hwp3


def rgb(c):
    return '#%02x%02x%02x' % (c & 0xFF, (c >> 8) & 0xFF, (c >> 16) & 0xFF)


def para_lines(paras):
    out = []
    for p in paras:
        t = ''.join(x for x in p['items'] if isinstance(x, str))
        out.append((t, p['size']))
    return out


class Drawing:
    def __init__(self, pic):
        raw = pic['raw']
        self.d = raw[8 + 348:]
        self.w, self.h = pic['w'], pic['h']
        self.els = []
        self.warn = []

    def parse(self):
        d = self.d
        hl, zo, cnt = struct.unpack_from('<III', d, 0)
        self.box = struct.unpack_from('<iiii', d, 12)
        p = 4 + hl
        if hl > 24:
            pass
        self.cnt = cnt
        for _ in range(cnt):
            if p + 52 > len(d):
                break
            p = self.obj(p)
        return self

    def obj(self, p):
        d = self.d
        hl, = struct.unpack_from('<I', d, p)
        h = d[p + 4:p + 4 + hl]
        kind, link = struct.unpack_from('<HH', h, 0)
        rx, ry, sw, sh, ax, ay = struct.unpack_from('<iiiiii', h, 4)
        ls, ea, sa, lc, lw, fc, pat, pc, mx, my, opt = struct.unpack_from('<IIIIIIIIiiI', h, 44)
        q = p + 4 + hl
        text = None
        if kind == 6 or (opt >> 19) & 1:
            a, = struct.unpack_from('<I', d, q); q += 4
            n, = struct.unpack_from('<I', d, q); q += 4
            try:
                r = hwp3.Reader(d[q:q + n]); text = r.para_list()
            except Exception as e:
                self.warn.append('text %r' % e)
            q += n
            if kind == 6:
                o = dict(kind=kind, x=ax, y=ay, w=sw, h=sh, lc=lc, lw=lw, ls=ls, fc=fc, pat=pat, opt=opt, text=text, pts=None, flip=0, mx=mx, my=my)
                self.els.append(o)
                return q
        l1, = struct.unpack_from('<I', d, q); q += 4
        det1 = d[q:q + l1]; q += l1
        l2, = struct.unpack_from('<I', d, q); q += 4
        det2 = d[q:q + l2]; q += l2
        pts, flip = None, 0
        if kind in (1, 4) and len(det1) >= 4:
            flip, = struct.unpack_from('<I', det1, 0)
        if kind in (5, 7, 10) and len(det1) >= 4:
            np_, = struct.unpack_from('<I', det1, 0)
            pts = [struct.unpack_from('<ii', det2, 8 * i) for i in range(min(np_, len(det2) // 8))]
        o = dict(kind=kind, x=ax, y=ay, w=sw, h=sh, lc=lc, lw=lw, ls=ls, ea=ea, sa=sa, fc=fc, pat=pat, opt=opt,
                 text=text, pts=pts, flip=flip, mx=mx, my=my)
        if kind:
            self.els.append(o)
        return q

    def svg(self):
        W, H = max(self.w, 1), max(self.h, 1)
        W = int(W * 1.06)
        out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Noto Sans CJK KR, Malgun Gothic, sans-serif">'
               % (W, H, round(W / 18.75), round(H / 18.75)),
               '<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="context-stroke"/></marker></defs>',
               '<rect width="100%" height="100%" fill="#fff"/>']
        for e in self.els:
            sw = max(e['lw'], 8)
            stroke = 'none' if (e['lc'] & 0xFF000000) else rgb(e['lc'])
            dash = ' stroke-dasharray="%d %d"' % (sw * 4, sw * 3) if (e['ls'] & 0xFF) in (1, 2, 3, 4) else ''
            filled = (e['pat'] & 0xFFFFFF) != 0 or e['fc'] not in (0xFFFFFF, 0xFFFFFFFF) and e['kind'] in (2, 3, 5, 7, 10)
            fill = 'none' if (e['kind'] in (1, 4) or (e['fc'] & 0xFF000000)) else rgb(e['fc'])
            if (e['pat'] >> 25) & 1:
                fill = '#d9d9d9'
            mk = ''
            if e.get('ea'): mk += ' marker-end="url(#ah)"'
            if e.get('sa'): mk += ' marker-start="url(#ah)"'
            st = 'stroke="%s" stroke-width="%d" fill="%s"%s' % (stroke, sw, fill, dash)
            x, y, w, h = e['x'], e['y'], e['w'], e['h']
            k = e['kind']
            if k == 1:
                x1, y1, x2, y2 = x, y, x + w, y + h
                if e['flip'] & 1: x1, x2 = x2, x1
                if e['flip'] & 2: y1, y2 = y2, y1
                out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" %s%s/>' % (x1, y1, x2, y2, st, mk))
            elif k == 2:
                rr = min(w, h) // 6 if e['opt'] & 1 else 0
                out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="%d" %s/>' % (x, y, w, h, rr, st))
            elif k in (3, 8):
                out.append('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" %s/>' % (x + w / 2, y + h / 2, w / 2, h / 2, st))
            elif k in (4, 9):
                # quarter ellipse arc inside bounding box, flips choose quadrant
                fx, fy = e['flip'] & 1, e['flip'] & 2
                sx, sy = (x + w, y) if not fx else (x, y)
                ex, ey = (x, y + h) if not fx else (x + w, y + h)
                if fy: sy, ey = (y + h, y) if True else (sy, ey)
                out.append('<path d="M%d,%d A%d,%d 0 0,%d %d,%d" %s%s/>' % (sx, sy, w, h, 0 if fx else 1, ex, ey, st, mk))
            elif k == 7 and e['pts'] and (len(e['pts']) - 1) % 3 == 0 and len(e['pts']) > 1:
                P = [(x + px, y + py) for px, py in e['pts']]
                dd = 'M%d,%d ' % P[0] + ' '.join('C%d,%d %d,%d %d,%d' % (P[i][0], P[i][1], P[i+1][0], P[i+1][1], P[i+2][0], P[i+2][1]) for i in range(1, len(P) - 2, 3))
                if (e['opt'] >> 5) & 1: dd += ' Z'
                out.append('<path d="%s" %s%s/>' % (dd, st, mk))
            elif k in (5, 7, 10) and e['pts']:
                pts = ' '.join('%d,%d' % (x + px, y + py) for px, py in e['pts'])
                tag = 'polygon' if (e['opt'] >> 5) & 1 else 'polyline'
                out.append('<%s points="%s" %s%s/>' % (tag, pts, st, mk))
            if e.get('text'):
                if k == 6:
                    out.append('<rect x="%d" y="%d" width="%d" height="%d" %s/>' % (x, y, w, h, st))
                lines = para_lines(e['text'])
                ty = y + max(e.get('my', 0), 60)
                center = (e['opt'] >> 4) & 1
                for t, size in lines:
                    fs = size or 250
                    ty += fs
                    tx = x + w / 2 if center else x + max(e.get('mx', 0), 60)
                    anchor = ' text-anchor="middle"' if center else ''
                    if t.strip():
                        out.append('<text x="%d" y="%d" font-size="%d"%s xml:space="preserve">%s</text>' % (tx, ty - fs * 0.15, fs, anchor, html.escape(t.rstrip())))
                    ty += fs * 0.6
        out.append('</svg>')
        return '\n'.join(out)


if __name__ == '__main__':
    import json
    doc = hwp3.load(sys.argv[1])
    idx = int(sys.argv[2])
    pics = []
    def walk(paras):
        for p in paras:
            for it in p['items']:
                if isinstance(it, dict):
                    if it['type'] == 'picture' and it['ptype'] == 3: pics.append(it)
                    if it['type'] == 'box':
                        for c in it['cells']: walk(c['paras'])
    walk(doc['paras'])
    dr = Drawing(pics[idx]).parse()
    for e in dr.els:
        print({k: v for k, v in e.items() if k not in ('text',)}, 'TEXT' if e.get('text') else '')
    print(dr.warn)
    open(sys.argv[3], 'w').write(dr.svg())


def classify(pic):
    """Return ('svg', svgtext) for real diagrams, or ('text', str) for caption/text boxes."""
    try:
        dr = Drawing(pic).parse()
    except Exception:
        return ('text', '')
    shapes = [e for e in dr.els if e['kind'] != 6]
    texts = []
    for e in dr.els:
        if e.get('text'):
            texts.extend(t for t, _ in para_lines(e['text']) if t.strip())
    if pic['w'] > 2500 and pic['h'] > 800 and len(shapes) >= 2:
        return ('svg', dr.svg())
    return ('text', ' '.join(t.strip() for t in texts))
