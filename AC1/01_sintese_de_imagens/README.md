# Área 1 — Síntese de Imagens (Computação Gráfica)

> **MODELO 3D → IMAGEM.** A imagem é produzida a partir de uma descrição numérica da
> cena. É o problema direto, e o limite da qualidade é o orçamento computacional.

## Aplicação de referência

[**Ray Tracing in One Weekend**](https://github.com/RayTracing/raytracing.github.io)
(Shirley, Black & Hollasch — CC0), portado aqui para NumPy vetorizado, mais um
rasterizador por software que reproduz o pipeline do OpenGL usado na disciplina.

## Scripts

| Script | O que faz | Tempo |
|---|---|---|
| `raytracer.py` | path tracer Monte Carlo: BRDFs lambertiano/metal/dielétrico, iluminação global, profundidade de campo, antialiasing, correção gama | ~43 s (480×270, 128 spp) |
| `rasterizador.py` | pipeline modelo → visão → projeção → viewport, back-face culling, Z-buffer, wireframe/flat/Gouraud | ~5 s |
| `convergencia_amostras.py` | mesma cena com 1, 4, 16 e 64 amostras/pixel, com RMSE | ~12 s |

```bash
python raytracer.py                        # padrão
python raytracer.py --largura 800 --spp 200 --profundidade 12
python rasterizador.py
python convergencia_amostras.py
```

## Aspectos da área que aparecem no código

- **Interseção raio-esfera** resolvida analiticamente (equação do 2º grau, forma reduzida) — `interseccao_mais_proxima()`
- **Modelo de câmera** pinhole + lente fina (abertura > 0 gera profundidade de campo) — classe `Camera`
- **BRDFs**: difuso (amostragem na esfera unitária), metálico (reflexão + fuzz), dielétrico (Lei de Snell + Fresnel/Schlick + reflexão total interna)
- **Equação de renderização** resolvida por Monte Carlo, com roleta russa para encerrar caminhos de contribuição desprezível
- **Matrizes homogêneas 4×4** e divisão perspectiva — `look_at()`, `perspectiva()`
- **Coordenadas baricêntricas** para interpolar cor e profundidade dentro do triângulo
- **Z-buffer** como algoritmo de visibilidade em espaço de imagem

## Resultados obtidos

- 16,6 milhões de raios primários em 43,3 s (1 núcleo de CPU, NumPy)
- Erro cai com **O(1/√N)**: RMSE 29,4 → 11,5 → 4,8 ao passar de 1 → 4 → 16 amostras/pixel
- Sombras suaves, reflexos mútuos, refração e cor sangrada **emergem** do transporte de
  luz simulado; nenhum deles foi programado como efeito
