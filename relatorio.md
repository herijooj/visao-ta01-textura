# Relatório TA01 — Segmentação por textura (rascunho em formato artigo)

> Link do código: <https://github.com/herijooj/visao-ta01-textura>

## 1. Introdução
Tipo escolhido: texturas domésticas/equipamentos — alumínio, arroz, aveia,
batata-palha, couro, granola, madeira, papel, toalha (9 classes × 4 fotos = 36).
Por quê: grãos e tramas bem distintos entre classes, fáceis de fotografar em casa,
cada um excita um subconjunto diferente do banco de filtros.

## 2. Método (só clássicos, sem IA)
**Filtros (8 em 1 escala):** 4 Gabor orientados (0/45/90/135 graus, k=21, sigma=4, lambda=10),
Gauss 5x5 (circular), Laplaciano k=5 (circular), Sobel X/Y. Resposta em módulo.
**3 escalas:** pirâmide — Gauss + `pyrDown` à metade por nível (512 para 256 para 128),
resize p/ 512 (2ª opção do enunciado). 8×3 = 24 mapas.
**Vetor 24D:** média em janela 31×31 (`blur`) de cada mapa, cf. slides.
1 vetor/imagem = média global (classificação); 1 vetor/bloco p/ segmentação.
**Agrupamento:** z-score + KMeans, distância euclidiana (Lloyd).
`classify` K=9; `segment` K=3–4; `predict` = centroide mais próximo.

## 3. Dados
36 fotos próprias (`raw/`), crop quadrado central + resize 512×512 + RGB→cinza
(`convert.py` → `data/`). Ambiente reproduzível: `flake.nix`/`shell.nix`.

## 4. Resultados
- `classify --k 9`: 8 das 9 classes com 4/4 no mesmo grupo; madeira com 3/4
  (só `131641` cai com arroz). Achado: após recortar fundos de arroz/couro/papel,
  os centroides deslocaram e uma foto da madeira antes agrupada com alumínio
  voltou ao grupo da madeira (35/36, ~97%) — mostra que fundo estranho à textura
  contamina o vetor médio. A restante diverge no veio (orientação/escala),
  limitação esperada do Gabor sem invariância.
- `segment mosaico.png --k 9` → mosaico 3x3 com as 9 classes, mapa recupera
  os blocos (fig. `seg.png`; bordas sangram pelo efeito da janela 31).
- `predict`: foto de arroz → `Arroz` (dist 0.86 vs 4.30 da 2ª opção).
- Etapas por classe em `figs/out_etapas_*/etapas.png`.
- Limitações: rotação em texturas orientadas; borda da janela borra fronteiras.

## 5. Conclusão
24 médias + Euclides separam 8/9 texturas (35/36) e geram mapas por grupos. Suficiente p/ TA01.

## Referências
Slides Textura/Filtros/Clustering da disciplina; MacQueen/KMeans 1967;
OpenCV `getGaborKernel/pyrDown`.
