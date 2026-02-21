import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
import io

# Tesseract yolunu ayarla (Streamlit Cloud için)
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

st.set_page_config(page_title="Orka Fiş Asistanı", layout="wide")
st.title("🚀 Orka Hatasız Fiş Dönüştürücü")
st.write("Fişleri yükleyin, gerisini bana bırakın.")

uploaded_files = st.file_uploader("Fiş Fotoğraflarını Seçin", accept_multiple_files=True)

def analiz_et(file):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img, lang='tur')
        
        # TARİH DÜZELTME (2026'ya zorla)
        gun_ay = re.search(r'(\d{2})[./](\d{2})', text)
        tarih = f"{gun_ay.group(1)}.{gun_ay.group(2)}.2026" if gun_ay else "21.02.2026"
        
        # TUTAR VE BELGE NO (Hatasız)
        fiyatlar = re.findall(r'(\d+[\.,]\d{2})', text)
        tutar = max([float(f.replace(',', '.')) for f in fiyatlar]) if fiyatlar else 0.0
        b_no = re.search(r'(\d{5,})', text).group(1) if re.search(r'(\d{5,})', text) else "0001"
        
        if tutar <= 0: return []
        matrah = round(tutar / 1.01, 2)
        kdv = round(tutar - matrah, 2)
        
        # Belge No başına ' koyarak Excel'in bozmasını engelliyoruz
        return [
            [tarih, '153.01.001', 'Mal Alimi', matrah, 0, f"'{b_no}", 'F'],
            [tarih, '191.01.001', 'KDV %1', kdv, 0, f"'{b_no}", 'F'],
            [tarih, '100.01.001', 'Nakit Odeme', 0, tutar, f"'{b_no}", 'F']
        ]
    except: return []

if uploaded_files:
    data = []
    for f in uploaded_files:
        data.extend(analiz_et(f))
    
    if data:
        df = pd.DataFrame(data, columns=['Tarih', 'Hesap_Kod', 'Aciklama', 'Borc', 'Alacak', 'Belge_No', 'Belge_Turu'])
        st.table(df) # Ekranda kontrol et
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button("📥 HATASIZ EXCEL'İ İNDİR", output.getvalue(), "Orka_Aktarim.xlsx")
