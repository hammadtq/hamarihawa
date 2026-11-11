# Minimal PNG decoder (8-bit, colour types 2/3/6, non-interlaced) returning list of RGBA tuples.
import struct, zlib
def decode(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    pos = 8; idat = b''; plte = None; trns = None
    while pos < len(data):
        n, typ = struct.unpack('>I4s', data[pos:pos+8]); body = data[pos+8:pos+8+n]; pos += 12 + n
        if typ == b'IHDR': w, h, bd, ct, _, _, il = struct.unpack('>IIBBBBB', body)
        elif typ == b'PLTE': plte = [tuple(body[i:i+3]) for i in range(0, len(body), 3)]
        elif typ == b'tRNS': trns = body
        elif typ == b'IDAT': idat += body
        elif typ == b'IEND': break
    assert bd == 8 and il == 0, (bd, il)
    bpp = {2: 3, 3: 1, 6: 4, 0: 1, 4: 2}[ct]
    raw = zlib.decompress(idat); stride = w * bpp; out = []; prev = bytearray(stride); i = 0
    for _ in range(h):
        f = raw[i]; line = bytearray(raw[i+1:i+1+stride]); i += 1 + stride
        for x in range(stride):
            a = line[x-bpp] if x >= bpp else 0; b = prev[x]; c = prev[x-bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c; pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        for x in range(w):
            if ct == 6: out.append(tuple(line[x*4:x*4+4]))
            elif ct == 2: out.append(tuple(line[x*3:x*3+3]) + (255,))
            elif ct == 3:
                k = line[x]; al = trns[k] if trns and k < len(trns) else 255
                out.append(plte[k] + (al,))
            elif ct == 0: out.append((line[x],)*3 + (255,))
            elif ct == 4: out.append((line[x*2],)*3 + (line[x*2+1],))
        prev = line
    return w, h, out
