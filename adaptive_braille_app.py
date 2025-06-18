import streamlit as st
import cv2
import numpy as np
from PIL import Image

def apply_binarization(image_array, method="otsu", manual_threshold=127, block_size=11, C_value=2, adaptive_method="gaussian"):
    """
    Applies binarization to a given image using either Otsu's method, a manual threshold, or adaptive methods.
    If the image is colored, it is first converted to grayscale.

    Args:
        image_array (numpy.ndarray): The input image (can be grayscale or color).
        method (str): Binarization method. Can be "otsu", "manual", or "adaptive".
        manual_threshold (int): The threshold value to use if method is "manual".
        block_size (int): Size of a pixel neighborhood that is used to calculate a threshold value for the pixel.
                          Must be an odd number.
        C_value (int): Constant subtracted from the mean or weighted mean.
        adaptive_method (str): Type of adaptive thresholding. Can be "gaussian" or "mean".

    Returns:
        tuple: A tuple containing:
            - numpy.ndarray: The binarized image.
            - str: Information about the threshold value used (Otsu's, manual, or adaptive parameters).
            - numpy.ndarray: The grayscale version of the input image.
    """
    # Tasvir rangli bo'lsa, kulrang tasvirga aylantirish
    if len(image_array.shape) == 3:
        grayscale_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    else:
        grayscale_image = image_array

    binarized_image = None
    used_threshold_info = ""

    if method == "otsu":
        # Otsu binarizatsiyasini qo'llash
        ret, binarized_image = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        used_threshold_info = f"Otsu tomonidan hisoblangan: **{ret:.2f}**"
    elif method == "manual":
        # Qo'lda binarizatsiyani qo'llash
        ret, binarized_image = cv2.threshold(grayscale_image, manual_threshold, 255, cv2.THRESH_BINARY)
        used_threshold_info = f"Qo'lda belgilangan: **{manual_threshold}**"
    elif method == "adaptive":
        # Adaptiv binarizatsiyani qo'llash
        if adaptive_method == "gaussian":
            # ADAPTIVE_THRESH_GAUSSIAN_C: chegara qiymati qo'shni piksellarning og'irlikdagi o'rtacha qiymati (Gaussiy oynasi bo'yicha).
            binarized_image = cv2.adaptiveThreshold(
                grayscale_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, block_size, C_value
            )
            used_threshold_info = f"Adaptiv (Gauss): Block Size **{block_size}**, C **{C_value}**"
        elif adaptive_method == "mean":
            # ADAPTIVE_THRESH_MEAN_C: chegara qiymati qo'shni piksel blokining o'rtacha qiymati.
            binarized_image = cv2.adaptiveThreshold(
                grayscale_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY, block_size, C_value
            )
            used_threshold_info = f"Adaptiv (O'rtacha): Block Size **{block_size}**, C **{C_value}**"
    else:
        # Default holat yoki xato
        binarized_image = grayscale_image
        used_threshold_info = "Hech qanday binarizatsiya qo'llanilmagan"


    return binarized_image, used_threshold_info, grayscale_image

st.set_page_config(layout="wide", page_title="Brayl Tasviri uchun Binarizatsiya Dasturi")

st.title("Brayl Tasviri uchun Binarizatsiya")
st.write("Tasvirni yuklang va uni Otsu, qo'lda yoki adaptiv usullar yordamida binarizatsiya qiling.")
st.write("Adaptiv binarizatsiya tasvirning har bir kichik mintaqasi uchun alohida chegara hisoblab, yorug'lik sharoitlari notekis bo'lgan hollarda juda samaralidir.")

# Tasvirni yuklash qismi
uploaded_file = st.file_uploader("Tasvirni yuklang...", type=["jpg", "jpeg", "png", "bmp", "tiff"])

