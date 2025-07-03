import streamlit as st
from PIL import Image
import numpy as np
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
import io
# import platform

# Configure Tesseract path (for Windows - optional on Render)
# Comment this line out when deploying to Render or Streamlit Cloud
# if platform.system == "Windows":
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Admin\Tesseract-OCR\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="Nepali PDF to Excel Converter", page_icon="📄")
st.title("📄 Nepali PDF to Excel Converter with OCR and Data Extraction")

st.markdown("Upload a scanned Nepali-language PDF. The app will extract `नाम`, `उमेर`, `लिङ्ग`, and `जाति` using OCR and convert it into Excel.")

uploaded_file = st.file_uploader("📤 Upload scanned PDF file", type="pdf")

if uploaded_file:
    try:
        st.info("🔄 Starting OCR... This may take time depending on the PDF size.")
        images = convert_from_bytes(uploaded_file.read(), dpi=383)
        num_pages = len(images)

        progress_bar = st.progress(0)
        status_text = st.empty()
        all_text = ""

        for i, image in enumerate(images):
            progress = int(((i + 1) / num_pages) * 100)
            progress_bar.progress(progress)
            status_text.markdown(f"🔍 **Processing Page {i + 1} of {num_pages}**...")

            # Convert to grayscale and binarize using PIL (no OpenCV)
            gray_image = image.convert("L")  # L mode = grayscale
            binary_image = gray_image.point(lambda x: 0 if x < 200 else 255, '1')  # Binarize

            text = pytesseract.image_to_string(binary_image, lang='nep')
            all_text += f"Page {i + 1}:\n{text}\n\n"

            # Show OCR preview
            st.text_area(f"📝 OCR Preview (Page {i + 1})", value=text[:500], height=100, key=f"preview_{i}", disabled=True)

        st.success("✅ OCR completed. Extracting structured data...")

        # Regex for: नाम, उमेर, लिङ्ग, जाति
        pattern = re.compile(r'([^\d\.\n]+?)\s+(\d+)\s+वर्ष\s+/\s+(पुरुष|महिला)\s+([^\n]+)')
        matches = re.findall(pattern, all_text)

        if not matches:
            st.warning("⚠️ No structured data matched. Please review the text layout or modify the regex.")
        else:
            data = {
                'नाम': [match[0].strip() for match in matches],
                'उमेर': [int(match[1]) for match in matches],
                'लिङ्ग': [match[2] for match in matches],
                'जाति': [match[0].strip().split()[-1] for match in matches]  # Approximation of caste
            }

            df = pd.DataFrame(data)
            st.dataframe(df.head(50), use_container_width=True)

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Data')
            excel_buffer.seek(0)

            st.download_button(
                label="📥 Download Excel File",
                data=excel_buffer,
                file_name="extracted_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")
