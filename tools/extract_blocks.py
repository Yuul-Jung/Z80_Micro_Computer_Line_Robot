import sys, struct, os, glob
sys.path.insert(0, os.path.dirname(__file__))
import hwp3
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
for path in sorted(glob.glob(os.path.join(sys.argv[1], '*.hwp'))):
    doc = hwp3.load(path)
    stem = os.path.basename(path)[:-4].replace(' ', '')
    r = doc['rest']; q = 0
    while q + 8 <= len(r):
        bid, ln = struct.unpack_from('<II', r, q)
        if bid == 0 and ln == 0: break
        data = r[q + 8:q + 8 + ln]
        if bid == 1:
            name = data[:16].split(b'\0')[0].decode('ascii', 'replace')
            open(os.path.join(out, stem + '__' + name), 'wb').write(data[32:])
        elif bid == 2:
            open(os.path.join(out, stem + '__ole.bin'), 'wb').write(data)
        q += 8 + ln
