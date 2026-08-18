import io
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image


# ============================================================
# IMPOSTAZIONI
# ============================================================

FINAL_W = 1080
FINAL_H = 1350

DEFAULT_URL = (
    "https://widget.weathersicily.it/assets/cover/revisions/"
    "midnight-20260818T005707-1317182/"
    "sicilia-social-icone.png?v=1787007429"
)


# ============================================================
# SCARICA L'IMMAGINE DAL LINK
# ============================================================

def download_image(url):

    url = url.strip()

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError("Inserisci un URL valido.")

    host = (parsed.hostname or "").lower()

    if not (
        host == "weathersicily.it"
        or host.endswith(".weathersicily.it")
    ):
        raise ValueError(
            "Per sicurezza il link deve essere di Weather Sicily."
        )

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")


# ============================================================
# PORTA L'IMMAGINE A 1080x1350 SENZA DISTORCERLA
# ============================================================

def normalize_image(image):

    if image.size == (1080, 1350):
        return image.copy()

    return image.resize(
        (1080, 1350),
        Image.Resampling.LANCZOS
    )


# ============================================================
# RIMUOVE LE PARTI DUPLICATE DALLA MAPPA
# ============================================================

def clean_map(map_img):

    img = np.array(map_img)

    h, w = img.shape[:2]

    mask = np.zeros(
        (h, w),
        dtype=np.uint8
    )

    # --------------------------------------------------------
    # RIQUADRO "SICILIA / DOMANI / DATA"
    #
    # Nella mappa originale si trova in alto a sinistra.
    # --------------------------------------------------------

    mask[
        8:min(78, h),
        8:min(245, w)
    ] = 255

    # --------------------------------------------------------
    # SECONDO LOGO WS
    #
    # Si trova in alto a destra della mappa.
    # --------------------------------------------------------

    mask[
        5:min(72, h),
        max(875, w - 115):min(988, w)
    ] = 255

    # --------------------------------------------------------
    # INPAINT
    # --------------------------------------------------------

    bgr = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2BGR
    )

    repaired = cv2.inpaint(
        bgr,
        mask,
        9,
        cv2.INPAINT_TELEA
    )

    rgb = cv2.cvtColor(
        repaired,
        cv2.COLOR_BGR2RGB
    )

    return Image.fromarray(rgb)


# ============================================================
# INGRANDISCE UNA ZONA DELL'IMMAGINE
# ============================================================

def zoom_region(
    image,
    box,
    scale=1.30,
    paste_position=None
):
    """
    Ingrandisce una zona dell'immagine e la riposiziona.
    box = (x1, y1, x2, y2)
    """

    x1, y1, x2, y2 = box

    crop = image.crop(
        (x1, y1, x2, y2)
    )

    new_w = int(crop.width * scale)
    new_h = int(crop.height * scale)

    crop = crop.resize(
        (new_w, new_h),
        Image.Resampling.LANCZOS
    )

    if paste_position is None:
        paste_position = (x1, y1)

    image.paste(
        crop,
        paste_position
    )

    return image


# ============================================================
# INGRANDISCE LE DIDASCALIE DELLA MAPPA
# ============================================================

def enlarge_map_labels(map_image):

    result = map_image.copy()

    # --------------------------------------------------------
    # IMPORTANTE
    #
    # Queste coordinate sono riferite alla mappa già
    # ingrandita 1080 x 670.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # MARE TIRRENO OCCIDENTALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (270, 35, 465, 105),
        scale=1.32,
        paste_position=(255, 25)
    )

    # --------------------------------------------------------
    # MARE TIRRENO ORIENTALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (500, 100, 690, 170),
        scale=1.32,
        paste_position=(490, 90)
    )

    # --------------------------------------------------------
    # CANALE DI SICILIA OCCIDENTALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (25, 325, 175, 405),
        scale=1.32,
        paste_position=(15, 315)
    )

    # --------------------------------------------------------
    # MAR IONIO SETTENTRIONALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (875, 245, 1075, 330),
        scale=1.32,
        paste_position=(865, 235)
    )

    # --------------------------------------------------------
    # MAR IONIO MERIDIONALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (875, 425, 1075, 505),
        scale=1.32,
        paste_position=(865, 415)
    )

    # --------------------------------------------------------
    # CANALE DI SICILIA MERIDIONALE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (390, 585, 570, 655),
        scale=1.32,
        paste_position=(380, 575)
    )

    # --------------------------------------------------------
    # RIQUADRO PELAGIE
    # --------------------------------------------------------

    result = zoom_region(
        result,
        (120, 575, 270, 650),
        scale=1.38,
        paste_position=(105, 565)
    )

    return result

