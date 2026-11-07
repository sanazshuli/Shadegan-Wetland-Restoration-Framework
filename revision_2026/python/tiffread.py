import numpy as np, tifffile

def lzw_decode(data):
    # TIFF LZW (MSB-first, early change)
    out = bytearray(); table = [bytes([i]) for i in range(256)] + [b'', b'']
    bitpos = 0; nbits = 9; prev = None; n = len(data) * 8
    def read(bp, nb):
        v = 0
        for i in range(nb):
            byte = data[(bp + i) >> 3]
            v = (v << 1) | ((byte >> (7 - ((bp + i) & 7))) & 1)
        return v
    while bitpos + nbits <= n:
        code = read(bitpos, nbits); bitpos += nbits
        if code == 256:
            table = table[:258]; nbits = 9; prev = None; continue
        if code == 257: break
        if prev is None:
            entry = table[code]
        elif code < len(table):
            entry = table[code]; table.append(prev + entry[:1])
        else:
            entry = prev + prev[:1]; table.append(entry)
        out += entry; prev = entry
        if len(table) + 1 >= (1 << nbits) and nbits < 12:
            nbits += 1
    return bytes(out)

def read_geotiff(path):
    t = tifffile.TiffFile(path); p = t.pages[0]
    H, W = p.shape[:2]; dt = np.dtype(p.dtype).newbyteorder(t.byteorder)
    arr = np.full((H, W), np.nan)
    tl, tw = p.tilelength, p.tilewidth
    ntx = -(-W // tw)
    fh = t.filehandle
    for i, (off, cnt) in enumerate(zip(p.dataoffsets, p.databytecounts)):
        fh.seek(off); raw = fh.read(cnt)
        dec = lzw_decode(raw) if p.compression == 5 else raw
        tile = np.frombuffer(dec[:tl * tw * dt.itemsize], dtype=dt).reshape(tl, tw)
        ty, tx = divmod(i, ntx)
        y0, x0 = ty * tl, tx * tw
        h, w = min(tl, H - y0), min(tw, W - x0)
        arr[y0:y0 + h, x0:x0 + w] = tile[:h, :w]
    tags = {k.name: k.value for k in p.tags.values()}
    nod = tags.get('GDAL_NODATA')
    if nod is not None:
        arr[arr == float(str(nod).strip('\x00'))] = np.nan
    return arr, tags
