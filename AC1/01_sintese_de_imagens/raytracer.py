"""
=============================================================================
 AREA 1 - SINTESE DE IMAGENS (Computacao Grafica)
 Aplicacao: Path Tracer (Ray Tracing estocastico) - porte didatico em NumPy
 Referencia: "Ray Tracing in One Weekend", Peter Shirley et al.
             https://github.com/RayTracing/raytracing.github.io  (CC0)
=============================================================================

O QUE ESTE CODIGO DEMONSTRA (aspectos especificos da SINTESE DE IMAGENS):

  MODELO 3D  ---->  [ pipeline de sintese ]  ---->  IMAGEM (matriz de pixels)

  1. Modelagem geometrica implicita (esferas definidas por equacao quadratica)
  2. Modelo de camera (pinhole + lente fina => profundidade de campo)
  3. Tracado de raios primarios: 1 raio por amostra de pixel
  4. Intersecao raio-objeto resolvida analiticamente (formula de Bhaskara)
  5. Modelos de material / BRDF:
        - Lambertiano  (difuso)
        - Metal        (reflexao especular + rugosidade)
        - Dieletrico   (refracao pela Lei de Snell + reflectancia de Schlick)
  6. Iluminacao global por Monte Carlo (a luz "quica" ate `max_depth` vezes;
     e o que produz sombras suaves, cor sangrada e caustica)
  7. Antialiasing por supersampling estocastico (jitter dentro do pixel)
  8. Correcao gama (linear -> sRGB) antes de gravar o arquivo

Implementacao VETORIZADA: todos os raios da imagem sao processados de uma vez
em arrays NumPy (N,3), o que torna o Python viavel para esta tarefa.

USO:
    python raytracer.py                        # padrao 480x270, 48 amostras
    python raytracer.py --largura 800 --spp 96 # mais qualidade (mais lento)
"""

import argparse
import os
import time

import numpy as np

# ---------------------------------------------------------------------------
# Utilitarios de algebra vetorial (arrays de shape (N,3))
# ---------------------------------------------------------------------------


def normalizar(v):
    """Normaliza cada vetor-linha do array (N,3)."""
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def produto_escalar(a, b):
    """Produto escalar linha a linha -> (N,1)."""
    return np.sum(a * b, axis=-1, keepdims=True)


def refletir(v, n):
    """Reflexao especular: r = v - 2(v.n)n  (v e n unitarios)."""
    return v - 2.0 * produto_escalar(v, n) * n


def refratar(v, n, eta_razao):
    """Refracao pela Lei de Snell (vetorial). v e n unitarios."""
    cos_theta = np.minimum(produto_escalar(-v, n), 1.0)
    r_perp = eta_razao * (v + cos_theta * n)
    k = 1.0 - np.sum(r_perp * r_perp, axis=-1, keepdims=True)
    k = np.maximum(k, 0.0)
    r_paral = -np.sqrt(k) * n
    return r_perp + r_paral


def schlick(cosseno, indice_ref):
    """Aproximacao de Schlick para a reflectancia de Fresnel."""
    r0 = ((1.0 - indice_ref) / (1.0 + indice_ref)) ** 2
    return r0 + (1.0 - r0) * (1.0 - cosseno) ** 5


def direcoes_aleatorias_esfera(n, rng):
    """Amostra n direcoes uniformes na esfera unitaria (para o BRDF difuso)."""
    z = rng.uniform(-1.0, 1.0, size=(n, 1))
    ang = rng.uniform(0.0, 2.0 * np.pi, size=(n, 1))
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    return np.concatenate([r * np.cos(ang), r * np.sin(ang), z], axis=1)


# ---------------------------------------------------------------------------
# Materiais (identificadores inteiros para permitir processamento vetorizado)
# ---------------------------------------------------------------------------
LAMBERTIANO = 0
METAL = 1
DIELETRICO = 2

# ---------------------------------------------------------------------------
# Cena: esferas descritas por centro, raio e material
# ---------------------------------------------------------------------------


