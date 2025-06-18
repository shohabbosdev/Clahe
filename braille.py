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

# Morfologik "ochilish" (Opening) operatsiyasini qo'llash
def apply_morphological_opening(image, kernel_size):
    """
    Applies morphological opening operation to the binarized image.
    This helps to remove small objects (noise) and smooth contours.

    Args:
        image (numpy.ndarray): The binarized image.
        kernel_size (int): Size of the kernel for erosion and dilation. Must be an odd number.

    Returns:
        numpy.ndarray: Image after morphological opening.
    """
    if kernel_size % 2 == 0: # Kernel hajmi toq son bo'lishini ta'minlash
        kernel_size += 1
    
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # Eroziya: kichik obyektlarni olib tashlaydi
    eroded_image = cv2.erode(image, kernel, iterations=1)
    
    # Dilatasiya: yo'qolgan haqiqiy obyektlarni tiklaydi
    dilated_image = cv2.dilate(eroded_image, kernel, iterations=1)
    
    return dilated_image

st.set_page_config(layout="wide", page_title="Brayl Tasviri uchun Binarizatsiya Dasturi")

st.title("Brayl Tasviri uchun Binarizatsiya va Morfologik Filterlash")
st.write("Tasvirni yuklang va uni Otsu, qo'lda yoki adaptiv usullar yordamida binarizatsiya qiling. So'ngra, orqa tomondagi nuqtalarni (shovqinni) filtrlash uchun morfologik operatsiyalarni qo'llang.")
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
            "Block Size (Blok hajmi) (g'alati son bo'lishi kerak)",
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

    # Binarizatsiya natijasini olish
    binarized_img, threshold_info_text, grayscale_img = apply_binarization(
        img_array,
        method=method_to_pass,
        manual_threshold=manual_threshold_value,
        block_size=block_size_value,
        C_value=C_value_value,
        adaptive_method="gaussian" if adaptive_threshold_type == "Gaussiy (Gaussian)" else "mean"
    )

    st.sidebar.header("Morfologik Operatsiyalar (Shovqinni Filtrlash)")
    apply_morphology = st.sidebar.checkbox("Morfologik filtrlashni qo'llash", value=True, help="Binarizatsiyadan so'ng kichik shovqin nuqtalarini (masalan, orqa tomondagi Braille nuqtalarini) olib tashlash uchun 'ochilish' operatsiyasini qo'llaydi.")
    
    if apply_morphology:
        kernel_size_morph = st.sidebar.slider(
            "Morfologik Kernel Hajmi",
            min_value=1,
            max_value=9,
            value=3,
            step=2, # Faqat toq sonlarni ta'minlash
            help="Morfologik operatsiyalar uchun kernel (struktura elementi) hajmi. Kichik qiymatlar kamroq shovqinni olib tashlaydi, katta qiymatlar esa haqiqiy nuqtalarni ham buzishi mumkin."
        )
        final_processed_img = apply_morphological_opening(binarized_img, kernel_size_morph)
        morph_caption = f"Morfologik 'ochilish' qo'llanilgan tasvir (Kernel: {kernel_size_morph})"
    else:
        final_processed_img = binarized_img
        morph_caption = "Morfologik filtrlash qo'llanilmagan"


    st.subheader("Natijalar")

    col1, col2 = st.columns(2)

    with col1:
        st.image(grayscale_img, caption="Kulrang tasvir", use_column_width=True)
        st.info(f"Ishlatilgan chegara ma'lumotlari: {threshold_info_text}")


    with col2:
        st.image(final_processed_img, caption=f"Binarizatsiya qilingan Brayl tasviri ({binarization_method_choice}) va {morph_caption}", use_column_width=True)

    st.markdown("""
    ---
    ### Binarizatsiya haqida

    **Binarizatsiya** - bu tasvirni faqat ikki xil piksel qiymatiga ega bo'lgan (odatda qora va oq) tasvirga aylantirish jarayoni. Bu tasvirdagi obyektlar (masalan, Brayl nuqtalari) va fonni aniq ajratish uchun muhim qadamdir.

    - **Otsu binarizatsiyasi** - bu tasvirning umumiy gistogrammasini tahlil qilib, tasvirdagi ikki asosiy guruh (masalan, fon va oldingi plan) o'rtasidagi farqni maksimal darajada oshiradigan optimal chegara qiymatini topadigan avtomatik usul. Bu, ayniqsa, ikkita aniq cho'qqi (moda) mavjud bo'lgan gistogrammali tasvirlar uchun samarali.

    - **Qo'lda chegara belgilash** - bu foydalanuvchi tasvirni binarizatsiya qilish uchun ma'lum bir piksel qiymatini (0 dan 255 gacha) chegara sifatida belgilashini anglatadi. Bu qiymatdan past bo'lgan barcha piksellar qora (0) bo'ladi, yuqori bo'lganlar esa oq (255) bo'ladi. Bu usul, agar siz tasvirning yorqinlik xususiyatlarini aniq bilsangiz yoki eksperiment qilishni istasangiz foydalidir.

    - **Adaptiv Binarizatsiya** - bu tasvirni kichik bo'laklarga (bloklarga) bo'lib, har bir bo'lak uchun alohida chegara qiymatini hisoblaydigan usul. Bu, ayniqsa, tasvirda yorug'lik sharoitlari bir xil bo'lmaganda yoki gradyentlar mavjud bo'lganda juda foydalidir. Adaptiv usullar global chegara topish o'rniga, har bir lokal mintaqaga moslashadi.
        - **Gaussiy (Gaussian)**: Chegara qiymati qo'shni piksellarning og'irlikdagi o'rtacha qiymati (Gaussiy oynasi bo'yicha) asosida hisoblanadi. Bu usul shovqinga kamroq sezgir.
        - **O'rtacha (Mean)**: Chegara qiymati qo'shni piksellarning oddiy o'rtacha qiymati asosida hisoblanadi.

    ---
    ### Morfologik Operatsiyalar (Shovqinni Filtrlash)

    **Morfologik "Ochilish" (Opening)** - bu binarizatsiya qilingan tasvirlarda kichik shovqinlarni (nuqtalarni) olib tashlash va obyektlarning silliq konturlarini saqlash uchun ishlatiladigan samarali usul. U ikki asosiy morfologik operatsiyani ketma-ket qo'llashdan iborat:

    1.  **Eroziya (Erosion)**: Tasvirdagi oldingi plan piksellarini (Braille nuqtalarini) "yemirib", kichik obyektlarni butunlay yo'q qiladi. Bu orqa tomondagi zaif yoki kichik nuqtalarni o'chirishga yordam beradi.
    2.  **Dilatasiya (Dilation)**: Eroziyadan so'ng qo'llaniladi. Yo'qotilgan piksellarni (faqat haqiqiy Braille nuqtalaridan yo'qolgan qismlarni) qaytaradi va Braille nuqtalarini yana asl hajmiga yaqinlashtiradi. Bu eroziya natijasida o'chirilishi mumkin bo'lgan haqiqiy nuqtalarning uzilishlarini ham to'g'irlashi mumkin.

    **Qanday yordam beradi (Brayl tasvirlari uchun):**
    Agar sizning Brayl tasvirlaringizda qog'ozning orqa tomonidan ko'rinib turgan kichik, zaif nuqtalar yoki tasvirga tushgan boshqa shovqinlar bo'lsa, morfologik "ochilish" bu kichik obyektlarni avtomatik ravishda olib tashlashi mumkin, shu bilan birga haqiqiy Braille nuqtalarini saqlab qoladi. Siz `Morfologik Kernel Hajmi` slayderidan foydalanib, qancha shovqinni olib tashlashni boshqarishingiz mumkin. Kichikroq kernel kichikroq shovqinni, kattaroq kernel esa kattaroq shovqinni olib tashlaydi, lekin ehtiyot bo'lish kerak, juda katta kernel haqiqiy Braille nuqtalarini ham buzishi mumkin.
    """)
else:
    st.info("Boshlash uchun yuqoridagi 'Tasvirni yuklang...' tugmasi orqali Brayl tasvirini yuklang.")
