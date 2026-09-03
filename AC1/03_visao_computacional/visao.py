"""
=============================================================================
 AREA 3 - VISAO COMPUTACIONAL (Visao Artificial)
 Aplicacao: OpenCV - detector de Viola-Jones (Haar Cascade), segmentacao por
            watershed com extracao de descritores e casamento de pontos-chave
            ORB + RANSAC
   https://github.com/opencv/opencv  (Apache 2.0)
   Classificadores Haar pre-treinados distribuidos junto com o OpenCV.
=============================================================================

O QUE ESTE CODIGO DEMONSTRA (aspectos especificos da VISAO COMPUTACIONAL):

  IMAGEM  ---->  [ interpretacao ]  ---->  DADOS / DESCRICAO SIMBOLICA

  Repare na inversao em relacao a Area 1: la o computador PRODUZIA a imagem a
  partir de um modelo; aqui ele RECUPERA um modelo (quantos objetos existem,
  onde estao, que tamanho tem, ha um rosto?) a partir da imagem. A saida
  principal deste script NAO e uma figura - sao arquivos .json e .csv. As
  figuras servem apenas para conferencia humana.

  Experimentos:
    1. DETECCAO DE OBJETOS  - Viola-Jones (Haar + AdaBoost + cascata), o
       classificador que popularizou a deteccao de faces em tempo real.
       Saida: caixas delimitadoras (x, y, w, h) + confianca por nivel.
    2. SEGMENTACAO E MENSURACAO - separacao de objetos encostados por
       watershed sobre a transformada de distancia; para cada objeto sao
       extraidos descritores (area, diametro, circularidade, excentricidade).
       Saida: tabela CSV - o passo tipico de inspecao industrial / contagem.
    3. CASAMENTO DE CARACTERISTICAS - detector/descritor ORB, casamento por
       forca bruta com Hamming, filtragem de outliers por RANSAC e estimativa
       da HOMOGRAFIA que relaciona as duas vistas. E a base de reconhecimento
       de objetos, panoramas, realidade aumentada e SLAM.

USO:
    python visao.py
"""

import csv
import json
import os

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from skimage import data, measure  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saidas", "03_visao")
os.makedirs(SAIDA, exist_ok=True)


def salvar(fig, nome):
    caminho = os.path.join(SAIDA, nome)
    fig.savefig(caminho, dpi=110, facecolor="white")
    plt.close(fig)
    print(f"  [ok] {caminho}")


# ---------------------------------------------------------------------------
# 1) Deteccao de faces e olhos - Viola-Jones (Haar Cascade)
# ---------------------------------------------------------------------------


