import struct, numpy as np

A = 6378137.0; F = 1 / 298.257223563; E2 = F * (2 - F); E = np.sqrt(E2)

def lcc_inverse(x, y, lon0=54.0, lat1=30.0, lat2=36.0, lat0=24.0, fe=0.0, fn=0.0):
    r = np.deg2rad
    def m(p): return np.cos(p) / np.sqrt(1 - E2 * np.sin(p) ** 2)
    def t(p): return np.tan(np.pi / 4 - p / 2) / ((1 - E * np.sin(p)) / (1 + E * np.sin(p))) ** (E / 2)
    p1, p2, p0 = r(lat1), r(lat2), r(lat0)
    n = (np.log(m(p1)) - np.log(m(p2))) / (np.log(t(p1)) - np.log(t(p2)))
    Fc = m(p1) / (n * t(p1) ** n); rho0 = A * Fc * t(p0) ** n
    x = np.asarray(x) - fe; y = np.asarray(y) - fn
    rho = np.sign(n) * np.sqrt(x ** 2 + (rho0 - y) ** 2)
    tt = (rho / (A * Fc)) ** (1 / n); theta = np.arctan2(x, rho0 - y)
    lam = theta / n + r(lon0)
    phi = np.pi / 2 - 2 * np.arctan(tt)
    for _ in range(10):
        phi = np.pi / 2 - 2 * np.arctan(tt * ((1 - E * np.sin(phi)) / (1 + E * np.sin(phi))) ** (E / 2))
    return np.rad2deg(lam), np.rad2deg(phi)

def utm_inverse(x, y, zone=39, north=True):
    k0 = 0.9996; x = np.asarray(x) - 500000.0; y = np.asarray(y) - (0 if north else 1e7)
    ep2 = E2 / (1 - E2); M = y / k0
    mu = M / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - np.sqrt(1 - E2)) / (1 + np.sqrt(1 - E2))
    p1 = mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu) \
        + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu)
    C1 = ep2 * np.cos(p1) ** 2; T1 = np.tan(p1) ** 2; N1 = A / np.sqrt(1 - E2 * np.sin(p1) ** 2)
    R1 = A * (1 - E2) / (1 - E2 * np.sin(p1) ** 2) ** 1.5; D = x / (N1 * k0)
    lat = p1 - (N1 * np.tan(p1) / R1) * (D ** 2 / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * ep2) * D ** 4 / 24
                                         + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * ep2 - 3 * C1 ** 2) * D ** 6 / 720)
    lon = (D - (1 + 2 * T1 + C1) * D ** 3 / 6 + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * ep2 + 24 * T1 ** 2) * D ** 5 / 120) / np.cos(p1)
    return np.rad2deg(lon) + (zone - 1) * 6 - 180 + 3, np.rad2deg(lat)

def read_dbf(path):
    b = open(path, 'rb').read(); n = struct.unpack('<I', b[4:8])[0]; hl, rl = struct.unpack('<HH', b[8:12])
    fields = []; o = 32
    while b[o] != 0x0D:
        name = b[o:o + 11].split(b'\x00')[0].decode('latin1'); ln = b[o + 16]; fields.append((name, ln)); o += 32
    recs = []
    for i in range(n):
        r = b[hl + i * rl + 1: hl + (i + 1) * rl]; d = {}; p = 0
        for name, ln in fields:
            raw = r[p:p + ln]
            try: d[name] = raw.decode('utf-8').strip()
            except UnicodeDecodeError: d[name] = raw.decode('latin1').strip()
            p += ln
        recs.append(d)
    return recs

def read_shp(path):
    """Return list of records; each record is a list of parts (N x 2 arrays)."""
    b = open(path, 'rb').read(); o = 100; out = []
    while o < len(b):
        clen = struct.unpack('>i', b[o + 4:o + 8])[0] * 2; c = b[o + 8:o + 8 + clen]; o += 8 + clen
        st = struct.unpack('<i', c[:4])[0]
        if st == 0: out.append([]); continue
        if st in (3, 5, 13, 15, 23, 25):
            npart, npt = struct.unpack('<ii', c[36:44])
            parts = list(struct.unpack(f'<{npart}i', c[44:44 + 4 * npart])) + [npt]
            pts = np.frombuffer(c[44 + 4 * npart:44 + 4 * npart + 16 * npt], dtype='<f8').reshape(-1, 2)
            out.append([pts[parts[i]:parts[i + 1]] for i in range(npart)])
        elif st == 1:
            out.append([np.frombuffer(c[4:20], dtype='<f8').reshape(1, 2)])
    return out
