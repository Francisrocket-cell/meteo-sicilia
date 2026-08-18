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

OUTPUT_WIDTH = 1080
OUTPUT_HEIGHT = 1350

DEFAULT_URL = (
    "https://widget.weathersicily.it/assets/cover/revisions/"
    "midnight-20260818T005707-1317182/"
    "sicilia-social-icone.png?v=1787007429"
)


# ============================================================
# SCARICA IMMAGINE DAL LINK
# ============================================================

def download_image(url):

    url = url.strip()

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            "Il link deve iniziare con http:// oppure https://"
        )

    host = (parsed.hostname or "").lower()

    # Per sicurezza accettiamo solo Weather Sicily
    if not (
        host == "weathersicily.it"
        or host.endswith(".weathersicily.it")
    ):
        raise ValueError(
            "Per sicurezza il link deve provenire da "
            "weathersicily.it"
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
# ELIMINA LA SCHEDA "DOMANI" DUPLICATA
# E IL SECONDO LOGO WS
# ============================================================

def clean_map(map_image):

    image = np.array(map_image)

    # Maschera per le zone da eliminare
    mask = np.zeros(
        image.shape[:2],
        dtype=np.uint8
    )

    # --------------------------------------------------------
    # 1. SCHEDA INTERNA:
    # "SICILIA / DOMANI / Mercoledì 19 agosto"
    # --------------------------------------------------------

    mask[5:75, 10:240] = 255

    # --------------------------------------------------------
    # 2. SECONDO LOGO WEATHER SICILY
    # --------------------------------------------------------

    mask[5:65, 880:988] = 255

    # Inpainting: ricostruisce lo sfondo
    # senza toccare il resto della mappa
    image_bgr = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    cleaned = cv2.inpaint(
        image_bgr,
        mask,
        15,
        cv2.INPAINT_NS
    )

    cleaned = cv2.cvtColor(
        cleaned,
        cv2.COLOR_BGR2RGB
    )

    return Image.fromarray(cleaned)


# ============================================================
# CREA IL FORMATO FINALE
# ============================================================

def format_weather_image(original):

    # --------------------------------------------------------
    # NORMALIZZA L'IMMAGINE
    # --------------------------------------------------------

    source = original.resize(
        (1080, 1350),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # 1. INTESTAZIONE
    #
    # Manteniamo completamente quella originale.
    #
    # Rimane quindi:
    # PREVISIONI SICILIA
    # DOMANI
    # giorno/data
    # UN SOLO LOGO WS
    # --------------------------------------------------------

    header = source.crop(
        (0, 0, 1080, 165)
    )

    # --------------------------------------------------------
    # 2. MAPPA
    #
    # Ritagliamo la parte utile della mappa.
    # La allarghiamo a tutta la larghezza.
    # --------------------------------------------------------

    map_source = source.crop(
        (46, 190, 1034, 790)
    )

    # Elimina:
    # - scheda giorno/data duplicata
    # - secondo logo
    map_source = clean_map(
        map_source
    )

    # Ingrandimento della mappa
    map_panel = map_source.resize(
        (1080, 670),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # 3. TEMPERATURE PER PROVINCIA
    #
    # Questo è il punto importante:
    # ritagliamo leggermente i bordi e ingrandiamo
    # la sezione per rendere le scritte più leggibili.
    # --------------------------------------------------------

    temperature_source = source.crop(
        (20, 845, 1060, 1275)
    )

    temperature_panel = temperature_source.resize(
        (1080, 500),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # 4. FOOTER
    # --------------------------------------------------------

    footer = source.crop(
        (0, 1330, 1080, 1350)
    )

    # --------------------------------------------------------
    # 5. CREA CANVAS FINALE
    # --------------------------------------------------------

    output = Image.new(
        "RGB",
        (1080, 1350),
        (7, 26, 49)
    )

    # Intestazione
    output.paste(
        header,
        (0, 0)
    )

    # Mappa ingrandita
    output.paste(
        map_panel,
        (0, 165)
    )

    # Temperature ingrandite
    output.paste(
        temperature_panel,
        (0, 835)
    )

    # Footer
    output.paste(
        footer,
        (0, 1330)
    )

    return output


# ============================================================
# INTERFACCIA STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Meteo Sicilia",
    page_icon="🌤️",
    layout="centered"
)


# Titolo
st.title("🌤️ Meteo Sicilia")

st.write(
    "Inserisci il link dell'immagine Weather Sicily "
    "oppure carica direttamente l'immagine."
)


# ============================================================
# LINK
# ============================================================

url = st.text_input(
    "🔗 Link dell'immagine",
    value=DEFAULT_URL
)


# ============================================================
# CARICAMENTO FILE
# ============================================================

uploaded_file = st.file_uploader(
    "📷 Oppure carica l'immagine dal telefono",
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
            "Sto preparando la grafica..."
        ):

            # Se l'utente ha caricato una foto,
            # utilizziamo quella.
            if uploaded_file is not None:

                original = Image.open(
                    uploaded_file
                ).convert("RGB")

            else:

                # Altrimenti scarichiamo dal link
                original = download_image(
                    url
                )

            # Trasformazione
            result = format_weather_image(
                original
            )

        # ----------------------------------------------------
        # RISULTATO
        # ----------------------------------------------------

        st.success(
            "✅ Immagine pronta!"
        )

        st.image(
            result,
            caption="Anteprima finale",
            use_container_width=True
        )

        # ----------------------------------------------------
        # DOWNLOAD PNG
        # ----------------------------------------------------

        buffer = io.BytesIO()

        result.save(
            buffer,
            format="PNG",
            optimize=True
        )

        st.download_button(
            label="⬇️ SCARICA PNG",
            data=buffer.getvalue(),
            file_name="meteo_sicilia_formattato.png",
            mime="image/png",
            use_container_width=True
        )

    except Exception as error:

        st.error(
            "❌ Non riesco a elaborare l'immagine."
        )

        st.code(
            str(error)
        )


# ============================================================
# INFORMAZIONI
# ============================================================

st.divider()

st.caption(
    "Formato finale: 1080 × 1350 px • "
    "Meteo Sicilia Formatter"
)
