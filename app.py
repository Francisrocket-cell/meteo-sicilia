import io
from urllib.parse import urlparse

import cv2
import numpy as np
import requests
import streamlit as st
from PIL import Image


# ============================================================
# CONFIGURAZIONE
# ============================================================

OUTPUT_SIZE = (1080, 1350)

DEFAULT_URL = (
    "https://widget.weathersicily.it/assets/cover/revisions/"
    "midnight-20260818T005707-1317182/"
    "sicilia-social-icone.png?v=1787007429"
)


# ============================================================
# DOWNLOAD IMMAGINE
# ============================================================

def download_image(url: str) -> Image.Image:

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            "Il link deve iniziare con http:// o https://."
        )

    host = (parsed.hostname or "").lower()

    if not (
        host == "weathersicily.it"
        or host.endswith(".weathersicily.it")
    ):
        raise ValueError(
            "Per sicurezza questa versione accetta solo "
            "immagini provenienti da weathersicily.it."
        )

    response = requests.get(
        url.strip(),
        timeout=30,
        headers={
            "User-Agent": "MeteoSiciliaFormatter/1.0"
        }
    )

    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")


# ============================================================
# NORMALIZZA IMMAGINE
# ============================================================

def normalize_image(image: Image.Image) -> Image.Image:

    return image.resize(
        OUTPUT_SIZE,
        Image.Resampling.LANCZOS
    )


# ============================================================
# PULIZIA MAPPA
# ============================================================

def clean_map(map_image: Image.Image) -> Image.Image:

    arr = np.array(map_image)

    mask = np.zeros(
        arr.shape[:2],
        dtype=np.uint8
    )

    h, w = arr.shape[:2]

    # --------------------------------------------------------
    # ELIMINA RIQUADRO INTERNO:
    # SICILIA / DOMANI / GIORNO
    # --------------------------------------------------------

    mask[
        5:min(80, h),
        5:min(250, w)
    ] = 255

    # --------------------------------------------------------
    # ELIMINA SECONDO LOGO WS
    # --------------------------------------------------------

    x1 = max(0, w - 120)
    x2 = w - 5

    mask[
        5:min(70, h),
        x1:x2
    ] = 255

    # --------------------------------------------------------
    # INPAINTING
    # --------------------------------------------------------

    bgr = cv2.cvtColor(
        arr,
        cv2.COLOR_RGB2BGR
    )

    repaired = cv2.inpaint(
        bgr,
        mask,
        5,
        cv2.INPAINT_TELEA
    )

    return Image.fromarray(
        cv2.cvtColor(
            repaired,
            cv2.COLOR_BGR2RGB
        )
    )


# ============================================================
# ZOOM DI UNA ZONA
# ============================================================

def zoom_region(
    image: Image.Image,
    box,
    scale=1.30,
    paste_position=None
):

    x1, y1, x2, y2 = box

    crop = image.crop(
        (x1, y1, x2, y2)
    )

    new_width = int(
        crop.width * scale
    )

    new_height = int(
        crop.height * scale
    )

    crop = crop.resize(
        (new_width, new_height),
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
# INGRANDISCE LE INFORMAZIONI MARINE
# ============================================================

def enlarge_map_labels(map_image):

    result = map_image.copy()

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


# ============================================================
# CREA IMMAGINE FINALE
# ============================================================

def create_final_image(original):

    source = normalize_image(
        original
    )

    # ========================================================
    # HEADER
    # ========================================================

    header = source.crop(
        (0, 0, 1080, 165)
    )

    # ========================================================
    # MAPPA
    # ========================================================

    map_original = source.crop(
        (46, 190, 1034, 790)
    )

    # Elimina doppio logo e doppia data
    map_clean = clean_map(
        map_original
    )

    # Ingrandimento generale della mappa
    map_final = map_clean.resize(
        (1080, 670),
        Image.Resampling.LANCZOS
    )

    # Ingrandimento selettivo
    # delle informazioni marine
    map_final = enlarge_map_labels(
        map_final
    )

    # ========================================================
    # TEMPERATURE
    # ========================================================

    temperature_original = source.crop(
        (20, 845, 1060, 1275)
    )

    temperature_final = temperature_original.resize(
        (1080, 500),
        Image.Resampling.LANCZOS
    )

    # ========================================================
    # CANVAS FINALE
    # ========================================================

    result = Image.new(
        "RGB",
        OUTPUT_SIZE,
        (7, 26, 49)
    )

    # Header
    result.paste(
        header,
        (0, 0)
    )

    # Mappa
    result.paste(
        map_final,
        (0, 165)
    )

    # Temperature
    result.paste(
        temperature_final,
        (0, 835)
    )

    return result


# ============================================================
# WEB APP STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Meteo Sicilia Formatter",
    page_icon="🌤️",
    layout="centered"
)


st.title(
    "🌤️ Meteo Sicilia — Formatter"
)

st.caption(
    "Incolla il link dell'immagine Weather Sicily "
    "e genera automaticamente il formato pulito."
)


# ============================================================
# LINK
# ============================================================

url = st.text_input(
    "🔗 Link dell'immagine",
    value=DEFAULT_URL
)


# ============================================================
# UPLOAD ALTERNATIVO
# ============================================================

uploaded = st.file_uploader(
    "📷 Oppure carica direttamente l'immagine",
    type=[
        "png",
        "jpg",
        "jpeg"
    ]
)


# ============================================================
# PULSANTE
# ============================================================

generate = st.button(
    "✨ GENERA IMMAGINE",
    use_container_width=True
)


# ============================================================
# GENERAZIONE
# ============================================================

if generate:

    try:

        with st.spinner(
            "Elaborazione in corso..."
        ):

            # Se è stata caricata un'immagine,
            # usa quella.
            if uploaded is not None:

                source = Image.open(
                    uploaded
                ).convert("RGB")

            else:

                source = download_image(
                    url
                )

            # Crea immagine finale
            result = create_final_image(
                source
            )

        st.success(
            "✅ Immagine generata correttamente!"
        )

        # ----------------------------------------------------
        # ANTEPRIMA
        # ----------------------------------------------------

        st.image(
            result,
            caption="Anteprima finale",
            use_container_width=True
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        buffer = io.BytesIO()

        result.save(
            buffer,
            format="PNG",
            optimize=True
        )

        st.download_button(
            "⬇️ SCARICA PNG",
            data=buffer.getvalue(),
            file_name="meteo_sicilia_formattato.png",
            mime="image/png",
            use_container_width=True
        )

    except Exception as error:

        st.error(
            f"❌ Errore durante l'elaborazione: {error}"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Il formatter non usa generazione AI: "
    "ricompone l'immagine mantenendo i dati originali."
)
