import streamlit as st
import cv2
import numpy as np
from PIL import Image

def apply_binarization(image_array, method="otsu", manual_threshold=127):
    """
    Applies binarization to a given image using either Otsu's method or a manual threshold.
    If the image is colored, it is first converted to grayscale.

    Args:
        image_array (numpy.ndarray): The input image (can be grayscale or color).
        method (str): Binarization method. Can be "otsu" or "manual".
        manual_threshold (int): The threshold value to use if method is "manual".

    Returns:
        tuple: A tuple containing:
            - numpy.ndarray: The binarized image.
            - int: The threshold value actually used (Otsu's or manual).
            - numpy.ndarray: The grayscale version of the input image.
    """
    # Check if the image is colored and convert to grayscale if necessary
    if len(image_array.shape) == 3:
        grayscale_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        grayscale_image = image_array

    if method == "otsu":
        # Apply Otsu's binarization
        ret, binarized_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        used_threshold = ret
    else: # method == "manual"
        # Apply manual binarization
        ret, binarized_image = cv2.threshold(grayscale_image, manual_threshold, 255, cv2.THRESH_BINARY)
        used_threshold = manual_threshold

    return binarized_image, used_threshold, grayscale_image

st.set_page_config(layout="wide", page_title="Brayl Tasviri uchun Otsu/Qo'lda Binarizatsiya Dasturi")

st.title("Brayl Tasviri uchun Binarizatsiya")
st.write("Tasvirni yuklang va uni Otsu algoritmi yordamida avtomatik binarizatsiya qiling yoki chegara qiymatini qo'lda belgilang.")
st.write("Otsu binarizatsiyasi tasvirning gistogrammasiga asoslanib, fon va oldingi planni (Brayl nuqtalarini) ajratish uchun optimal chegara qiymatini avtomatik aniqlaydi.")

# Image upload section
uploaded_file = st.file_uploader("Tasvirni yuklang...", type=["jpg", "jpeg", "png", "bmp", "tiff"])

if uploaded_file is not None:
    # Open the uploaded file as a PIL Image
    image_pil = Image.open(uploaded_file)
    # Convert PIL Image to a numpy array for OpenCV processing (RGB format)
    img_array = np.array(image_pil.convert('RGB'))

    st.sidebar.header("Binarizatsiya Usulini Tanlang")
    binarization_method = st.sidebar.radio(
        "Qaysi binarizatsiya usulidan foydalanmoqchisiz?",
        ("Otsu (Avtomatik)", "Qo'lda Chegara")
    )

    manual_threshold_value = 127 # Default value for manual threshold
    if binarization_method == "Qo'lda Chegara":
        manual_threshold_value = st.sidebar.slider(
            "Chegara Qiymati (0 dan 255 gacha)",
            min_value=0,
            max_value=255,
            value=127,
            step=1,
            help="Tasvirni binarizatsiya qilish uchun qo'lda chegara qiymatini tanlang. Bu qiymatdan past piksellar qora, yuqori piksellar oq bo'ladi."
        )

    st.subheader("Natijalar")

    col1, col2 = st.columns(2)

    # Apply binarization based on selected method
    if binarization_method == "Otsu (Avtomatik)":
        binarized_img, threshold_value, grayscale_img = apply_binarization(img_array, method="otsu")
        threshold_info_text = f"Otsu tomonidan hisoblangan chegara qiymati: **{threshold_value:.2f}**"
        caption_text = "Otsu binarizatsiyasi qo'llanilgan Brayl tasviri"
    else:
        binarized_img, threshold_value, grayscale_img = apply_binarization(img_array, method="manual", manual_threshold=manual_threshold_value)
        threshold_info_text = f"Qo'lda belgilangan chegara qiymati: **{threshold_value}**"
        caption_text = f"Qo'lda binarizatsiya ({threshold_value}) qo'llanilgan Brayl tasviri"


    with col1:
        st.image(grayscale_img, caption="Kulrang tasvir", use_column_width=True)
        st.info(threshold_info_text)


    with col2:
        st.image(binarized_img, caption=caption_text, use_column_width=True)

    st.markdown("""
    ---
    ### Binarizatsiya haqida

    **Binarizatsiya** - bu tasvirni faqat ikki xil piksel qiymatiga ega bo'lgan (odatda qora va oq) tasvirga aylantirish jarayoni. Bu tasvirdagi obyektlar (masalan, Brayl nuqtalari) va fonni aniq ajratish uchun muhim qadamdir.

    - **Otsu binarizatsiyasi** - bu tasvirning umumiy gistogrammasini tahlil qilib, tasvirdagi ikki asosiy guruh (masalan, fon va oldingi plan) o'rtasidagi farqni maksimal darajada oshiradigan optimal chegara qiymatini topadigan avtomatik usul. Bu, ayniqsa, ikkita aniq cho'qqi (moda) mavjud bo'lgan gistogrammali tasvirlar uchun samarali.

    - **Qo'lda chegara belgilash** - bu foydalanuvchi tasvirni binarizatsiya qilish uchun ma'lum bir piksel qiymatini (0 dan 255 gacha) chegara sifatida belgilashini anglatadi. Bu qiymatdan past bo'lgan barcha piksellar qora (0) bo'ladi, yuqori bo'lganlar esa oq (255) bo'ladi. Bu usul, agar siz tasvirning yorqinlik xususiyatlarini aniq bilsangiz yoki eksperiment qilishni istasangiz foydalidir.

    **Brayl tasvirlari uchun ahamiyati:**
    Brayl tasvirlarida nuqtalar odatda fondan qorong'iroq yoki yorug'roq bo'ladi. Binarizatsiya bu kontrastdan foydalanib, nuqtalarni fondan ajratishga yordam beradi va matnni raqamli qayta ishlash uchun tayyorlaydi. Siz endi avtomatik Otsu algoritmidan foydalanishingiz yoki o'zingizning aniq talablaringizga mos keladigan chegara qiymatini qo'lda belgilashingiz mumkin.
    """)
else:
    st.info("Boshlash uchun yuqoridagi 'Tasvirni yuklang...' tugmasi orqali Brayl tasvirini yuklang.")
