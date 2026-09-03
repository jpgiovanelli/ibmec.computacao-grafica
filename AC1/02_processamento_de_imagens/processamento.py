"""
=============================================================================
 AREA 2 - PROCESSAMENTO DIGITAL DE IMAGENS
 Aplicacao: OpenCV + scikit-image (bibliotecas open source)
   https://github.com/opencv/opencv          (Apache 2.0)
   https://github.com/scikit-image/scikit-image  (BSD-3)
=============================================================================

O QUE ESTE CODIGO DEMONSTRA (aspectos especificos do PROCESSAMENTO):

  IMAGEM  ---->  [ operador ]  ---->  IMAGEM

  A entrada E uma imagem e a saida TAMBEM E uma imagem. Nao existe modelo 3D
  (como na sintese) nem extracao de significado (como na visao). O objetivo e
  MELHORAR ou TRANSFORMAR o sinal: realce, restauracao, compressao, realce de
  bordas, remocao de ruido.

  Etapas executadas:
    1. Operacoes pontuais (dependem so do pixel):
         negativo, ajuste de brilho/contraste, correcao gama
    2. Analise e manipulacao de HISTOGRAMA:
         alargamento de contraste, equalizacao global, CLAHE (local)
    3. Filtragem ESPACIAL (convolucao com mascaras / vizinhanca):
         media, gaussiano, mediana (nao-linear), sharpening (nitidez)
    4. Filtragem no DOMINIO DA FREQUENCIA (Transformada de Fourier 2D):
         passa-baixa e passa-alta com filtro de Butterworth
    5. Realce de BORDAS: gradiente de Sobel, Laplaciano e Canny
    6. Segmentacao por LIMIARIZACAO (Otsu) e MORFOLOGIA MATEMATICA:
         erosao, dilatacao, abertura, fechamento
    7. Metricas objetivas de qualidade: PSNR e SSIM

USO:
    python processamento.py
"""

import json
import os

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from skimage import data  # noqa: E402
from skimage.metrics import peak_signal_noise_ratio, structural_similarity  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saidas", "02_processamento")
os.makedirs(SAIDA, exist_ok=True)

CINZA = "gray"


def salvar(fig, nome):
    caminho = os.path.join(SAIDA, nome)
    fig.savefig(caminho, dpi=110, facecolor="white")
    plt.close(fig)
    print(f"  [ok] {caminho}")
    return caminho


def painel(imagens, titulos, nome, sup, linhas=None, cmap=CINZA, tamanho=(13, 7)):
    n = len(imagens)
    linhas = linhas or (1 if n <= 4 else 2)
    colunas = int(np.ceil(n / linhas))
    fig, eixos = plt.subplots(linhas, colunas, figsize=tamanho,
                              constrained_layout=True)
    eixos = np.atleast_1d(eixos).ravel()
    for eixo, img, titulo in zip(eixos, imagens, titulos):
        if img.ndim == 3:
            eixo.imshow(img)
        else:
            eixo.imshow(img, cmap=cmap, vmin=0, vmax=255 if img.dtype == np.uint8 else None)
        eixo.set_title(titulo, fontsize=10)
        eixo.axis("off")
    for eixo in eixos[n:]:
        eixo.axis("off")
    fig.suptitle(sup, fontsize=13, fontweight="bold")
    return salvar(fig, nome)


# ---------------------------------------------------------------------------
# 1) Operacoes pontuais + histograma
# ---------------------------------------------------------------------------


def operacoes_pontuais(cinza):
    negativo = 255 - cinza
    escuro = np.clip(cinza * 0.45, 0, 255).astype(np.uint8)  # imagem subexposta
    gama = np.clip(((escuro / 255.0) ** 0.45) * 255, 0, 255).astype(np.uint8)
    contraste = cv2.convertScaleAbs(cinza, alpha=1.8, beta=-60)

    painel(
        [cinza, negativo, escuro, gama, contraste],
        ["Original", "Negativo  s = 255 - r",
         "Subexposta (r x 0,45)", "Correcao gama (y=0,45)\nsobre a subexposta",
         "Contraste linear\ns = 1,8r - 60"],
        "01_operacoes_pontuais.png",
        "Operacoes PONTUAIS: cada pixel de saida depende so do pixel de entrada",
        linhas=1, tamanho=(16, 3.8),
    )
    return escuro


def histogramas(cinza, escuro):
    equalizada = cv2.equalizeHist(escuro)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(escuro)

    fig, eixos = plt.subplots(2, 3, figsize=(13, 6.5), constrained_layout=True)
    trios = [(escuro, "Entrada (baixo contraste)"),
             (equalizada, "Equalizacao GLOBAL de histograma"),
             (clahe, "CLAHE (equalizacao LOCAL adaptativa)")]
    for col, (img, titulo) in enumerate(trios):
        eixos[0, col].imshow(img, cmap=CINZA, vmin=0, vmax=255)
        eixos[0, col].set_title(titulo, fontsize=10)
        eixos[0, col].axis("off")
        eixos[1, col].hist(img.ravel(), bins=256, range=(0, 255),
                           color="#2b6cb0", alpha=0.85)
        eixos[1, col].set_xlim(0, 255)
        eixos[1, col].set_xlabel("nivel de cinza")
        eixos[1, col].set_ylabel("frequencia" if col == 0 else "")
        eixos[1, col].grid(alpha=0.25)
    fig.suptitle("Analise e manipulacao de HISTOGRAMA (realce de contraste)",
                 fontsize=13, fontweight="bold")
    salvar(fig, "02_histograma_equalizacao.png")
    return clahe


