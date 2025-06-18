import streamlit as st
import cv2
import numpy as np
from PIL import Image

def apply_clahe(image, clip_limit, tile_grid_size):
    """
    Berilgan tasvirga CLAHE (Contrast Limited Adaptive Histogram Equalization) algoritmini qo'llaydi.
    Args:
        image (numpy.ndarray): Qayta ishlanadigan tasvir.
        clip_limit (float): Kontrastni cheklovchi chegarasi.
        tile_grid_size (int): Tasvirni bo'linadigan panjara hajmi (en va bo'yi uchun).

    Returns:
        numpy.ndarray: CLAHE qo'llanilgan tasvir.
    """
    if len(image.shape) == 3: # Agar tasvir rangli bo'lsa
        # Rangli tasvirlar uchun YCbCr rang maydoniga o'tkazish
        ycbcr_image = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        y_channel = ycbcr_image[:,:,0] # Y kanalini ajratib olish
    else: # Agar tasvir kulrang bo'lsa
        y_channel = image

    # CLAHE ob'ektini yaratish
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_grid_size, tile_grid_size))

    # Y kanaliga CLAHE qo'llash
    clahe_applied_y_channel = clahe.apply(y_channel)

    if len(image.shape) == 3:
        # Y kanalini qayta birlashtirish
        ycbcr_image[:,:,0] = clahe_applied_y_channel
        # Qayta ishlangan tasvirni RGB ga qaytarish
        processed_image = cv2.cvtColor(ycbcr_image, cv2.COLOR_YCrCb2RGB)
    else:
        processed_image = clahe_applied_y_channel

    return processed_image

st.set_page_config(layout="wide", page_title="CLAHE Tasvirni Yaxshilash Dasturi")

st.title("Contrast Limited Adaptive Histogram Equalization (CLAHE)")
st.write("Tasvirni yuklang va `Clip Limit` hamda `Tile Grid Size` qiymatlarini o'zgartirib, kontrastni yaxshilang.")

# Tasvirni yuklash qismi
uploaded_file = st.file_uploader("Tasvirni yuklang...", type=["jpg", "jpeg", "png", "bmp", "tiff"])

if uploaded_file is not None:
    # Faylni PIL Image ob'ektiga aylantirish
    image = Image.open(uploaded_file)
    # PIL Image ni OpenCV ga mos numpy massiviga aylantirish (RGB formatida)
    img_array = np.array(image.convert('RGB'))

    # Parametrlarni sozlash uchun slayderlar
    st.sidebar.header("CLAHE Parametrlari")
    clip_limit = st.sidebar.slider(
        "Clip Limit (Kontrast chegarasi)",
        min_value=0.01,
        max_value=10.0,
        value=2.0,
        step=0.01,
        help="Bu qiymat kontrastni oshirishda cheklov vazifasini bajaradi. Yuqori qiymatlar kuchliroq kontrast beradi, lekin shovqinni ham kuchaytirishi mumkin."
    )
    tile_grid_size = st.sidebar.slider(
        "Tile Grid Size (Panjara hajmi)",
        min_value=2,
        max_value=32,
        value=8,
        step=1,
        help="Bu qiymat tasvirning qanday kattalikdagi bo'laklarga bo'linishini belgilaydi. Kichikroq qiymatlar lokalroq, kattaroq qiymatlar esa globalroq natija beradi."
    )

    st.subheader("Natijalar")

    col1, col2 = st.columns(2)

    with col1:
        st.image(img_array, caption="Asl tasvir", use_column_width=True)

    # CLAHE algoritmini qo'llash
    processed_img_array = apply_clahe(img_array, clip_limit, tile_grid_size)

    with col2:
        st.image(processed_img_array, caption=f"CLAHE qo'llanilgan tasvir (Clip Limit: {clip_limit}, Tile Grid Size: {tile_grid_size})", use_column_width=True)

    st.markdown("""
    ---
    ### CLAHE (Contrast Limited Adaptive Histogram Equalization) haqida
    CLAHE - bu tasvir kontrastini yaxshilash uchun ishlatiladigan kuchli algoritmdir. Oddiy gistogramma tenglashishidan farqli o'laroq, CLAHE butun tasvirni bir martada emas, balki kichik "panjara" (tiles) ga bo'lib, har bir bo'lakka alohida gistogramma tenglashishini qo'llaydi. Bu lokal kontrastni yaxshilashga yordam beradi va to'liq yorqinligi bir xil bo'lmagan tasvirlar uchun juda foydali.

    - **`Clip Limit`**: Bu parametr gistogrammadagi har bir bin (yoki chastota) ni qancha yuqoriga ko'tarish mumkinligini cheklaydi. Agar biror bin shu chegaradan oshib ketsa, qolgan qiymatlar boshqa binlarga teng taqsimlanadi. Bu, kontrastni haddan tashqari oshirib yuborish va shovqinni kuchaytirishning oldini oladi.
    - **`Tile Grid Size`**: Bu parametr tasvirning qancha bo'laklarga bo'linishini belgilaydi (masalan, `8x8` panjara). Har bir bo'lak o'zining gistogrammasini mustaqil ravishda tenglashtiradi. Kichikroq panjara hajmi ko'proq lokal tafsilotlarni saqlashga yordam beradi, kattaroq panjara esa globalroq o'zgarishlarni tekislaydi.
    """)
else:
    st.info("Boshlash uchun yuqoridagi 'Tasvirni yuklang...' tugmasi orqali tasvir yuklang.")