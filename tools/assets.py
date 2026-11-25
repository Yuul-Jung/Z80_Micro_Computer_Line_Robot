"""Resolve every HWP picture to a web image file (PNG/JPG/GIF) under site/assets/img."""
import os, re, struct, shutil, subprocess, hashlib, glob
import olefile
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'raw')
EMB = os.path.join(ROOT, 'emb')
WORK = os.path.join(ROOT, 'work_img')


def drawing_text(raw):
    """Pull readable caption text out of a drawing object."""
    import hwp3
    b = raw[8 + 348:]
    best = []
    for par in (0, 1):
        s = []
        for i in range(par, len(b) - 1, 2):
            v = struct.unpack_from('<H', b, i)[0]
            ch = hwp3.hchar_to_str(v) if (v >= 0x8000 or 0x20 <= v < 0x7f or 0x3400 <= v < 0x3800) else ''
            s.append(ch if ch else '|')
        parts = [p.strip() for p in re.sub(r'\|+', '|', ''.join(s)).split('|')]
        parts = [p for p in parts if re.search('[가-힣]', p) and len(p) > 1 and not re.search(r"[\\'\*]", p)]
        if sum(len(p) for p in parts) > sum(len(p) for p in best):
            best = parts
    return ' '.join(best)


def ole_wmf(stem, storage):
    path = os.path.join(EMB, stem + '__ole.bin')
    if not os.path.exists(path):
        return None
    o = olefile.OleFileIO(open(path, 'rb').read()[4:])
    name = storage + '/\x02OlePres000'
    if not o.exists(name):
        return None
    d = o.openstream(name).read()
    for sig in (b'\x01\x00\x09\x00\x00\x03', b'\x02\x00\x09\x00\x00\x03'):
        k = d.find(sig)
        if k >= 0:
            return d[k:]
    return None


def wmf_single_dib(w):
    """If a WMF is just one bitmap blit, return it as BMP file bytes."""
    p = 18; dibs = []; draw = 0
    while p + 6 <= len(w):
        sz, fn = struct.unpack_from('<IH', w, p)
        if sz == 0 or fn == 0:
            break
        if fn == 0x940:
            dibs.append(w[p + 26:p + sz * 2])
        elif fn == 0xf43:
            dibs.append(w[p + 28:p + sz * 2])
        elif fn in (0x324, 0x538, 0x418, 0x41b, 0x213, 0x521, 0xa32, 0x325, 0x817):
            draw += 1
        p += sz * 2
    if len(dibs) != 1 or draw:
        return None
    d = dibs[0]
    hsize, = struct.unpack_from('<I', d, 0)
    bits, = struct.unpack_from('<H', d, 14)
    clr, = struct.unpack_from('<I', d, 32)
    ncol = clr if clr else (1 << bits if bits <= 8 else 0)
    off = 14 + hsize + 4 * ncol
    return b'BM' + struct.pack('<IHHI', 14 + len(d), 0, 0, off) + d


def fix_wmf_charset(w):
    """Force Korean charset on fonts so CP949 text records render as Hangul."""
    w = bytearray(w)
    p = 22 if w[:4] == b'\xd7\xcd\xc6\x9a' else 0
    hdr = struct.unpack_from('<H', w, p + 2)[0] * 2
    p += hdr
    while p + 6 <= len(w):
        sz, fn = struct.unpack_from('<IH', w, p)
        if sz == 0:
            break
        if fn == 0x2FB and p + 6 + 14 <= len(w):
            if w[p + 6 + 13] in (0, 1):
                w[p + 6 + 13] = 129
        p += sz * 2
    return bytes(w)


