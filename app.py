import streamlit as st
import pytesseract
from PIL import Image
import pandas as pd
import re
import io

st.set_page_config(page_title="Orka Fatura Asistanı", layout="wide")
st.title("📄 Orka Fatura Listesi Dönüştürücü")

secilen_tarih = st.date_input("Belge Tarihi Seçin", pd.to_datetime("today"))
formatli_tarih = secilen_tarih.strftime("%d.%m.%Y")

uploaded_files = st.file_uploader("Fiş/Fatura Fotoğraflarını Seçin", accept_multiple_files=True)

def analiz_et(file, tarih):
    try:
        img = Image.open(file)
        text = pytesseract.image_to_string(img, lang='tur')
        
        # TUTAR VE VERGİ NO BULMA (Basit mantık)
        fiyatlar = re.findall(r'(\d+[\.,]\d{2})', text)
        genel_toplam = max([float(f.replace(',', '.')) for f in fiyatlar]) if fiyatlar else 0.0
        v_no = re.search(r'(\d{10,11})', text).group(1) if re.search(r'(\d{10,11})', text) else ""
        b_no = re.search(r'(\d{3,})', text).group(1) if re.search(r'(\d{3,})', text) else "1"
        
        if genel_toplam <= 0: return None
        
        kdv_tutar = round(genel_toplam - (genel_toplam / 1.10), 2) # %10 varsayılan
        alis_tutar = round(genel_toplam - kdv_tutar, 2)
        
        return {
            "belge tarihi": tarih,
            "belge no": b_no,
            "kdv oranı": 10,
            "vergi no": v_no,
            "firma adı": "FİŞTEN OKUNAN İŞLETME",
            "alış tutar": alis_tutar,
            "kdv tutar": kdv_tutar,
            "genel toplam": genel_toplam
        }
    except: return None

if uploaded_files:
    sonuclar = []
    for f in uploaded_files:
        res = analiz_et(f, formatli_tarih)
        if res: sonuclar.append(res)
    
    if sonuclar:
        df = pd.DataFrame(sonuclar)
        st.table(df)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Sheet1')
            ws = writer.sheets['Sheet1']
            for idx, col in enumerate(df.columns):
                ws.column_dimensions[chr(65 + idx)].width = 20
        
        st.download_button("📥 ORKA EXCEL'İNİ İNDİR", output.getvalue(), "Orka_Fatura_Listesi.xlsx")