def deteccao_viola_jones():
    print("\n[1] DETECCAO DE OBJETOS - Viola-Jones (Haar Cascade)")
    rgb = data.astronaut()                       # 512x512, dominio publico (NASA)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    cinza = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    cinza = cv2.equalizeHist(cinza)              # pre-processamento (Area 2!)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    olho_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_eye.xml")

    faces, _, pesos = face_cascade.detectMultiScale3(
        cinza, scaleFactor=1.08, minNeighbors=5, minSize=(40, 40),
        outputRejectLevels=True)

    anotada = rgb.copy()
    deteccoes = []
    for i, (x, y, w, h) in enumerate(faces):
        cv2.rectangle(anotada, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(anotada, f"face {i} ({w}x{h}px)", (x, max(y - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

        roi = cinza[y:y + h, x:x + w]
        olhos = olho_cascade.detectMultiScale(roi, scaleFactor=1.06,
                                              minNeighbors=8, minSize=(18, 18))
        lista_olhos = []
        for (ex, ey, ew, eh) in olhos[:2]:
            cv2.rectangle(anotada, (x + ex, y + ey),
                          (x + ex + ew, y + ey + eh), (255, 60, 60), 2)
            lista_olhos.append({"x": int(x + ex), "y": int(y + ey),
                                "largura": int(ew), "altura": int(eh)})

        deteccoes.append({
            "id": i,
            "classe": "face_frontal",
            "caixa": {"x": int(x), "y": int(y), "largura": int(w), "altura": int(h)},
            "area_px": int(w * h),
            "score_cascata": round(float(pesos[i]), 3) if len(pesos) > i else None,
            "olhos_detectados": lista_olhos,
        })

    resultado = {
        "algoritmo": "Viola-Jones (Haar-like + AdaBoost + cascata de rejeicao)",
        "classificadores": ["haarcascade_frontalface_default.xml",
                            "haarcascade_eye.xml"],
        "imagem": {"fonte": "skimage.data.astronaut", "largura": int(rgb.shape[1]),
                   "altura": int(rgb.shape[0])},
        "parametros": {"scaleFactor": 1.08, "minNeighbors": 5, "minSize": [40, 40]},
        "total_faces": len(deteccoes),
        "deteccoes": deteccoes,
    }
    caminho = os.path.join(SAIDA, "deteccoes_faces.json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"    faces detectadas: {len(deteccoes)}")
    for d in deteccoes:
        c = d["caixa"]
        print(f"      face {d['id']}: caixa=({c['x']},{c['y']},{c['largura']},"
              f"{c['altura']})  olhos={len(d['olhos_detectados'])}"
              f"  score={d['score_cascata']}")
    print(f"  [ok] {caminho}")

    fig, eixos = plt.subplots(1, 2, figsize=(11, 5.6), constrained_layout=True)
    eixos[0].imshow(rgb)
    eixos[0].set_title("Entrada: apenas uma matriz de pixels", fontsize=10)
    eixos[1].imshow(anotada)
    eixos[1].set_title(f"Saida: {len(deteccoes)} face(s) + olhos localizados\n"
                       "(a informacao util e o JSON, nao a figura)", fontsize=10)
    for e in eixos:
        e.axis("off")
    fig.suptitle("Visao computacional: deteccao de objetos por Viola-Jones",
                 fontsize=13, fontweight="bold")
    salvar(fig, "01_deteccao_faces.png")
    return resultado


# ---------------------------------------------------------------------------
# 2) Segmentacao + mensuracao (watershed sobre transformada de distancia)
# ---------------------------------------------------------------------------


def contagem_e_medicao():
    print("\n[2] SEGMENTACAO E MENSURACAO - watershed + descritores de regiao")
    cinza = data.coins().astype(np.uint8)
    bgr = cv2.cvtColor(cinza, cv2.COLOR_GRAY2BGR)

    # --- pre-processamento (tecnicas da Area 2 a servico da Area 3) --------
    # A foto tem iluminacao nao uniforme (canto superior mais claro). O fundo
    # e estimado por uma ABERTURA morfologica com elemento maior que as moedas
    # e subtraido da imagem - so entao o limiar global de Otsu funciona bem.
    kernel_fundo = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (75, 75))
    fundo_estimado = cv2.morphologyEx(cinza, cv2.MORPH_OPEN, kernel_fundo)
    corrigida = cv2.normalize(cv2.subtract(cinza, fundo_estimado), None,
                              0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    suave = cv2.GaussianBlur(corrigida, (5, 5), 1.2)
    _, binaria = cv2.threshold(suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel, iterations=3)
    binaria = cv2.morphologyEx(binaria, cv2.MORPH_OPEN, kernel, iterations=2)

    # --- marcadores: fundo certo, frente certa e regiao desconhecida --------
    fundo_certo = cv2.dilate(binaria, kernel, iterations=3)
    distancia = cv2.distanceTransform(binaria, cv2.DIST_L2, 5)
    _, frente_certa = cv2.threshold(distancia, 0.45 * distancia.max(), 255, 0)
    frente_certa = np.uint8(frente_certa)
    desconhecido = cv2.subtract(fundo_certo, frente_certa)

    n_marcadores, marcadores = cv2.connectedComponents(frente_certa)
    marcadores += 1
    marcadores[desconhecido == 255] = 0
    marcadores = cv2.watershed(bgr, marcadores)   # linhas divisorias = -1

    rotulos = marcadores.copy()
    rotulos[rotulos <= 1] = 0                     # 1 = fundo, -1 = divisa

    propriedades = measure.regionprops(rotulos)
    linhas = []
    anotada = cv2.cvtColor(cinza, cv2.COLOR_GRAY2RGB)
    for p in propriedades:
        if p.area < 300:
            continue
        cy, cx = p.centroid
        diametro = float(p.equivalent_diameter_area)
        circularidade = float(4 * np.pi * p.area / max(p.perimeter ** 2, 1e-9))
        linhas.append({
            "id": len(linhas) + 1,
            "centroide_x": round(float(cx), 1),
            "centroide_y": round(float(cy), 1),
            "area_px2": int(p.area),
            "perimetro_px": round(float(p.perimeter), 1),
            "diametro_equivalente_px": round(diametro, 1),
            "circularidade": round(circularidade, 3),
            "excentricidade": round(float(p.eccentricity), 3),
        })
        cv2.circle(anotada, (int(cx), int(cy)), int(diametro / 2),
                   (0, 200, 255), 2)
        cv2.putText(anotada, str(linhas[-1]["id"]), (int(cx) - 8, int(cy) + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    caminho_csv = os.path.join(SAIDA, "medicoes_objetos.csv")
    with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)

    diametros = [l["diametro_equivalente_px"] for l in linhas]
    resumo = {
        "objetos_contados": len(linhas),
        "gabarito_visual": 24,
        "diametro_medio_px": round(float(np.mean(diametros)), 2),
        "diametro_min_px": float(np.min(diametros)),
        "diametro_max_px": float(np.max(diametros)),
        "circularidade_media": round(
            float(np.mean([l["circularidade"] for l in linhas])), 3),
    }
    with open(os.path.join(SAIDA, "medicoes_resumo.json"), "w",
              encoding="utf-8") as f:
        json.dump({"resumo": resumo, "objetos": linhas}, f, indent=2,
                  ensure_ascii=False)

    print(f"    objetos contados: {resumo['objetos_contados']} "
          f"(gabarito visual: {resumo['gabarito_visual']})")
    print(f"    diametro medio: {resumo['diametro_medio_px']} px  "
          f"(min {resumo['diametro_min_px']} / max {resumo['diametro_max_px']})")
    print(f"  [ok] {caminho_csv}")

    dist_norm = cv2.normalize(distancia, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    fig, eixos = plt.subplots(2, 3, figsize=(15, 7.4), constrained_layout=True)
    for eixo, img, titulo, cmap in [
        (eixos[0, 0], cinza, "1. Imagem de entrada", "gray"),
        (eixos[0, 1], corrigida, "2. Correcao de iluminacao\n(subtracao do fundo morfologico)", "gray"),
        (eixos[0, 2], binaria, "3. Segmentacao (Otsu + morfologia)", "gray"),
        (eixos[1, 0], dist_norm, "4. Transformada de distancia\n(picos = centros dos objetos)", "magma"),
        (eixos[1, 1], np.where(marcadores == -1, 255, 0).astype(np.uint8),
         "5. Linhas divisorias do watershed", "gray"),
        (eixos[1, 2], anotada, f"6. {len(linhas)} objetos separados, medidos e rotulados", None),
    ]:
        eixo.imshow(img, cmap=cmap) if cmap else eixo.imshow(img)
        eixo.set_title(titulo, fontsize=10)
        eixo.axis("off")
    fig.suptitle("Da imagem para os DADOS: contagem e mensuracao automatica",
                 fontsize=13, fontweight="bold")
    salvar(fig, "02_contagem_medicao.png")
    return resumo


# ---------------------------------------------------------------------------
# 3) Casamento de caracteristicas ORB + RANSAC (homografia)
# ---------------------------------------------------------------------------


def casamento_orb():
    print("\n[3] CASAMENTO DE CARACTERISTICAS - ORB + forca bruta + RANSAC")
    original = cv2.cvtColor(data.astronaut(), cv2.COLOR_RGB2GRAY)

    # Cena sintetica: o mesmo objeto rotacionado, reduzido e mais escuro.
    # A ideia e verificar a INVARIANCIA do descritor a essas transformacoes.
    h, w = original.shape
    M_conhecida = cv2.getRotationMatrix2D((w / 2, h / 2), angle=32, scale=0.7)
    M_conhecida[0, 2] += 40
    M_conhecida[1, 2] += 25
    cena = cv2.warpAffine(original, M_conhecida, (w, h), borderValue=110)
    cena = cv2.convertScaleAbs(cena, alpha=0.75, beta=12)   # mudanca de brilho

    orb = cv2.ORB_create(nfeatures=1500)
    kp1, des1 = orb.detectAndCompute(original, None)
    kp2, des2 = orb.detectAndCompute(cena, None)

    casador = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    pares = casador.knnMatch(des1, des2, k=2)

    # teste da razao de Lowe: descarta casamentos ambiguos
    bons = [m for m, n in pares if m.distance < 0.75 * n.distance]
    bons = sorted(bons, key=lambda m: m.distance)

    origem = np.float32([kp1[m.queryIdx].pt for m in bons]).reshape(-1, 1, 2)
    destino = np.float32([kp2[m.trainIdx].pt for m in bons]).reshape(-1, 1, 2)
    H, mascara = cv2.findHomography(origem, destino, cv2.RANSAC, 4.0)
    inliers = int(mascara.sum())

    # projeta o contorno do objeto original na cena usando a homografia
    cantos = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    projetado = cv2.perspectiveTransform(cantos, H)
    cena_rgb = cv2.cvtColor(cena, cv2.COLOR_GRAY2RGB)
    cv2.polylines(cena_rgb, [np.int32(projetado)], True, (0, 255, 0), 3)

    desenho = cv2.drawMatches(
        original, kp1, cena, kp2, bons[:60], None,
        matchesMask=mascara.ravel().tolist()[:60],
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    resultado = {
        "detector_descritor": "ORB (FAST + BRIEF orientado, descritor binario 256 bits)",
        "casamento": "forca bruta, distancia de Hamming + teste da razao de Lowe (0,75)",
        "estimador_robusto": "RANSAC, limiar de reprojecao 4,0 px",
        "pontos_chave_imagem_1": len(kp1),
        "pontos_chave_imagem_2": len(kp2),
        "casamentos_apos_lowe": len(bons),
        "inliers_ransac": inliers,
        "taxa_inliers": round(inliers / max(len(bons), 1), 3),
        "transformacao_aplicada_a_cena": {"rotacao_graus": 32, "escala": 0.7,
                                          "translacao_px": [40, 25],
                                          "brilho": "alpha=0,75 beta=+12"},
        "homografia_estimada": [[round(float(v), 5) for v in linha] for linha in H],
    }
    with open(os.path.join(SAIDA, "casamento_orb.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"    pontos-chave: {len(kp1)} / {len(kp2)}")
    print(f"    casamentos apos Lowe: {len(bons)} | inliers RANSAC: {inliers} "
          f"({resultado['taxa_inliers'] * 100:.1f}%)")

    fig, eixos = plt.subplots(2, 1, figsize=(12, 9.5), constrained_layout=True)
    eixos[0].imshow(desenho, cmap="gray")
    eixos[0].set_title(f"Casamentos ORB validados por RANSAC "
                       f"({inliers} inliers de {len(bons)} candidatos)", fontsize=10)
    eixos[1].imshow(cena_rgb)
    eixos[1].set_title("Objeto localizado na cena pela homografia estimada\n"
                       "(mesmo com rotacao de 32 graus, escala 0,7 e mudanca de brilho)",
                       fontsize=10)
    for e in eixos:
        e.axis("off")
    fig.suptitle("Reconhecimento por CARACTERISTICAS LOCAIS invariantes",
                 fontsize=13, fontweight="bold")
    salvar(fig, "03_casamento_orb_ransac.png")
    return resultado


def main():
    print("=" * 70)
    print(" AREA 3 - VISAO COMPUTACIONAL (OpenCV)")
    print("=" * 70)
    print(f"  OpenCV {cv2.__version__}")
    faces = deteccao_viola_jones()
    medicao = contagem_e_medicao()
    orb = casamento_orb()

    print("\n" + "-" * 70)
    print("  SINTESE DA AREA: a saida sao DADOS, nao imagens ->")
    print(f"    {faces['total_faces']} face(s) localizada(s) | "
          f"{medicao['objetos_contados']} objetos medidos | "
          f"{orb['inliers_ransac']} correspondencias geometricamente validas")
    print("=" * 70)


if __name__ == "__main__":
    main()
