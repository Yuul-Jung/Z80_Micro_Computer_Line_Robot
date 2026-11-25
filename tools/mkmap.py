import struct, zlib, sys
src = open(sys.argv[1], 'rb').read()
di = src[30:158]
ib = struct.unpack_from('<H', di, 126)[0]
head = src[:30 + 128 + 1008 + ib]
z = zlib.decompress(src[len(head):], -15)
p = 0
for _ in range(7):
    n = struct.unpack_from('<H', z, p)[0]; p += 2 + 40 * n
n = struct.unpack_from('<H', z, p)[0]; p += 2 + 238 * n
pre = z[:p]
first = z[p:p + 230]           # first para header incl. para shape (prev must be 0)
assert first[0] == 0
cs = first[12:43]
def para(chars, firstp=False):
    hc = [ord(c) for c in chars] if isinstance(chars, str) else chars
    hc = hc + [13]
    if firstp:
        h = bytearray(first); struct.pack_into('<HHBB', h, 1, len(hc), 1, 0, 0); struct.pack_into('<I', h, 7, 0)
    else:
        h = bytearray(struct.pack('<BHHBBIB', 1, len(hc), 1, 0, 0, 0, 0)) + cs
    return bytes(h) + b'\0' * 14 + b''.join(struct.pack('<H', c) for c in hc)
codes = list(range(0x80, 0x100)) + list(range(0x2000, 0x4000))
body = [para('START', True)]
for c in codes:
    body.append(para([ord(x) for x in '%04X=' % c] + [c, ord('|')]))
term = struct.pack('<BHHBBIB', 1, 0, 0, 0, 0, 0, 0) + cs
newz = pre + b''.join(body) + term + b'\0' * 64
comp = zlib.compressobj(9, zlib.DEFLATED, -15)
out = head + comp.compress(newz) + comp.flush()
open(sys.argv[2], 'wb').write(out)
