"""Minimal HWP 3.0 (Hangul 97) reader -> structured blocks.

Usage: python3 -I hwp3.py file.hwp [--json]
"""
import sys, zlib, struct, json, os

_SYM = {int(k, 16): v for k, v in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'symmap.json'), encoding='utf-8')).items()}
_GREEK = 'αβγδεζηθικλμνξοπρστυφχψω'
_OVR = {0x2053: '×', 0x223C: '∼', 0x22C5: '·', 0x3151: '·', 0x310D: 'μ', 0x3157: '·',
        0x3440: '□', 0x34C5: '%', 0x21E8: '', 0x2322: '', 0x2323: ''}
for _i in range(1, 21):
    _OVR[0x2E00 + _i] = chr(0x2460 + _i - 1)
for _i in range(15):
    _OVR[0x36E7 + _i] = chr(0x2460 + _i)
for _i, _c in enumerate(_GREEK):
    _OVR.setdefault(0x35C1 + _i, _c)

def hchar_to_str(v):
    if v in _OVR:
        return _OVR[v]
    if v in _SYM and _SYM[v] != '\ufffd':
        return _SYM[v]
    r = _raw_hchar(v)
    return '' if r == '\ufffd' else r

def _raw_hchar(v):
    if v < 0x20:
        return ''
    if v < 0x80:
        return chr(v)
    if v >= 0x8000:  # Johab Hangul
        try:
            return struct.pack('>H', v).decode('johab')
        except Exception:
            return '�'
    if 0x4000 <= v < 0x8000:  # Hanja (KS C 5601 order)
        idx = v - 0x4000
        r, c = divmod(idx, 94)
        try:
            return bytes([0xCA + r, 0xA1 + c]).decode('euc-kr')
        except Exception:
            return '�'
    if 0x3400 <= v < 0x4000:  # symbols (KS C 5601 rows 1-12)
        idx = v - 0x3400
        r, c = divmod(idx, 94)
        try:
            return bytes([0xA1 + r, 0xA1 + c]).decode('euc-kr')
        except Exception:
            return '�'
    return '�'