class Assets:
    def __init__(self, outdir):
        self.out = outdir
        os.makedirs(outdir, exist_ok=True)
        os.makedirs(WORK, exist_ok=True)
        self.jobs = {}      # wmf path -> output basename
        self.done = {}      # key -> filename

    def _name(self, key, ext):
        h = hashlib.md5(key.encode()).hexdigest()[:10]
        return 'img_' + h + ext

    def picture(self, stem, pic):
        """Return (filename or None, extra caption text)."""
        t, f = pic['ptype'], pic['file']
        key = '%s|%d|%s' % (stem, t, f)
        if t == 3:
            import drawsvg
            kind, val = drawsvg.classify(pic)
            if kind == 'svg':
                name = self._name(key + '|%d' % len(self.done), '.svg')
                open(os.path.join(self.out, name), 'w', encoding='utf-8').write(val)
                self.done[key + '|%d' % len(self.done)] = name
                return name, ''
            return None, val or drawing_text(pic['raw'])
        if key in self.done:
            return self.done[key], ''
        if t == 0:
            src = os.path.join(RAW, f)
            if not os.path.exists(src):
                return None, ''
            name = self._name(key, os.path.splitext(f)[1].lower())
            shutil.copy(src, os.path.join(self.out, name))
        elif t == 2:
            src = os.path.join(EMB, stem + '__' + f)
            if not os.path.exists(src):
                return None, ''
            ext = os.path.splitext(f)[1].lower()
            if ext == '.wmf':
                name = self._name(key, '.png')
                self.jobs[src] = name
            else:
                name = self._name(key, ext)
                shutil.copy(src, os.path.join(self.out, name))
        elif t == 1:
            wmf = ole_wmf(stem, f)
            if not wmf:
                return None, ''
            dib = wmf_single_dib(wmf)
            im = None
            if dib:
                import io
                try:
                    im = Image.open(io.BytesIO(dib)).convert('RGB')
                except Exception:
                    im = None
            if im is not None:
                if im.getcolors(4096) is None:
                    name = self._name(key, '.jpg'); im.save(os.path.join(self.out, name), quality=86)
                else:
                    name = self._name(key, '.png'); im.save(os.path.join(self.out, name), optimize=True)
                self.done[key] = name
                return name, ''
            src = os.path.join(WORK, self._name(key, '.wmf'))
            open(src, 'wb').write(wmf)
            name = self._name(key, '.png')
            self.jobs[src] = name
        else:
            return None, ''
        self.done[key] = name
        return name, ''

    def convert(self):
        """Convert queued WMF files: WMF -> PDF (LibreOffice) -> PNG 150dpi -> trim."""
        tmp = os.path.join(WORK, 'conv')
        os.makedirs(tmp, exist_ok=True)
        items = list(self.jobs.items())
        for i, (src, name) in enumerate(items):
            dst = os.path.join(tmp, '%03d.wmf' % i)
            open(dst, 'wb').write(fix_wmf_charset(open(src, 'rb').read()))
        files = sorted(glob.glob(os.path.join(tmp, '*.wmf')))
        for k in range(0, len(files), 20):
            subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', tmp] + files[k:k + 20],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900)
        for i, (src, name) in enumerate(items):
            pdf = os.path.join(tmp, '%03d.pdf' % i)
            if not os.path.exists(pdf):
                print('convert failed', src); continue
            base = os.path.join(tmp, '%03d' % i)
            subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', pdf, base], check=True)
            im = Image.open(base + '.png').convert('RGB')
            bg = Image.new('RGB', im.size, (255, 255, 255))
            bbox = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
            if bbox:
                pad = 12
                bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(im.width, bbox[2] + pad), min(im.height, bbox[3] + pad))
                im = im.crop(bbox)
            out = os.path.join(self.out, name)
            colors = im.getcolors(4096)
            g = im.convert('L').resize((max(1, im.width // 4), max(1, im.height // 4)))
            white = sum(1 for v in g.getdata() if v > 235) / (g.width * g.height)
            if colors is None and white <= 0.55:   # photo-like -> jpeg
                jpg = name[:-4] + '.jpg'
                im.thumbnail((2000, 2000))
                im.save(os.path.join(self.out, jpg), quality=86)
                self.rename[name] = jpg
                continue
            if im.width > 1900:   # large circuit drawing: re-render at 600 dpi for zooming
                subprocess.run(['pdftoppm', '-r', '600', '-png', '-singlefile', pdf, base + 'h'], check=True)
                hi = Image.open(base + 'h.png').convert('RGB')
                im = hi.crop(tuple(v * 2 for v in bbox)) if bbox else hi
                colors = im.getcolors(4096)
            n = 256 if (colors is None or len(colors) > 256) else len(colors)
            im.quantize(n).save(out, optimize=True)

    rename = {}
