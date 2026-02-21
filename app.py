import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
import io

st.set_page_config(page_title="Orka Fatura Asistanı", layout="wide")
st.title("📄 Orka Fatura Listesi Dönüştürücü")

# Tarih ve KDV Seçimi
col1, col2 = st.columns(2)
with col1:
    secilen_tarih = st.date_input("Belge Tarihi Seçin", pd.to_datetime("today"))
with col2:
    varsayilan_kdv = st.selectbox("Varsayılan KDV Oranı", [20, 10, 1], index=1)

formatli_tarih = secilen_tarih.strftime("%d.%m.%Y")
uploaded_files = st.file_uploader("Fiş/Fatura Fotoğraflarını Seçin", accept_multiple_files=True)

def analiz_et(file, tarih, kdv_oran):
    try:
        img = Image.open(file)
        # Görüntü kalitesini artırmak için gri tonlamaya çeviriyoruz
        text = pytesseract.image_to_string(img.convert('L'), lang='tur')
        
        # TUTAR BULMA (Daha geniş kapsamlı arama)
        fiyatlar = re.findall(r'(\d+[\.,]\s?\d{2})', text)
        temiz_fiyatlar = [float(f.replace(',', '.').replace(' ', '')) for f in fiyatlar]
        genel_toplam = max(temiz_fiyatlar) if temiz_fiyatlar else 0.0
        
        # VERGİ VE BELGE NO
        v_no = re.search(r'(\d{10,11})', text).group(1) if re.search(r'(\d{10,11})', text) else ""
        b_no_match = re.search(r'(Fiş No|No|Belge No)\s?:?\s?(\d+)', text, re.IGNORECASE)
        b_no = b_no_match.group(2) if b_no_match else "1"
        
        # KDV HESAPLAMA
        matrah = round(genel_toplam / (1 + (kdv_oran/100)), 2)
        kdv_tutar = round(genel_toplam - matrah, 2)
        
        return {
            "belge tarihi": tarih,
            "belge no": b_no,
            "kdv oranı": kdv_oran,
            "vergi no": v_no,
            "firma adı": "KONTROL EDİLECEK",
            "alış tutar": matrah,
            "kdv tutar": kdv_tutar,
            "genel toplam": genel_toplam
        }
    except:
        return None

if uploaded_files:
    sonuclar = []
    progress_bar = st.progress(0)
    for i, f in enumerate(uploaded_files):
        res = analiz_et(f, formatli_tarih, varsayilan_kdv)
        if res:
            sonuclar.append(res)
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    if sonuclar:
        df = pd.DataFrame(sonuclar)
        st.subheader(f"Toplam {len(sonuclar)} Fiş İşlendi")
        st.table(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            ws = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns):
                ws.column_dimensions[chr(65 + idx)].width = 22
        
        st.download_button("📥 TÜMÜNÜ EXCEL OLARAK İNDİR", output.getvalue(), "Orka_Toplu_Liste.xlsx")
