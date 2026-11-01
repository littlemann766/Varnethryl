"""Stage 11 (Beth): straight coastline / edge finder on a land mask.
Contours at 0.5 of the (sigma 1 px smoothed) mask, Douglas-Peucker at 0.5 m (a run that stays within 0.5 m of a line for 30 m+), every segment >= 30 m is a straight run.
Usage: straight_scan.py <mask.npy> <x0> <z0> <px_m> <out.json> [label]"""
import sys, json, numpy as np
from scipy.ndimage import gaussian_filter
from skimage.measure import find_contours, approximate_polygon
TOL = 0.5
def scan(M, x0, z0, px, label=''):
    U = gaussian_filter(M.astype(float), 1.0); out = []
    for C in find_contours(np.pad(U, 1), 0.5):
        P = np.c_[x0 + (C[:, 1] - 1 + 0.5) * px, z0 + (C[:, 0] - 1 + 0.5) * px]
        if len(P) < 6: continue
        A = approximate_polygon(P, TOL)
        for a, b in zip(A[:-1], A[1:]):
            L = float(np.hypot(*(b - a)))
            if L >= 30.0: out.append({'where': label, 'a': [round(float(a[0])), round(float(a[1]))], 'b': [round(float(b[0])), round(float(b[1]))], 'len_m': round(L)})
    return sorted(out, key=lambda s: -s['len_m'])
if __name__ == '__main__':
    M = np.load(sys.argv[1]); S = scan(M, float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[6] if len(sys.argv) > 6 else '')
    json.dump(S, open(sys.argv[5], 'w'), indent=0); print(len(S), 'straight runs >= 30 m', [s['len_m'] for s in S[:10]])
