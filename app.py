import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
import io

st.set_page_config(page_title="Orka Fiş Asistanı", layout="wide")
st.title("🚀 Orka Hatasız Fiş Dönüştürücü")

# Kullanıcıdan Manuel Tarih Girişi (Hataları önlemek için)
secilen_tarih = st.date_input("Fişlerin Tarihini Seçin (Otomatik düzeltme için)", pd.to_datetime("today"))
formatli_tarih = secilen_tarih.strftime("%d.%m.%Y")

uploaded_files = st.file_uploader("Fiş Fotoğraflarını Seçin", accept_multiple_files=True)

def analiz_et(file, sabitle_tarih):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img, lang='tur')
        
        # TUTAR BULMA
        fiyatlar = re.findall(r'(\d+[\.,]\d{2})', text)
        tutar = max([float(f.replace(',', '.')) for f in fiyatlar]) if fiyatlar else 0.0
        
        # BELGE NO BULMA
        b_no_match = re.search(r'(\d{7,})', text)
        b_no = b_no_match.group(1) if b_no_match else "0001"
        
        if tutar <= 0: return []
        matrah = round(tutar / 1.01, 2)
        kdv = round(tutar - matrah, 2)
        
        return [
            [sabitle_tarih, '153.01.001', 'Mal Alimi', matrah, 0, f"'{b_no}", 'F'],
            [sabitle_tarih, '191.01.001', 'KDV %1', kdv, 0, f"'{b_no}", 'F'],
            [sabitle_tarih, '100.01.001', 'Nakit Odeme', 0, tutar, f"'{b_no}", 'F']
        ]
    except: return []

if uploaded_files:
    data = []
    for f in uploaded_files:
        data.extend(analiz_et(f, formatli_tarih))
    
    if data:
        df = pd.DataFrame(data, columns=['Tarih', 'Hesap_Kod', 'Aciklama', 'Borc', 'Alacak', 'Belge_No', 'Belge_Turu'])
        st.subheader("Önizleme (Orka'ya Uygun)")
        st.table(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button("📥 HATASIZ EXCEL'İ İNDİR", output.getvalue(), "Orka_Aktarim.xlsx")
