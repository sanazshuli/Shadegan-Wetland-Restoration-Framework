import numpy as np, tifffile, re

def lzw_decode(data):
    out = bytearray(); table = [bytes([i]) for i in range(256)] + [b'', b'']
    buf = 0; nb = 0; nbits = 9; prev = None; pos = 0; L = len(data)
    while True:
        while nb < nbits:
            if pos >= L: return bytes(out)
            buf = (buf << 8) | data[pos]; pos += 1; nb += 8
        nb -= nbits; code = (buf >> nb) & ((1 << nbits) - 1); buf &= (1 << nb) - 1
        if code == 256:
            del table[258:]; nbits = 9; prev = None; continue
        if code == 257: break
        if prev is None: entry = table[code]
        elif code < len(table):
            entry = table[code]; table.append(prev + entry[:1])
        else:
            entry = prev + prev[:1]; table.append(entry)
        out += entry; prev = entry
        if len(table) + 1 >= (1 << nbits) and nbits < 12: nbits += 1
    return bytes(out)

def read_stack(path):
    t = tifffile.TiffFile(path); p = t.pages[0]
    H, W = p.shape[:2]; S = p.samplesperpixel
    dt = np.dtype(p.dtype).newbyteorder(t.byteorder)
    arr = np.full((H, W, S), np.nan, dtype=np.float32)
    tl, tw = p.tilelength, p.tilewidth; ntx = -(-W // tw); fh = t.filehandle
    for i, (off, cnt) in enumerate(zip(p.dataoffsets, p.databytecounts)):
        fh.seek(off); dec = lzw_decode(fh.read(cnt))
        tile = np.frombuffer(dec[:tl*tw*S*dt.itemsize], dtype=dt).reshape(tl, tw, S)
        ty, tx = divmod(i, ntx); y0, x0 = ty*tl, tx*tw
        h, w = min(tl, H-y0), min(tw, W-x0)
        arr[y0:y0+h, x0:x0+w] = tile[:h, :w]
    tags = {k.name: k.value for k in p.tags.values()}
    names = re.findall(r'sample="(\d+)" role="description">([^<]+)<', tags.get('GDAL_METADATA', ''))
    names = [n for _, n in sorted(names, key=lambda x: int(x[0]))]
    return arr, names, tags