if uploaded_file is not None:
    # Yuklangan faylni PIL Image ob'ektiga aylantirish
    image_pil = Image.open(uploaded_file)
    # PIL Image ni OpenCV ga mos numpy massiviga aylantirish (RGB formatida)
    img_array = np.array(image_pil.convert('RGB'))

    st.sidebar.header("Binarizatsiya Usulini Tanlang")
    binarization_method_choice = st.sidebar.radio(
        "Qaysi binarizatsiya usulidan foydalanmoqchisiz?",
        ("Otsu (Avtomatik)", "Qo'lda Chegara", "Adaptiv Binarizatsiya")
    )

    # Parametrlarni boshlang'ich qiymatlar bilan initsializatsiya qilish
    manual_threshold_value = 127
    block_size_value = 11
    C_value_value = 2
    adaptive_threshold_type = "gaussian"

    if binarization_method_choice == "Qo'lda Chegara":
        method_to_pass = "manual"
        manual_threshold_value = st.sidebar.slider(
            "Chegara Qiymati (0 dan 255 gacha)",
            min_value=0,
            max_value=255,
            value=127,
            step=1,
            help="Tasvirni binarizatsiya qilish uchun qo'lda chegara qiymatini tanlang. Bu qiymatdan past piksellar qora, yuqori piksellar oq bo'ladi."
        )
    elif binarization_method_choice == "Adaptiv Binarizatsiya":
        method_to_pass = "adaptive"
        adaptive_threshold_type = st.sidebar.radio(
            "Adaptiv usul turi:",
            ("Gaussiy (Gaussian)", "O'rtacha (Mean)")
        )
        block_size_value = st.sidebar.slider(
            "Block Size (Blok hajmi) (tub son bo'lishi kerak)",
            min_value=3,
            max_value=101, # Kengroq diapazon uchun maksimal qiymatni oshirdik
            value=11,
            step=2, # Faqat toq sonlarni ta'minlash
            help="Har bir piksel uchun chegara qiymatini hisoblashda qo'llaniladigan qo'shni piksel blokining o'lchami. Har doim toq son bo'lishi kerak."
        )
        C_value_value = st.sidebar.slider(
            "C qiymati (O'zgarmas)",
            min_value=-10,
            max_value=10,
            value=2,
            step=1,
            help="O'rtacha yoki og'irlikdagi o'rtacha qiymatidan ayiriladigan doimiy. Manfiy qiymatlar natijani yorqinlashtiradi, musbat qiymatlar esa qorong'ulashtiradi."
        )
    else: # Otsu (Avtomatik)
        method_to_pass = "otsu"

    st.subheader("Natijalar")

    col1, col2 = st.columns(2)

    # Tanlangan usulga qarab binarizatsiyani qo'llash
    binarized_img, threshold_info_text, grayscale_img = apply_binarization(
        img_array,
        method=method_to_pass,
        manual_threshold=manual_threshold_value,
        block_size=block_size_value,
        C_value=C_value_value,
        adaptive_method="gaussian" if adaptive_threshold_type == "Gaussiy (Gaussian)" else "mean"
    )

    with col1:
        st.image(grayscale_img, caption="Kulrang tasvir", use_column_width=True)
        st.info(f"Ishlatilgan chegara ma'lumotlari: {threshold_info_text}")


    with col2:
        st.image(binarized_img, caption=f"Binarizatsiya qilingan Brayl tasviri ({binarization_method_choice})", use_column_width=True)

    st.markdown("""
    ---
    ### Binarizatsiya haqida

    **Binarizatsiya** - bu tasvirni faqat ikki xil piksel qiymatiga ega bo'lgan (odatda qora va oq) tasvirga aylantirish jarayoni. Bu tasvirdagi obyektlar (masalan, Brayl nuqtalari) va fonni aniq ajratish uchun muhim qadamdir.

    - **Otsu binarizatsiyasi** - bu tasvirning umumiy gistogrammasini tahlil qilib, tasvirdagi ikki asosiy guruh (masalan, fon va oldingi plan) o'rtasidagi farqni maksimal darajada oshiradigan optimal chegara qiymatini topadigan avtomatik usul. Bu, ayniqsa, ikkita aniq cho'qqi (moda) mavjud bo'lgan gistogrammali tasvirlar uchun samarali.

    - **Qo'lda chegara belgilash** - bu foydalanuvchi tasvirni binarizatsiya qilish uchun ma'lum bir piksel qiymatini (0 dan 255 gacha) chegara sifatida belgilashini anglatadi. Bu qiymatdan past bo'lgan barcha piksellar qora (0) bo'ladi, yuqori bo'lganlar esa oq (255) bo'ladi. Bu usul, agar siz tasvirning yorqinlik xususiyatlarini aniq bilsangiz yoki eksperiment qilishni istasangiz foydalidir.

    - **Adaptiv Binarizatsiya** - bu tasvirni kichik bo'laklarga (bloklarga) bo'lib, har bir bo'lak uchun alohida chegara qiymatini hisoblaydigan usul. Bu, ayniqsa, tasvirda yorug'lik sharoitlari bir xil bo'lmaganda yoki gradyentlar mavjud bo'lganda juda foydalidir. Adaptiv usullar global chegara topish o'rniga, har bir lokal mintaqaga moslashadi.
        - **Gaussiy (Gaussian)**: Chegara qiymati qo'shni piksellarning og'irlikdagi o'rtacha qiymati (Gaussiy oynasi bo'yicha) asosida hisoblanadi. Bu usul shovqinga kamroq sezgir.
        - **O'rtacha (Mean)**: Chegara qiymati qo'shni piksellarning oddiy o'rtacha qiymati asosida hisoblanadi.

    **Brayl tasvirlari uchun ahamiyati:**
    Brayl tasvirlarida nuqtalar odatda fondan qorong'iroq yoki yorug'roq bo'ladi. Binarizatsiya bu kontrastdan foydalanib, nuqtalarni fondan ajratishga yordam beradi. Adaptiv binarizatsiya, ayniqsa, Brayl tasvirlari skanerlanganda yoki yorug'lik sharoitlari notekis bo'lgan hollarda juda samaralidir, chunki u har bir mintaqadagi nuqtalarni yaxshiroq ajratib olishga imkon beradi.
    """)
else:
    st.info("Boshlash uchun yuqoridagi 'Tasvirni yuklang...' tugmasi orqali Brayl tasvirini yuklang.")

