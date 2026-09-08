#!/usr/bin/env bash
# Demo completa TA01 em 1 comando: ./run.sh
# Precisa: nix-shell — ou python3 -m venv .venv && pip install -r requirements.txt
set -e
cd "$(dirname "$0")"

K=$(ls -d data/*/ | wc -l)
echo "== classes em data/: $K"

if [ -d raw ] && [ "$(find raw -type f | wc -l)" -ge 32 ]; then
  echo "== convert raw -> data"
  python convert.py --input raw --output data | tail -12
fi

echo "== classify (K=$K)"
python src/textura.py classify --data data --k "$K"

echo "== mosaico (9 classes, 3x3) + segment"
python - <<'EOF'
import cv2, numpy as np
from pathlib import Path
cls = sorted(c for c in Path('data').iterdir() if c.is_dir())
ims = [cv2.resize(cv2.imread(str(sorted(c.glob('*.jpg'))[0]), 0), (170, 170)) for c in cls]
rows = [np.hstack(ims[i:i+3]) for i in range(0, 9, 3)]
cv2.imwrite('mosaico.png', np.vstack(rows))
print('mosaico.png ok', [c.name for c in cls])
EOF
python src/textura.py segment mosaico.png --k 9 --stride 4 --out seg.png

echo "== predict (1a imagem da 1a classe)"
python src/textura.py predict "$(ls data/*/*.jpg | head -1)" --data data --k "$K" | head -4
echo "== fim: ver seg.png, mosaico.png e figs/out_etapas_*/etapas.png"
