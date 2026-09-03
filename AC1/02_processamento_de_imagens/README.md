# Área 2 — Processamento Digital de Imagens

> **IMAGEM → IMAGEM.** O operador trata a imagem como sinal. Nada é interpretado: o
> programa nunca produz a palavra "moeda".

## Aplicação de referência

[**OpenCV**](https://github.com/opencv/opencv) (Apache 2.0) e
[**scikit-image**](https://github.com/scikit-image/scikit-image) (BSD-3).
Entrada: `skimage.data.coins` (303×384, 256 níveis de cinza), que acompanha a biblioteca.

```bash
python processamento.py     # ~10 s
```

## Etapas executadas

1. **Operações pontuais** — negativo, subexposição, correção gama, contraste linear
2. **Histograma** — alargamento, equalização global e CLAHE (adaptativa, com limite de contraste)
3. **Filtragem espacial** — média, gaussiano, mediana, realce de nitidez, com PSNR/SSIM
4. **Domínio da frequência** — FFT 2D, espectro de magnitude, Butterworth passa-baixa e passa-alta
5. **Bordas** — Sobel X/Y, magnitude do gradiente, Laplaciano, Canny
6. **Limiarização e morfologia** — Otsu, erosão, dilatação, abertura, fechamento, gradiente morfológico

## Resultado-chave

Contra ruído impulsivo (sal e pimenta, 6%):

| Filtro | PSNR | SSIM |
|---|---:|---:|
| imagem ruidosa | 17,38 dB | — |
| média 5×5 (linear) | 23,21 dB | 0,569 |
| **mediana 5×5 (não-linear)** | **26,27 dB** | **0,773** |

A média dilui o pixel corrompido entre os vizinhos e borra a borda junto; a mediana é
uma estatística de ordem e simplesmente descarta o valor extremo. Limiar de Otsu
escolhido automaticamente: **T = 107**.

**Saídas:** seis painéis PNG + `metricas_processamento.json` em `../saidas/02_processamento/`.