def montar_cena():
    """Monta a cena classica: 3 esferas sobre um 'chao' (esfera gigante)."""
    centros = [
        (0.0, -1000.5, -1.0),  # chao
        (0.0, 0.0, -1.0),      # esfera central, difusa
        (-1.05, 0.0, -1.0),    # esfera de vidro
        (-1.05, 0.0, -1.0),    # casca interna do vidro (raio negativo)
        (1.05, 0.0, -1.0),     # esfera de metal polido
        (0.0, 0.35, -2.6),     # esfera de metal rugoso ao fundo
        (-0.42, -0.32, -0.35),  # esferinha difusa em primeiro plano
    ]
    raios = [1000.0, 0.5, 0.5, -0.45, 0.5, 0.85, 0.18]
    materiais = [LAMBERTIANO, LAMBERTIANO, DIELETRICO, DIELETRICO,
                 METAL, METAL, LAMBERTIANO]
    albedos = [
        (0.55, 0.55, 0.58),
        (0.85, 0.25, 0.22),
        (1.00, 1.00, 1.00),
        (1.00, 1.00, 1.00),
        (0.92, 0.90, 0.85),
        (0.30, 0.45, 0.85),
        (0.95, 0.78, 0.20),
    ]
    parametros = [0.0, 0.0, 1.5, 1.5, 0.02, 0.35, 0.0]  # fuzz (metal) ou IOR

    return {
        "centros": np.array(centros, dtype=np.float64),
        "raios": np.array(raios, dtype=np.float64),
        "materiais": np.array(materiais, dtype=np.int32),
        "albedos": np.array(albedos, dtype=np.float64),
        "parametros": np.array(parametros, dtype=np.float64),
    }


def interseccao_mais_proxima(origem, direcao, cena, t_min=1e-3, t_max=1e9):
    """
    Testa TODOS os raios contra TODAS as esferas e devolve o hit mais proximo.

    Intersecao raio-esfera: |o + t*d - c|^2 = r^2  =>  equacao do 2o grau
        a = d.d ;  b = 2 d.(o-c) ;  c = (o-c).(o-c) - r^2
    Usamos a forma reduzida (meio_b) para reduzir operacoes.
    """
    n_raios = origem.shape[0]
    melhor_t = np.full((n_raios,), t_max)
    melhor_id = np.full((n_raios,), -1, dtype=np.int32)

    for i in range(cena["centros"].shape[0]):
        oc = origem - cena["centros"][i]
        a = produto_escalar(direcao, direcao)[:, 0]
        meio_b = produto_escalar(oc, direcao)[:, 0]
        c = produto_escalar(oc, oc)[:, 0] - cena["raios"][i] ** 2
        discriminante = meio_b * meio_b - a * c

        valido = discriminante > 0.0
        if not np.any(valido):
            continue

        raiz = np.sqrt(np.where(valido, discriminante, 0.0))
        t1 = (-meio_b - raiz) / a
        t2 = (-meio_b + raiz) / a
        t = np.where((t1 > t_min) & (t1 < melhor_t), t1,
                     np.where((t2 > t_min) & (t2 < melhor_t), t2, np.inf))

        atualiza = valido & (t > t_min) & (t < melhor_t)
        melhor_t = np.where(atualiza, t, melhor_t)
        melhor_id = np.where(atualiza, i, melhor_id)

    return melhor_t, melhor_id


def cor_do_ceu(direcao):
    """Ceu procedural: interpolacao linear (lerp) entre branco e azul."""
    t = 0.5 * (normalizar(direcao)[:, 1:2] + 1.0)
    branco = np.array([1.0, 1.0, 1.0])
    azul = np.array([0.5, 0.7, 1.0])
    return (1.0 - t) * branco + t * azul