class Reader:
    def __init__(self, data):
        self.d = data
        self.p = 0
        self.warn = []

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v
    def u16(self):
        v = struct.unpack_from('<H', self.d, self.p)[0]; self.p += 2; return v
    def u32(self):
        v = struct.unpack_from('<I', self.d, self.p)[0]; self.p += 4; return v
    def skip(self, n):
        self.p += n
    def peek16(self, off=0):
        return struct.unpack_from('<H', self.d, self.p + off)[0]

    # ---- paragraph list -------------------------------------------------
    def para_list(self):
        paras = []
        while self.p < len(self.d):
            para = self.paragraph()
            if para is None:
                break
            paras.append(para)
        return paras

    def paragraph(self):
        start = self.p
        prev = self.u8()
        nch = self.u16()
        nline = self.u16()
        cflag = self.u8()
        self.u8()           # etc flag
        self.u32()          # special char flag
        style = self.u8()
        rep_cs = self.d[self.p:self.p + 31]; self.skip(31)
        if nch == 0:
            return None  # list terminator (43 bytes only)
        if prev == 0:
            ps = self.d[self.p:self.p + 187]; self.skip(187)
        self.skip(14 * nline)
        if cflag:
            for _ in range(nch):
                f = self.u8()
                if f != 1:
                    self.skip(31)
        size = struct.unpack_from('<H', rep_cs, 0)[0]
        attr = rep_cs[26]
        items = []   # str pieces or dict blocks
        buf = []
        i = 0
        while i < nch:
            ch = self.u16()
            if ch >= 32:
                buf.append(hchar_to_str(ch)); i += 1; continue
            if ch == 13:
                i += 1; break
            if buf:
                items.append(''.join(buf)); buf = []
            blk, used = self.special(ch)
            i += used
            if blk is not None:
                items.append(blk)
        if buf:
            items.append(''.join(buf))
        return {'style': style, 'size': size, 'bold': bool(attr & 2), 'items': items}

    # ---- special characters ---------------------------------------------
    def special(self, ch):
        # returns (block_or_None, hchar_units_consumed)
        if ch in (30, 31):
            self.skip(2)
            return (' ', 2)
        if ch == 9:
            self.skip(6)
            return ('\t', 4)
        if ch in (18, 19, 20, 21):
            self.skip(6); return (None, 4)
        if ch == 22:
            self.skip(22); return (None, 4)
        if ch == 23:
            self.skip(8); return (None, 4)
        if ch in (24, 25):
            self.skip(4); return (None, 4)
        if ch == 26:
            self.skip(244); return (None, 4)
        if ch == 28:
            self.skip(62); return (None, 4)
        if ch == 6:
            self.skip(40); return (None, 4)
        if ch == 7:
            self.skip(82); return (None, 4)
        if ch == 8:
            self.skip(94); return (None, 4)
        if ch == 5:
            n = self.u32(); self.u16(); self.skip(n); return (None, 4)
        if ch == 14:
            self.skip(4); self.u16(); self.skip(84); return (None, 4)
        if ch == 15:
            self.skip(4); self.u16(); self.skip(8)
            paras = self.para_list()
            return ({'type': 'hidden', 'paras': paras}, 4)
        if ch == 16:
            self.skip(4); self.u16(); self.skip(10)
            paras = self.para_list()
            return ({'type': 'headfoot', 'paras': paras}, 4)
        if ch == 17:
            self.skip(4); self.u16(); self.skip(14)
            paras = self.para_list()
            return ({'type': 'footnote', 'paras': paras}, 4)
        if ch == 10:
            return (self.box(), 4)
        if ch == 11:
            st = self.p - 2
            pic = self.picture()
            pic['raw'] = self.d[st:self.p]
            return (pic, 4)
        self.warn.append('unknown special %d at %d' % (ch, self.p))
        n = self.u32(); self.u16(); self.skip(n)
        return (None, 4)

    def box(self):
        self.skip(4); self.u16()
        info = self.d[self.p:self.p + 84]; self.skip(84)
        kind = struct.unpack_from('<H', info, 78)[0]
        ncell = struct.unpack_from('<H', info, 80)[0]
        bw, bh = struct.unpack_from('<HH', info, 42)
        cells = []
        for _ in range(ncell):
            c = self.d[self.p:self.p + 27]; self.skip(27)
            x, y, w, h = struct.unpack_from('<HHHH', c, 4)
            cells.append({'x': x, 'y': y, 'w': w, 'h': h})
        for c in cells:
            c['paras'] = self.para_list()
        caption = self.para_list()
        return {'type': 'box', 'kind': kind, 'w': bw, 'h': bh,
                'cells': cells, 'caption': caption}

    def picture(self):
        n = self.u32(); self.u16()
        info = self.d[self.p:self.p + 348]; self.skip(348)
        n2 = struct.unpack_from('<I', info, 0)[0]
        ptype = info[74]
        fname = info[83:83 + 256].split(b'\0')[0].decode('cp949', 'replace')
        bw, bh = struct.unpack_from('<HH', info, 42)
        extra = self.d[self.p:self.p + n2]; self.skip(n2)
        caption = self.para_list()
        return {'type': 'picture', 'ptype': ptype, 'file': fname,
                'w': bw, 'h': bh, 'n_id': n, 'n_extra': n2,
                'caption': caption}


def load(path):
    d = open(path, 'rb').read()
    assert d.startswith(b'HWP Document File V3.00')
    di = d[30:158]
    comp, ib = di[124], struct.unpack_from('<H', di, 126)[0]
    body = d[30 + 128 + 1008 + ib:]
    z = zlib.decompress(body, -15) if comp else body
    r = Reader(z)
    for _ in range(7):
        n = r.u16(); r.skip(40 * n)
    n = r.u16()
    styles = [z[r.p + i * 238:r.p + i * 238 + 20].split(b'\0')[0].decode('johab', 'replace') for i in range(n)]
    r.skip(238 * n)
    paras = r.para_list()
    return {'styles': styles, 'paras': paras, 'rest': z[r.p:], 'warn': r.warn}


def plain(paras, ind=0):
    out = []
    for p in paras:
        line = []
        for it in p['items']:
            if isinstance(it, str):
                line.append(it)
            elif it['type'] == 'box':
                out.append(' ' * ind + ''.join(line)); line = []
                out.append(' ' * ind + '[BOX kind=%d cells=%d]' % (it['kind'], len(it['cells'])))
                for c in it['cells']:
                    out.extend(plain(c['paras'], ind + 2))
            elif it['type'] == 'picture':
                line.append('[PIC t=%d %s %d/%d]' % (it['ptype'], it['file'], it['n_id'], it['n_extra']))
            else:
                line.append('[%s]' % it['type'])
        out.append(' ' * ind + ''.join(line))
    return out


if __name__ == '__main__':
    doc = load(sys.argv[1])
    print('\n'.join(plain(doc['paras'])))
    print('--- rest bytes:', len(doc['rest']), 'warn:', doc['warn'][:5], file=sys.stderr)
