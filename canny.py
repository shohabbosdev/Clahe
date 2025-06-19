import streamlit as st
import cv2
import numpy as np

# Tasvirni yuklash
st.title("Brayl Tasvirini Orientatsiya Rostlash")
uploaded_file = st.file_uploader("Tasvirni yuklang (.jpg, .png)", type=["jpg", "png"])
st.latex(r"""
         I_{silliqlash}(x,y)=\frac{1}{2\pi\sigma^2}e^{-\frac{x^2+y^2}{2\sigma^2}}\cdot I(x,y)
         """)
if uploaded_file is not None:
    # Tasvirni o'qish
    img = cv2.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
    
    # Canny edge detection
    edges = cv2.Canny(img, 50, 150)
    
    # Hough transformatsiyasi
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, minLineLength=50, maxLineGap=10)
    theta_avg = 0
    if lines is not None:
        thetas = [np.arctan2(line[0][3] - line[0][1], line[0][2] - line[0][0]) * 180/np.pi for line in lines]
        theta_avg = np.mean(thetas) if thetas else 0
    
    # Rotatsiya
    if theta_avg != 0:
        M = cv2.getRotationMatrix2D((img.shape[1]/2, img.shape[0]/2), -theta_avg, 1)
        rotated_img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
    else:
        rotated_img = img
    
    # Natijani ko'rsatish
    st.image([img, edges, rotated_img], caption=['Asl tasvir', 'Edge aniqlash', 'Rostlangan tasvir'], channels="GRAY")
    st.write(f"Og'ish burchagi: {theta_avg:.2f} daraja")