def tracar(origem, direcao, cena, max_prof, rng):
    """
    Laco iterativo de path tracing (equivalente a recursao, porem vetorizado).

    `throughput` acumula o produto dos BRDFs; quando o raio escapa da cena,
    multiplicamos pela radiancia do ceu e somamos ao acumulador de cor.
    """
    n = origem.shape[0]
    cor = np.zeros((n, 3))
    throughput = np.ones((n, 3))
    ativos = np.ones((n,), dtype=bool)

    for _ in range(max_prof):
        if not np.any(ativos):
            break

        o = origem[ativos]
        d = normalizar(direcao[ativos])
        t, ids = interseccao_mais_proxima(o, d, cena)

        escapou = ids < 0
        idx_global = np.flatnonzero(ativos)

        # --- raios que nao acertaram nada: recebem a cor do ceu -------------
        if np.any(escapou):
            gi = idx_global[escapou]
            cor[gi] += throughput[gi] * cor_do_ceu(d[escapou])
            ativos[gi] = False

        acertou = ~escapou
        if not np.any(acertou):
            break

        gi = idx_global[acertou]
        oh, dh, th, idh = o[acertou], d[acertou], t[acertou], ids[acertou]

        ponto = oh + th[:, None] * dh
        normal = normalizar(ponto - cena["centros"][idh])
        # Normais de raio negativo (casca interna) ja apontam para dentro:
        normal *= np.sign(cena["raios"][idh])[:, None]

        frente = produto_escalar(dh, normal)[:, 0] < 0.0
        normal_face = np.where(frente[:, None], normal, -normal)

        mat = cena["materiais"][idh]
        albedo = cena["albedos"][idh]
        param = cena["parametros"][idh]

        nova_dir = np.zeros_like(dh)
        atenuacao = np.ones_like(albedo)

        # ---------------- material LAMBERTIANO (difuso) --------------------
        m = mat == LAMBERTIANO
        if np.any(m):
            alvo = normal_face[m] + direcoes_aleatorias_esfera(int(m.sum()), rng)
            # evita direcao degenerada (quase nula)
            degenerado = np.linalg.norm(alvo, axis=1) < 1e-8
            alvo[degenerado] = normal_face[m][degenerado]
            nova_dir[m] = normalizar(alvo)
            atenuacao[m] = albedo[m]

        # ---------------- material METAL (especular + fuzz) ----------------
        m = mat == METAL
        if np.any(m):
            r = refletir(dh[m], normal_face[m])
            fuzz = param[m][:, None]
            r = r + fuzz * direcoes_aleatorias_esfera(int(m.sum()), rng)
            nova_dir[m] = normalizar(r)
            atenuacao[m] = albedo[m]
            # raio que "afunda" na superficie e absorvido
            abaixo = produto_escalar(nova_dir[m], normal_face[m])[:, 0] <= 0
            if np.any(abaixo):
                aten_m = atenuacao[m]
                aten_m[abaixo] = 0.0
                atenuacao[m] = aten_m

        # ---------------- material DIELETRICO (vidro) ----------------------
        m = mat == DIELETRICO
        if np.any(m):
            ior = param[m]
            razao = np.where(frente[m], 1.0 / ior, ior)[:, None]
            v = dh[m]
            nf = normal_face[m]
            cos_theta = np.minimum(produto_escalar(-v, nf), 1.0)
            sin_theta = np.sqrt(np.maximum(0.0, 1.0 - cos_theta ** 2))

            nao_refrata = (razao * sin_theta) > 1.0            # reflexao total
            prob = schlick(cos_theta, razao)                   # Fresnel
            sorteio = rng.random((int(m.sum()), 1))
            usar_reflexao = nao_refrata | (prob > sorteio)

            dir_refl = refletir(v, nf)
            dir_refr = refratar(v, nf, razao)
            nova_dir[m] = normalizar(np.where(usar_reflexao, dir_refl, dir_refr))
            atenuacao[m] = 1.0  # vidro ideal nao absorve

        throughput[gi] *= atenuacao
        origem[gi] = ponto + 1e-4 * normal_face
        direcao[gi] = nova_dir

        # --- Roleta russa: encerra caminhos de contribuicao desprezivel ----
        fraco = throughput[gi].max(axis=1) < 1e-3
        if np.any(fraco):
            ativos[gi[fraco]] = False

    return cor


# ---------------------------------------------------------------------------
# Camera (modelo pinhole com lente fina para profundidade de campo)
# ---------------------------------------------------------------------------


