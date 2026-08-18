import io
import requests
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Meteo Sicilia Formatter", page_icon="🌤️", layout="centered")

st.title("🌤️ Meteo Sicilia Formatter")

uploaded_file = st.file_uploader("📁 1. Carica l'immagine dal telefono:", type=["png", "jpg", "jpeg"])
st.markdown("<p style='text-align: center; color: gray; margin: 0;'>— OPPURE —</p>", unsafe_allow_html=True)
url = st.text_input("🔗 2. Incolla l'URL dell'immagine:", placeholder="https://...")

def process_meteo_image(img):
    w, h = img.size
    
    # Sfondo blu scuro originale (#081A2C)
    bg_color = (8, 26, 44, 255)
    canvas = Image.new("RGBA", (1080, 1350), bg_color)

    # 1. INTESTAZIONE (Titolo + Logo WS)
    header = img.crop((0, 0, w, int(h * 0.13)))
    h_ratio = 1080 / header.width
    header_resized = header.resize((1080, int(header.height * h_ratio)), Image.Resampling.LANCZOS)
    canvas.paste(header_resized, (0, 0))

    # 2. MAPPA CENTRALE (Mantiene tutti i dettagli, mare e icone intatti)
    map_box = img.crop((0, int(h * 0.13), w, int(h * 0.615)))
    m_ratio = 1040 / map_box.width
    map_resized = map_box.resize((1040, int(map_box.height * m_ratio)), Image.Resampling.LANCZOS)
    canvas.paste(map_resized, (20, 175))

    # 3. GRIGLIA TEMPERATURE
    temp_grid = img.crop((0, int(h * 0.615), w, int(h * 0.96)))
    g_ratio = 1080 / temp_grid.width
    grid_resized = temp_grid.resize((1080, int(temp_grid.height * g_ratio)), Image.Resampling.LANCZOS)
    canvas.paste(grid_resized, (0, 810))

    # 4. FOOTER (weathersicily.it)
    footer = img.crop((0, int(h * 0.96), w, h))
    f_ratio = 1080 / footer.width
    footer_resized = footer.resize((1080, int(footer.height * f_ratio)), Image.Resampling.LANCZOS)
    canvas.paste(footer_resized, (0, 1300))

    return canvas

if st.button("GENERA NUOVA GRAFICA", type="primary", use_container_width=True):
    raw_img = None
    if uploaded_file is not None:
        try:
            raw_img = Image.open(uploaded_file).convert("RGBA")
        except Exception as e:
            st.error(f"Errore nella lettura del file: {e}")
    elif url.strip():
        with st.spinner("Scaricamento immagine da URL in corso..."):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                res = requests.get(url.strip(), headers=headers, timeout=12)
                if res.status_code == 200:
                    raw_img = Image.open(io.BytesIO(res.content)).convert("RGBA")
                else:
                    st.error(f"Errore di scaricamento: {res.status_code}")
            except Exception as e:
                st.error(f"Errore durante il download: {e}")
    else:
        st.warning("Carica un'immagine oppure inserisci un URL.")

    if raw_img is not None:
        with st.spinner("Elaborazione in corso..."):
            try:
                final_img = process_meteo_image(raw_img)
                st.success("Grafica generata con successo!")
                st.image(final_img, use_container_width=True)

                buf = io.BytesIO()
                final_img.save(buf, format="PNG", quality=100)
                buf.seek(0)

                st.download_button(
                    label="⬇️ SCARICA PNG (1080x1350)",
                    data=buf,
                    file_name="meteo_sicilia_formatted.png",
                    mime="image/png",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Errore durante l'elaborazione: {e}")
