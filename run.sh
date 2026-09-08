#!/usr/bin/env bash
# Demo completa TA01 em 1 comando: ./run.sh
# Precisa: nix develop (ou nix-shell) — ou pip install -r requirements.txt
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

echo "== mosaico 512 (4 classes) + segment"
python - <<'EOF'
import cv2, numpy as np
from pathlib import Path
ims = [cv2.imread(str(sorted(c.glob('*.jpg'))[0]), 0)
     for c in sorted(Path('data').iterdir()) if c.is_dir()][:4]
q = 256
top = np.hstack([cv2.resize(i, (q, q)) for i in ims[:2]])
bot = np.hstack([cv2.resize(i, (q, q)) for i in ims[2:4]])
cv2.imwrite('mosaico.png', np.vstack([top, bot]))
print('mosaico.png ok')
EOF
python src/textura.py segment mosaico.png --k 4 --stride 4 --out seg.png

echo "== predict (1a imagem da 1a classe)"
python src/textura.py predict "$(ls data/*/*.jpg | head -1)" --data data --k "$K" | head -4
echo "== fim: ver seg.png, mosaico.png e figs/out_etapas_*/etapas.png"
