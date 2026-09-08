#!/usr/bin/env python3
"""Salva as etapas que a foto passa: original -> filtros -> escalas -> medias -> grupos.
Uso: python src/etapas.py foto.jpg --out out_etapas/ [--k 3]
Gera PNGs numerados + um contato etapas.png.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np

from textura import (base_responses, load_gray, pyramid3, segment_image,
                     texture_maps, window_means)

NAMES8 = ["gabor0", "gabor45", "gabor90", "gabor135",
          "gauss-circ", "laplac-circ", "sobelX", "sobelY"]


def norm01(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float32)
    lo, hi = float(a.min()), float(a.max())
    if hi - lo < 1e-9:
        return np.zeros_like(a)
    return (a - lo) / (hi - lo)


def save_gray(path: Path, img: np.ndarray):
    cv2.imwrite(str(path), (np.clip(img, 0, 1) * 255).astype(np.uint8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("img")
    ap.add_argument("--out", default="out_etapas")
    ap.add_argument("--k", type=int, default=3)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    gray = load_gray(Path(a.img))
    save_gray(out / "00_original.png", gray)

    # 1) 8 respostas base
    bases = base_responses(gray)
    for i, (n, r) in enumerate(zip(NAMES8, bases)):
        save_gray(out / f"1{i}_base_{n}.png", norm01(r))

    # 2) exemplo de piramide: gabor0 nas 3 escalas
    for s, lvl in enumerate(pyramid3(bases[0])):
        save_gray(out / f"2{s}_escala_gabor0_L{s}.png", norm01(lvl))

    # 3) medias em janela (o vetor 24D): mostra 3 (gabor0 L0/L2 + gauss L0)
    maps = texture_maps(gray)
    means = window_means(maps)
    for tag, idx in [("gabor0_L0", 0), ("gabor0_L2", 2), ("gauss-circ_L0", 12)]:
        save_gray(out / f"3x_media_{tag}.png", norm01(means[:, :, idx]))

    # 4) agrupamento euclidiano
    segment_image(Path(a.img), a.k, 4, out / "40_segmentado.png")

    # contato: original + 8 bases + 3 escalas + segmentado
    thumbs = [cv2.imread(str(out / "00_original.png"), 0)]
    thumbs += [cv2.imread(str(out / f"1{i}_base_{n}.png"), 0)
               for i, n in enumerate(NAMES8)]
    thumbs += [cv2.imread(str(out / f"2{s}_escala_gabor0_L{s}.png"), 0) for s in range(3)]
    seg = cv2.imread(str(out / "40_segmentado.png"))
    h, w = 128, 128
    row = np.hstack([cv2.resize(t, (w, h)) for t in thumbs[:6]])
    row2 = np.hstack([cv2.resize(t, (w, h)) for t in thumbs[6:12]])
    seg_small = cv2.resize(seg, (w * 6, h))
    row_c = cv2.cvtColor(row, cv2.COLOR_GRAY2BGR)
    row2_c = cv2.cvtColor(row2, cv2.COLOR_GRAY2BGR)
    contato = np.vstack([row_c, row2_c, seg_small])
    cv2.imwrite(str(out / "etapas.png"), contato)
    print(f"ok -> {out}/ (13 PNGs + etapas.png)")


if __name__ == "__main__":
    main()