# ---------------------------------------------------------------------------
# 2) Filtragem espacial e ruido
# ---------------------------------------------------------------------------


def adicionar_ruido_sal_pimenta(img, prob=0.06, rng=None):
    rng = rng or np.random.default_rng(7)
    saida = img.copy()
    r = rng.random(img.shape[:2])
    saida[r < prob / 2] = 0
    saida[r > 1 - prob / 2] = 255
    return saida


def adicionar_ruido_gaussiano(img, sigma=22, rng=None):
    rng = rng or np.random.default_rng(7)
    ruido = rng.normal(0, sigma, img.shape)
    return np.clip(img.astype(np.float64) + ruido, 0, 255).astype(np.uint8)


def filtragem_espacial(cinza):
    sal_pimenta = adicionar_ruido_sal_pimenta(cinza)
    gaussiano = adicionar_ruido_gaussiano(cinza)

    media_sp = cv2.blur(sal_pimenta, (5, 5))
    mediana_sp = cv2.medianBlur(sal_pimenta, 5)
    gauss_g = cv2.GaussianBlur(gaussiano, (5, 5), 1.4)

    # nitidez por mascara de convolucao (kernel laplaciano invertido)
    kernel_nitidez = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32)
    nitidez = cv2.filter2D(cinza, -1, kernel_nitidez)

    metricas = {
        "ruido_sal_e_pimenta": {
            "psnr_ruidosa_dB": round(float(peak_signal_noise_ratio(cinza, sal_pimenta)), 2),
            "psnr_filtro_media_dB": round(float(peak_signal_noise_ratio(cinza, media_sp)), 2),
            "psnr_filtro_mediana_dB": round(float(peak_signal_noise_ratio(cinza, mediana_sp)), 2),
            "ssim_filtro_media": round(float(structural_similarity(cinza, media_sp)), 4),
            "ssim_filtro_mediana": round(float(structural_similarity(cinza, mediana_sp)), 4),
        },
        "ruido_gaussiano": {
            "psnr_ruidosa_dB": round(float(peak_signal_noise_ratio(cinza, gaussiano)), 2),
            "psnr_filtro_gaussiano_dB": round(float(peak_signal_noise_ratio(cinza, gauss_g)), 2),
            "ssim_filtro_gaussiano": round(float(structural_similarity(cinza, gauss_g)), 4),
        },
    }

    m = metricas["ruido_sal_e_pimenta"]
    g = metricas["ruido_gaussiano"]
    painel(
        [cinza, sal_pimenta, media_sp, mediana_sp, gaussiano, gauss_g, nitidez,
         cv2.absdiff(nitidez, cinza)],
        ["Original",
         f"Ruido sal e pimenta 6%\nPSNR={m['psnr_ruidosa_dB']} dB",
         f"Filtro de MEDIA 5x5 (linear)\nPSNR={m['psnr_filtro_media_dB']} dB",
         f"Filtro de MEDIANA 5x5 (nao-linear)\nPSNR={m['psnr_filtro_mediana_dB']} dB",
         f"Ruido gaussiano s=22\nPSNR={g['psnr_ruidosa_dB']} dB",
         f"Filtro GAUSSIANO 5x5\nPSNR={g['psnr_filtro_gaussiano_dB']} dB",
         "Realce de NITIDEZ (kernel 3x3)", "Diferenca |nitidez - original|"],
        "03_filtragem_espacial.png",
        "Filtragem ESPACIAL: convolucao / estatistica de ordem numa vizinhanca",
        linhas=2, tamanho=(15, 7.6),
    )
    return metricas


# ---------------------------------------------------------------------------
# 3) Dominio da frequencia
# ---------------------------------------------------------------------------


def filtro_butterworth(shape, corte, ordem=2, passa_alta=False):
    linhas, colunas = shape
    u = np.arange(linhas) - linhas // 2
    v = np.arange(colunas) - colunas // 2
    U, V = np.meshgrid(v, u)
    D = np.sqrt(U ** 2 + V ** 2)
    H = 1.0 / (1.0 + (D / max(corte, 1e-6)) ** (2 * ordem))
    return 1.0 - H if passa_alta else H


