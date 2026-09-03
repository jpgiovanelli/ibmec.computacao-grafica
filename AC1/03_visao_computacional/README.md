# Área 3 — Visão Computacional

> **IMAGEM → DADOS.** É a área inversa da Área 1, e um problema mal posto: infinitas
> cenas 3D projetam a mesma imagem. As saídas principais aqui são `.json` e `.csv`;
> as figuras servem só para conferência humana.

## Aplicação de referência

[**OpenCV**](https://github.com/opencv/opencv) (Apache 2.0), usando três recursos do
repositório público: classificadores Haar pré-treinados, watershed e ORB.

```bash
python visao.py     # ~15 s
```

## Experimentos

### 1. Detecção — Viola-Jones (Haar + AdaBoost + cascata)

Características Haar-like calculadas em tempo constante pela imagem integral,
selecionadas por AdaBoost e organizadas em cascata (os estágios iniciais descartam
rapidamente quase todas as janelas). Busca multiescala com `scaleFactor=1.08`;
os olhos são procurados **dentro** da região da face.

Resultado: 1 face em (176, 65, 97×97), score 6,35, com 2 olhos → `deteccoes_faces.json`.

### 2. Segmentação e mensuração — watershed

Correção de iluminação → Otsu → morfologia → transformada de distância → marcadores →
watershed → descritores de região.

| Métrica | Valor |
|---|---:|
| Objetos contados | **24** (gabarito: 24) |
| Diâmetro médio | 42,8 px |
| Circularidade média | 0,88 |

Sem a correção de iluminação (abertura morfológica com elemento maior que as moedas), a
contagem cai para 21 — **a Área 2 é pré-requisito da Área 3**. Saída: `medicoes_objetos.csv`.

### 3. Casamento de características — ORB + RANSAC

A cena de busca é a mesma imagem rotacionada 32°, escalada para 70% e com brilho alterado.

| Métrica | Valor |
|---|---:|
| Pontos-chave (imagem / cena) | 1500 / 1500 |
| Casamentos após o teste de Lowe (0,75) | 659 |
| *Inliers* após RANSAC (4,0 px) | **647 (98,2%)** |

A homografia estimada projeta a moldura do objeto na cena — localização geométrica, não
só reconhecimento. Saída: `casamento_orb.json`.
