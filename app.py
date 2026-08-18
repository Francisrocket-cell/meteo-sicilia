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
    "midnight-20260818T005707-1317182/sicilia-social-icone.png"
    "?v=1787007429"
)


# ============================================================
# SCARICA IMMAGINE
# ============================================================

def download_image(url):

    parsed = urlparse(url.strip())

    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            "Il link deve iniziare con http:// oppure https://"
        )

    host = (parsed.hostname or "").lower()

    if not (
        host == "weathersicily.it"
        or host.endswith(".weathersicily.it")
    ):
        raise ValueError(
            "Per sicurezza questa app accetta solo immagini "
            "provenienti da weathersicily.it"
        )

    response = requests.get(
        url.strip(),
        timeout=30,
        headers={
            "User-Agent": "MeteoSiciliaFormatter/1.0"
        },
    )

    response.raise_for_status()

    return Image.open(
        io.BytesIO(response.content)
    ).convert("RGB")


# ============================================================
# ELIMINA I DUPLICATI
# ============================================================

def remove_duplicates(image):

    """
    Rimuove dalla parte della mappa:
    - la seconda data/giorno
    - il secondo logo

    Il logo principale nell'intestazione rimane.
    """

    arr = np.array(image)

    mask = np.zeros(
        arr.shape[:2],
        dtype=np.uint8
    )

    # Seconda scritta del giorno/data
    mask[5:75, 10:240] = 255

    # Secondo logo
    mask[5:65, 880:970] = 255

    image_bgr = cv2.cvtColor(
        arr,
        cv2.COLOR_RGB2BGR
    )

    repaired = cv2.inpaint(
        image_bgr,
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
# CREA LA NUOVA GRAFICA
# ============================================================

def format_weather_image(source):

    # Uniformiamo l'immagine alla dimensione originale
    source = source.resize(
        (OUTPUT_WIDTH, OUTPUT_HEIGHT),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    header = source.crop(
        (0, 0, 1080, 165)
    )

    # --------------------------------------------------------
    # MAPPA
    # --------------------------------------------------------

    map_source = source.crop(
        (46, 190, 1034, 790)
    )

    map_source = remove_duplicates(
        map_source
    )

    map_panel = map_source.resize(
        (1080, 640),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------------

    temperature_panel = source.crop(
        (0, 835, 1080, 1270)
    )

    temperature_panel = temperature_panel.resize(
        (1080, 500),
        Image.Resampling.LANCZOS
    )

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    footer = source.crop(
        (0, 1305, 1080, 1350)
    )

    # --------------------------------------------------------
    # COMPOSIZIONE
    # --------------------------------------------------------

    output = Image.new(
        "RGB",
        (1080, 1350),
        (7, 27, 47)
    )

    output.paste(
        header,
        (0, 0)
    )

    output.paste(
        map_panel,
        (0, 165)
    )

    output.paste(
        temperature_panel,
        (0, 805)
    )

    output.paste(
        footer,
        (0, 1305)
    )

    return output


# ============================================================
# INTERFACCIA
# ============================================================

st.set_page_config(
    page_title="Meteo Sicilia",
    page_icon="🌤️",
    layout="centered"
)


st.title("🌤️ Meteo Sicilia")

st.write(
    "Incolla il link dell'immagine giornaliera "
    "Weather Sicily e premi GENERA."
)


url = st.text_input(
    "🔗 Link immagine",
    value=DEFAULT_URL
)


uploaded_file = st.file_uploader(
    "Oppure carica direttamente l'immagine",
    type=[
        "png",
        "jpg",
        "jpeg"
    ]
)


generate = st.button(
    "✨ GENERA IMMAGINE",
    use_container_width=True
)


# ============================================================
# ELABORAZIONE
# ============================================================

if generate:

    try:

        with st.spinner(
            "Sto preparando la grafica..."
        ):

            # Se viene caricata una foto,
            # utilizziamo quella.
            if uploaded_file is not None:

                original = Image.open(
                    uploaded_file
                ).convert("RGB")

            else:

                original = download_image(
                    url
                )

            result = format_weather_image(
                original
            )


        st.success(
            "Immagine pronta!"
        )


        st.image(
            result,
            caption="Anteprima",
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
            file_name="meteo_sicilia.png",
            mime="image/png",
            use_container_width=True
        )


    except Exception as error:

        st.error(
            "Si è verificato un errore:"
        )

        st.code(
            str(error)
        )


# ============================================================
# INFO
# ============================================================

st.divider()

st.caption(
    "Meteo Sicilia Formatter • "
    "Formato 1080 × 1350 px"
)
