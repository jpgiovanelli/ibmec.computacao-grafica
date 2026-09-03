# 00 — Quadro comparativo das quatro áreas

Gera os dois diagramas usados na introdução do [relatório](../README.md): o mapa de
fluxos (entrada → processo → saída de cada área) e o mapa de quadrantes.

```bash
python diagrama_areas.py
```

**Saídas:** `../saidas/00_comparativo/01_fluxos_das_areas.png` e `02_quadrantes.png`.

O ponto do segundo diagrama é o quadrante vazio: quando a entrada e a saída são ambas
dados/modelo, não há imagem envolvida — é modelagem, simulação ou análise numérica, e
está fora da Computação Visual. As Áreas 1 e 4 ocupam o **mesmo** quadrante
(dados/modelo → imagem) e se distinguem pela intenção, não pelo fluxo.