class Camera:
    def __init__(self, origem, alvo, cima, vfov_graus, aspecto, abertura, foco):
        theta = np.radians(vfov_graus)
        h = np.tan(theta / 2.0)
        altura_vp = 2.0 * h
        largura_vp = aspecto * altura_vp

        self.w = normalizar(np.array([origem - alvo]))[0]
        self.u = normalizar(np.array([np.cross(cima, self.w)]))[0]
        self.v = np.cross(self.w, self.u)

        self.origem = np.array(origem, dtype=np.float64)
        self.horizontal = foco * largura_vp * self.u
        self.vertical = foco * altura_vp * self.v
        self.canto = (self.origem - self.horizontal / 2.0
                      - self.vertical / 2.0 - foco * self.w)
        self.raio_lente = abertura / 2.0

    def gerar_raios(self, s, t, rng):
        """s,t em [0,1] -> origem e direcao de cada raio primario."""
        n = s.shape[0]
        if self.raio_lente > 0.0:
            ang = rng.uniform(0, 2 * np.pi, (n, 1))
            r = self.raio_lente * np.sqrt(rng.random((n, 1)))
            desloc = r * (np.cos(ang) * self.u + np.sin(ang) * self.v)
        else:
            desloc = np.zeros((n, 3))
        origem = self.origem + desloc
        destino = (self.canto + s[:, None] * self.horizontal
                   + t[:, None] * self.vertical)
        return origem, destino - origem


# ---------------------------------------------------------------------------
# Renderizacao
# ---------------------------------------------------------------------------


def renderizar(largura, altura, spp, max_prof, semente=42):
    rng = np.random.default_rng(semente)
    cena = montar_cena()

    camera = Camera(
        origem=np.array([0.0, 0.55, 2.2]),
        alvo=np.array([0.0, 0.0, -1.0]),
        cima=np.array([0.0, 1.0, 0.0]),
        vfov_graus=42.0,
        aspecto=largura / altura,
        abertura=0.06,   # > 0 ativa a profundidade de campo
        foco=3.2,
    )

    yy, xx = np.meshgrid(np.arange(altura), np.arange(largura), indexing="ij")
    px = xx.reshape(-1).astype(np.float64)
    py = (altura - 1 - yy).reshape(-1).astype(np.float64)

    acumulado = np.zeros((largura * altura, 3))
    t0 = time.time()
    for amostra in range(spp):
        # jitter sub-pixel => antialiasing por supersampling estocastico
        s = (px + rng.random(px.shape)) / (largura - 1)
        t = (py + rng.random(py.shape)) / (altura - 1)
        origem, direcao = camera.gerar_raios(s, t, rng)
        acumulado += tracar(origem, direcao, cena, max_prof, rng)

        if (amostra + 1) % max(1, spp // 8) == 0:
            pct = 100.0 * (amostra + 1) / spp
            print(f"    amostra {amostra + 1:3d}/{spp}  ({pct:5.1f}%)"
                  f"  {time.time() - t0:6.1f}s", flush=True)

    cor = acumulado / spp
    cor = np.sqrt(np.clip(cor, 0.0, 1.0))          # correcao gama (gama 2.0)
    return (cor.reshape(altura, largura, 3) * 255).astype(np.uint8)


def main():
    ap = argparse.ArgumentParser(description="Path tracer didatico (AC01 - CG)")
    ap.add_argument("--largura", type=int, default=480)
    ap.add_argument("--spp", type=int, default=48, help="amostras por pixel")
    ap.add_argument("--profundidade", type=int, default=8, help="quiques maximos")
    ap.add_argument("--saida", type=str, default=None)
    args = ap.parse_args()

    largura = args.largura
    altura = int(round(largura * 9 / 16))

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    destino = args.saida or os.path.join(raiz, "saidas", "01_sintese",
                                         "raytracer_cena.png")
    os.makedirs(os.path.dirname(destino), exist_ok=True)

    print("=" * 70)
    print(" AREA 1 - SINTESE DE IMAGENS | Path Tracer (Monte Carlo)")
    print("=" * 70)
    print(f"  Resolucao ......: {largura}x{altura}")
    print(f"  Amostras/pixel .: {args.spp}")
    print(f"  Profundidade ...: {args.profundidade} quiques")
    print(f"  Raios primarios : {largura * altura * args.spp:,}")
    print("-" * 70)

    t0 = time.time()
    img = renderizar(largura, altura, args.spp, args.profundidade)
    dt = time.time() - t0

    from PIL import Image
    Image.fromarray(img).save(destino)

    print("-" * 70)
    print(f"  Tempo total ....: {dt:.1f}s")
    print(f"  Imagem salva em : {destino}")
    print("=" * 70)


if __name__ == "__main__":
    main()
