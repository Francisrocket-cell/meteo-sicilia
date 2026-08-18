import io
import requests
import streamlit as st
from PIL import Image, ImageDraw

st.set_page_config(page_title="Meteo Sicilia Formatter", page_icon="🌤️", layout="centered")

st.title("🌤️ Meteo Sicilia Formatter")

uploaded_file = st.file_uploader("📁 1. Carica l'immagine dal telefono:", type=["png", "jpg", "jpeg"])
st.markdown("<p style='text-align: center; color: gray; margin: 0;'>— OPPURE —</p>", unsafe_allow_html=True)
url = st.text_input("🔗 2. Incolla l'URL dell'immagine:", placeholder="https://...")

def process_meteo_image(img):
    w, h = img.size
    bg_color = (8, 26, 44, 255)
    canvas = Image.new("RGBA", (1080, 1350), bg_color)
    
    header = img.crop((0, 0, w, int(h * 0.13)))
    header_resized = header.resize((1080, int(header.height * (1080 / header.width))), Image.Resampling.LANCZOS)
    canvas.paste(header_resized, (0, 0))

    map_box = img.crop((int(w * 0.035), int(h * 0.135), int(w * 0.965), int(h * 0.61)))
    draw = ImageDraw.Draw(map_box)
    mw, mh = map_box.size
    
    draw.rectangle([int(mw * 0.02), int(mh * 0.01), int(mw * 0.28), int(mh * 0.14)], fill=bg_color)
    draw.rectangle([int(mw * 0.88), int(mh * 0.01), int(mw * 0.98), int(mh * 0.08)], fill=bg_color)

    map_resized = map_box.resize((1020, int(map_box.height * (1020 / map_box.width))), Image.Resampling.LANCZOS)
    canvas.paste(map_resized, (30, 175))

    temp_grid = img.crop((0, int(h * 0.62), w, int(h * 0.96)))
    grid_resized = temp_grid.resize((1080, int(temp_grid.height * (1080 / temp_grid.width))), Image.Resampling.LANCZOS)
    canvas.paste(grid_resized, (0, 810))

    footer = img.crop((0, int(h * 0.96), w, h))
    footer_resized = footer.resize((1080, int(footer.height * (1080 / footer.width))), Image.Resampling.LANCZOS)
    f_draw = ImageDraw.Draw(footer_resized)
    f_draw.rectangle([int(1080 * 0.60), 0, 1080, footer_resized.height], fill=bg_color)
    canvas.paste(footer_resized, (0, 1300))

    return canvas

if st.button("GENERA", type="primary", use_container_width=True):
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
                    st.error(f"Errore di scaricamento dal link: {res.status_code}")
            except Exception as e:
                st.error(f"Errore durante il download: {e}")
    else:
        st.warning("Per favore, carica un'immagine dal telefono oppure inserisci un URL.")

    if raw_img is not None:
        with st.spinner("Elaborazione immagine in corso..."):
            try:
                final_img = process_meteo_image(raw_img)
                st.success("Immagine ottimizzata con successo!")
                st.image(final_img, use_container_width=True)

                buf = io.BytesIO()
                final_img.save(buf, format="PNG", quality=100)
                buf.seek(0)

                st.download_button(
                    label="⬇️ SCARICA PNG",
                    data=buf,
                    file_name="meteo_sicilia_formatted.png",
                    mime="image/png",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Errore durante l'elaborazione grafica: {e}")