def dominio_frequencia(cinza):
    F = np.fft.fftshift(np.fft.fft2(cinza.astype(np.float64)))
    espectro = np.log1p(np.abs(F))
    espectro_img = cv2.normalize(espectro, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    h_baixa = filtro_butterworth(cinza.shape, corte=40, ordem=2)
    h_alta = filtro_butterworth(cinza.shape, corte=18, ordem=2, passa_alta=True)

    def aplicar(H):
        r = np.fft.ifft2(np.fft.ifftshift(F * H)).real
        return cv2.normalize(r, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    passa_baixa = aplicar(h_baixa)
    passa_alta = aplicar(h_alta)

    painel(
        [cinza, (h_baixa * 255).astype(np.uint8), passa_baixa,
         espectro_img, (h_alta * 255).astype(np.uint8), passa_alta],
        ["Original (dominio espacial)",
         "Filtro Butterworth PASSA-BAIXA\nH(u,v), D0=40, n=2",
         "Resultado: suavizacao\n(altas frequencias removidas)",
         "Espectro de magnitude\nlog(1+|F(u,v)|)",
         "Filtro Butterworth PASSA-ALTA\nH(u,v), D0=18, n=2",
         "Resultado: so as bordas\n(baixas frequencias removidas)"],
        "04_dominio_frequencia.png",
        "Filtragem no DOMINIO DA FREQUENCIA (Transformada de Fourier 2D)",
        linhas=2, tamanho=(13, 7.6),
    )


# ---------------------------------------------------------------------------
# 4) Bordas, limiarizacao e morfologia
# ---------------------------------------------------------------------------


def bordas_e_morfologia(cinza):
    suave = cv2.GaussianBlur(cinza, (5, 5), 1.2)
    sobel_x = cv2.Sobel(suave, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(suave, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = cv2.normalize(np.hypot(sobel_x, sobel_y), None, 0, 255,
                              cv2.NORM_MINMAX).astype(np.uint8)
    laplaciano = cv2.normalize(np.abs(cv2.Laplacian(suave, cv2.CV_64F, ksize=3)),
                               None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    canny = cv2.Canny(suave, 60, 160)

    painel(
        [cinza,
         cv2.normalize(np.abs(sobel_x), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
         cv2.normalize(np.abs(sobel_y), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8),
         magnitude, laplaciano, canny],
        ["Original", "|Sobel X| (bordas verticais)", "|Sobel Y| (bordas horizontais)",
         "Magnitude do gradiente", "Laplaciano (2a derivada)",
         "Canny (nao-max + histerese)"],
        "05_deteccao_bordas.png",
        "Realce de BORDAS: derivadas discretas da funcao de intensidade",
        linhas=2, tamanho=(13, 7.4),
    )

    limiar, otsu = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    erosao = cv2.erode(otsu, kernel)
    dilatacao = cv2.dilate(otsu, kernel)
    abertura = cv2.morphologyEx(otsu, cv2.MORPH_OPEN, kernel)
    fechamento = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
    gradiente_morf = cv2.morphologyEx(otsu, cv2.MORPH_GRADIENT, kernel)

    painel(
        [otsu, erosao, dilatacao, abertura, fechamento, gradiente_morf],
        [f"Limiarizacao de OTSU (T={int(limiar)})", "Erosao (elipse 7x7)",
         "Dilatacao", "Abertura (erosao + dilatacao)",
         "Fechamento (dilatacao + erosao)", "Gradiente morfologico"],
        "06_limiarizacao_morfologia.png",
        "Limiarizacao automatica (Otsu) e MORFOLOGIA MATEMATICA binaria",
        linhas=2, tamanho=(13, 7.4),
    )
    return float(limiar)


def main():
    print("=" * 70)
    print(" AREA 2 - PROCESSAMENTO DIGITAL DE IMAGENS (OpenCV / scikit-image)")
    print("=" * 70)
    print(f"  OpenCV {cv2.__version__}")

    colorida = data.coins()                      # imagem classica de PDI
    cinza = colorida if colorida.ndim == 2 else cv2.cvtColor(colorida, cv2.COLOR_RGB2GRAY)
    cinza = np.ascontiguousarray(cinza.astype(np.uint8))
    print(f"  Imagem de entrada: skimage.data.coins  {cinza.shape}  {cinza.dtype}")
    print("-" * 70)

    escuro = operacoes_pontuais(cinza)
    histogramas(cinza, escuro)
    metricas = filtragem_espacial(cinza)
    dominio_frequencia(cinza)
    limiar = bordas_e_morfologia(cinza)

    metricas["limiar_otsu"] = limiar
    metricas["imagem"] = {"fonte": "skimage.data.coins",
                          "altura": int(cinza.shape[0]),
                          "largura": int(cinza.shape[1]),
                          "niveis_de_cinza": 256}
    caminho = os.path.join(SAIDA, "metricas_processamento.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)
    print(f"  [ok] {caminho}")

    print("-" * 70)
    m = metricas["ruido_sal_e_pimenta"]
    print("  RESULTADO-CHAVE: contra ruido impulsivo (sal e pimenta),")
    print(f"    media 5x5   -> PSNR {m['psnr_filtro_media_dB']} dB")
    print(f"    mediana 5x5 -> PSNR {m['psnr_filtro_mediana_dB']} dB  <-- melhor")
    print("    (filtro nao-linear preserva bordas; o linear as borra)")
    print("=" * 70)


if __name__ == "__main__":
    main()
