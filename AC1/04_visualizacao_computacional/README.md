# Área 4 — Visualização Computacional

> **DADOS → IMAGEM.** A entrada não tinha forma visual nenhuma: é uma matriz de
> temperaturas, um campo de velocidades, um volume de densidades. Compartilha as
> ferramentas da Área 1, mas o critério de sucesso é oposto — fidelidade ao dado, não
> realismo.

## Aplicação de referência

[**Matplotlib**](https://github.com/matplotlib/matplotlib) (BSD) e
[**scikit-image**](https://github.com/scikit-image/scikit-image) para o *marching cubes*,
seguindo o pipeline canônico do [**VTK/ParaView**](https://github.com/Kitware/VTK):
`source → filter → mapper → actor`.

```bash
python visualizacao.py     # ~25 s
```

## Experimentos

| # | Fonte de dados | Técnicas de mapeamento |
|---|---|---|
| A | equação do calor 2D por diferenças finitas (180×180, 4000 iterações) | mapa de cor, isolinhas rotuladas, relevo sombreado, sonda de linha, série temporal |
| B | escoamento potencial ao redor de um cilindro com circulação (260×260) | glifos (quiver), linhas de corrente, campo derivado preenchido |
| C | volume escalar 90³ = 729.000 voxels | cortes axial/coronal/sagital, isosuperfícies por marching cubes, corte de revelação |
| D | o campo escalar de A | comparação de colormaps + curva de luminosidade percebida |

## Resultados

- Temperatura média final: 50,97 °C (série completa em `serie_temperatura_media.csv`)
- Isosuperfícies extraídas: 32.984 / 9.916 / 536 triângulos nos níveis 0,30 / 0,62 / 0,95
- Os níveis não são arbitrários: saem dos picos do histograma do volume
- `jet` e `coolwarm` **não** têm luminosidade monótona — criam faixas que não existem no
  dado; `viridis` e `inferno` têm

O marching cubes é o ponto de contato mais direto entre esta área e a Área 1: a
visualização **produz geometria** e entrega para um renderizador desenhar.
