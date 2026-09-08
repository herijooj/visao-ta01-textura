#!/usr/bin/env python3
"""Segmentacao/classificacao por textura - so classicos, sem IA.

Banco: 8 filtros base em 1 escala, depois piramide gaussiana (3 escalas).
  1-4: Gabor 0, 45, 90, 135 graus (orientados)
  5:   Gaussiano 5x5 (circular)
  6:   Laplaciano (circular)
  7-8: Sobel X, Sobel Y (H/V)
Piramide: nivel0=512, nivel1=Gauss+pyrDown(256)->resize 512,
          nivel2=de novo (128)->resize 512. 8x3 = 24 mapas.
Vetor: media em janela W de cada mapa -> 24 dims (so media, cf. slides).
Agrupo: KMeans / distancia euclidiana (Lloyd, classico).
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

SIZE = 512
WIN = 31  # janela da media

GABOR_KSIZE = 21
GABOR_SIGMA = 4.0
GABOR_LAMBDA = 10.0
GABOR_GAMMA = 0.5


def base_responses(gray: np.ndarray) -> list:
    """gray float32 0-1 512x512 -> 8 respostas 512x512."""
    g8 = (gray * 255).astype(np.uint8)
    out = []
    for theta in [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4]:
        k = cv2.getGaborKernel((GABOR_KSIZE, GABOR_KSIZE), GABOR_SIGMA,
                               theta, GABOR_LAMBDA, GABOR_GAMMA, 0,
                               ktype=cv2.CV_32F)
        r = cv2.filter2D(gray, -1, k)
        out.append(np.abs(r))
    out.append(cv2.GaussianBlur(gray, (5, 5), 1.0))  # circular
    out.append(np.abs(cv2.Laplacian(g8, cv2.CV_32F, ksize=5) / 255.0))  # circular
    out.append(np.abs(cv2.Sobel(g8, cv2.CV_32F, 1, 0, ksize=3) / 255.0))
    out.append(np.abs(cv2.Sobel(g8, cv2.CV_32F, 0, 1, ksize=3) / 255.0))
    return out  # 8


def pyramid3(resp: np.ndarray) -> list:
    """1 mapa 512 -> 3 escalas (resizes p/ 512). Via Gauss + metade."""
    u8 = np.clip(resp * 255, 0, 255).astype(np.uint8).astype(np.float32) / 255.0
    l0 = resp
    l1 = cv2.pyrDown((u8 * 255).astype(np.uint8)).astype(np.float32) / 255.0
    l1 = cv2.resize(l1, (SIZE, SIZE))
    small = cv2.pyrDown((l1 * 255).astype(np.uint8)).astype(np.float32) / 255.0
    # small esta 256 -> reduz p/ 128 simulando 2a descida
    l2 = cv2.resize(cv2.pyrDown((small * 255).astype(np.uint8)), (SIZE, SIZE)).astype(np.float32) / 255.0
    return [l0, l1, l2]


def texture_maps(gray: np.ndarray) -> np.ndarray:
    """512x512 -> 512x512x24."""
    maps = []
    for r in base_responses(gray):
        maps.extend(pyramid3(r))
    return np.stack(maps, axis=-1).astype(np.float32)  # 24


def window_means(maps: np.ndarray, w: int = WIN) -> np.ndarray:
    """Media em janela de cada mapa -> 512x512x24. ponytail: O(H*W*24) via box blur, ok p/ 512."""
    return np.stack([cv2.blur(maps[:, :, i], (w, w)) for i in range(24)], axis=-1)


def load_gray(path: Path) -> np.ndarray:
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if g is None:
        raise FileNotFoundError(path)
    g = cv2.resize(g, (SIZE, SIZE))
    return g.astype(np.float32) / 255.0


def image_vector(path: Path) -> np.ndarray:
    """1 vetor 24D por imagem = media global das medias em janela."""
    f = window_means(texture_maps(load_gray(path)))
    return f.reshape(-1, 24).mean(axis=0)


def classify_folder(datadir: Path, k: int):
    paths = sorted([p for p in datadir.rglob("*.jpg")] + [p for p in datadir.rglob("*.png")])
    assert len(paths) >= 32, f"esperado >=32 imagens, achei {len(paths)} em {datadir}"
    X = np.stack([image_vector(p) for p in paths])
    Xs = StandardScaler().fit_transform(X)
    lab = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(Xs)
    for p, l in zip(paths, lab):
        print(f"{l}  {p.relative_to(datadir)}")
    return paths, lab


def segment_image(path: Path, k: int, stride: int, out: Path):
    gray = load_gray(path)
    f = window_means(texture_maps(gray))
    h, w, _ = f.shape
    ys, xs = np.mgrid[0:h:stride, 0:w:stride]
    samp = f[ys, xs].reshape(-1, 24)
    Xs = StandardScaler().fit_transform(samp)
    lab = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(Xs)
    small = lab.reshape(ys.shape)
    seg = cv2.resize(small.astype(np.uint8) * (255 // max(k - 1, 1)), (SIZE, SIZE),
                     interpolation=cv2.INTER_NEAREST)
    color = cv2.applyColorMap(seg, cv2.COLORMAP_JET)
    orig = (gray * 255).astype(np.uint8)
    vis = np.hstack([cv2.cvtColor(orig, cv2.COLOR_GRAY2BGR), color])
    cv2.imwrite(str(out), vis)
    print(f"ok {path} -> {out} (K={k})")


def fit_groups(datadir: Path, k: int):
    """Agrupa data/ e devolve (scaler, kmeans, rotulo_de_cada_grupo)."""
    paths = sorted([p for p in datadir.rglob("*.jpg")] + [p for p in datadir.rglob("*.png")])
    assert len(paths) >= 2, f"sem imagens em {datadir}"
    X = np.stack([image_vector(p) for p in paths])
    scaler = StandardScaler().fit(X)
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(scaler.transform(X))
    # nome do grupo = classe majoritaria nele
    names = {}
    for c in range(k):
        cls = [paths[i].parent.name for i in range(len(paths)) if km.labels_[i] == c]
        names[c] = max(set(cls), key=cls.count) if cls else f"grupo{c}"
    return scaler, km, names


def predict_image(img: Path, datadir: Path, k: int):
    """Diz o que a imagem eh: grupo mais proximo (euclidiano) + distancias."""
    scaler, km, names = fit_groups(datadir, k)
    v = scaler.transform(image_vector(img).reshape(1, -1))
    d = np.linalg.norm(km.cluster_centers_ - v, axis=1)
    c = int(np.argmin(d))
    print(f"imagem: {img}\neh o que: {names[c]} (grupo {c})")
    for i in np.argsort(d):
        print(f"  dist {d[i]:.2f}  {names[int(i)]} (grupo {int(i)})")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("classify")
    c.add_argument("--data", default="data")
    c.add_argument("--k", type=int, default=4)
    s = sub.add_parser("segment")
    s.add_argument("img")
    s.add_argument("--k", type=int, default=3)
    s.add_argument("--stride", type=int, default=4)
    s.add_argument("--out", default="seg.png")
    p = sub.add_parser("predict")
    p.add_argument("img")
    p.add_argument("--data", default="data")
    p.add_argument("--k", type=int, default=9)
    a = ap.parse_args()
    if a.cmd == "classify":
        classify_folder(Path(a.data), a.k)
    elif a.cmd == "predict":
        predict_image(Path(a.img), Path(a.data), a.k)
    else:
        segment_image(Path(a.img), a.k, a.stride, Path(a.out))


if __name__ == "__main__":
    main()
