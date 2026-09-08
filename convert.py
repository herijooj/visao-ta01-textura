#!/usr/bin/env python3
"""Converte fotos brutas em 512x512 cinza.
Uso: python3 convert.py --input raw --output data
Espera: raw/<classe>/*.jpg (4 pastas x 8 fotos). Gera data/<classe>/*.jpg.
"""
import argparse
from pathlib import Path
from PIL import Image

SIZE = 512
EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

def process_one(src: Path, dst: Path):
    img = Image.open(src).convert("L")  # RGB -> cinza
    w, h = img.size
    side = min(w, h)
    left, top = (w - side) // 2, (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    if side != SIZE:
        img = img.resize((SIZE, SIZE), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "JPEG", quality=95)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="raw")
    ap.add_argument("--output", default="data")
    a = ap.parse_args()
    inp, out = Path(a.input), Path(a.output)
    files = [p for p in inp.rglob("*") if p.suffix.lower() in EXTS and p.is_file()]
    if not files:
        print(f"nenhuma imagem em {inp}/ (esperado {inp}/<classe>/*.jpg)")
        return
    for src in sorted(files):
        cls = src.parent.name
        dst = out / cls / (src.stem + ".jpg")
        process_one(src, dst)
        print(f"ok {src} -> {dst}")
    # verificação
    print("\n--- conferência ---")
    total = 0
    for clsdir in sorted([d for d in out.iterdir() if d.is_dir()]):
        n = len(list(clsdir.glob("*.jpg")))
        total += n
        print(f"{clsdir.name}: {n} imagens")
    print(f"total: {total} (mínimo 32)")
    if total < 32:
        print("AVISO: faltam imagens (mínimo 32)!")

if __name__ == "__main__":
    main()
