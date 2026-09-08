# TA01 — Segmentação por textura (só clássicos, sem IA)

Banco de 8 filtros em 1 escala + pirâmide gaussiana (3 escalas) = 24 mapas.
Vetor = média em janela de cada mapa → **24D**. Agrupo = KMeans euclidiano.

- 1–4: Gabor 0°, 45°, 90°, 135° · 5: Gauss 5×5 (circular) · 6: Laplaciano (circular) · 7–8: Sobel X/Y
- Escalas: 512 → 256 → 128 via `GaussianBlur + pyrDown`

## Rodar (1 comando)

```bash
nix develop        # ou nix-shell; ou pip install -r requirements.txt
./run.sh
```

Isso faz: `convert` raw→data, `classify`, mosaico + `segment`, `predict` demo.
Gera `seg.png`, `mosaico.png`. Etapas detalhadas por classe:

```bash
python src/etapas.py data/Papel/IMG_*.jpg --out figs/out_etapas_Papel --k 3
```

Comandos avulsos:

```bash
python src/textura.py classify --data data --k 9
python src/textura.py segment <img> --k 3 --out seg.png
python src/textura.py predict <foto_nova> --data data --k 9
```

## Estrutura

```
raw/    originais 9 classes × 4 (fora do git, 654MB)
data/   36 imagens 512×512 cinza (gerado por convert.py)
src/    textura.py (classify/segment/predict) · etapas.py (debug visual)
figs/   out_etapas_<classe>/etapas.png (13 PNGs cada)
run.sh  demo ponta a ponta · relatorio.md  rascunho do artigo
```

## Relatório

Ver `relatorio.md`. Link do git da tarefa: <https://github.com/herijooj/visao-ta01-textura>