def create_final_image(original):

    source = normalize_image(original)

    # ========================================================
    # HEADER
    #
    # Manteniamo l'intestazione originale.
    #
    # Qui rimangono:
    # PREVISIONI SICILIA
    # DOMANI
    # Giorno/data
    # UN SOLO LOGO WS
    # ========================================================

    header = source.crop(
        (0, 0, 1080, 165)
    )

    # ========================================================
    # MAPPA
    #
    # Questa è la parte che deve diventare GRANDE.
    #
    # Prendiamo solo la mappa interna, eliminando:
    # - bordo esterno
    # - scheda giorno/data
    # - secondo logo
    # ========================================================

    map_original = source.crop(
        (46, 190, 1034, 790)
    )

    map_clean = clean_map(
        map_original
    )

    # La mappa occupa tutta la larghezza
    map_final = map_clean.resize(
        (1080, 670),
        Image.Resampling.LANCZOS
    )

    # ========================================================
    # TEMPERATURE
    #
    # Prendiamo la sezione originale e la ingrandiamo.
    # ========================================================

    temperature_original = source.crop(
        (20, 845, 1060, 1275)
    )

    temperature_final = temperature_original.resize(
        (1080, 500),
        Image.Resampling.LANCZOS
    )

    # ========================================================
    # CANVAS
    # ========================================================

    result = Image.new(
        "RGB",
        (FINAL_W, FINAL_H),
        (7, 26, 49)
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    result.paste(
        header,
        (0, 0)
    )

    # --------------------------------------------------------
    # MAPPA
    # --------------------------------------------------------

    result.paste(
        map_final,
        (0, 165)
    )

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    result.paste(
        temperature_final,
        (0, 835)
    )

    # --------------------------------------------------------
    # NON ricostruiamo il footer:
    # vogliamo esattamente il layout della tua immagine
    # di riferimento.
    # --------------------------------------------------------

    return result


# ============================================================
# STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Meteo Sicilia Formatter",
    page_icon="🌤️",
    layout="centered"
)

st.title("🌤️ Meteo Sicilia Formatter")

st.write(
    "Inserisci il link dell'immagine giornaliera "
    "oppure carica direttamente il PNG."
)


# ============================================================
# INPUT URL
# ============================================================

url = st.text_input(
    "🔗 Link immagine Weather Sicily",
    value=DEFAULT_URL
)


# ============================================================
# UPLOAD DA TELEFONO
# ============================================================

uploaded = st.file_uploader(
    "📷 Oppure carica un'immagine",
    type=["png", "jpg", "jpeg"]
)


# ============================================================
# PULSANTE
# ============================================================

if st.button(
    "✨ GENERA IMMAGINE",
    use_container_width=True
):

    try:

        with st.spinner(
            "Sto trasformando l'immagine..."
        ):

            # Se carichi una foto utilizziamo quella.
            if uploaded is not None:

                original = Image.open(
                    uploaded
                ).convert("RGB")

            # Altrimenti utilizziamo il link.
            else:

                original = download_image(
                    url
                )

            # Trasformazione
            result = create_final_image(
                original
            )

        st.success(
            "✅ Immagine trasformata!"
        )

        # Anteprima
        st.image(
            result,
            caption="Risultato finale",
            use_container_width=True
        )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        buffer = io.BytesIO()

        result.save(
            buffer,
            format="PNG"
        )

        st.download_button(
            "⬇️ SCARICA PNG",
            data=buffer.getvalue(),
            file_name="meteo_sicilia_finale.png",
            mime="image/png",
            use_container_width=True
        )

    except Exception as e:

        st.error(
            "❌ Errore durante la trasformazione"
        )

        st.code(
            str(e)
        )


st.divider()

st.caption(
    "Meteo Sicilia Formatter • 1080 × 1350"
)
