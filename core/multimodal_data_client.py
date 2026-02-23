import io
from PIL import Image
import PyPDF2
from typing import List, Optional
import streamlit as st

class ImagePreprocessor:
    @staticmethod
    def validate_and_load(file_bytes: bytes, max_size_mb: int = 10) -> Optional[Image.Image]:
        """Validates image size and loads it as a PIL Image."""
        if len(file_bytes) > max_size_mb * 1024 * 1024:
            st.error(f"Image too large. Maximum size is {max_size_mb}MB.")
            return None
            
        try:
            image = Image.open(io.BytesIO(file_bytes))
            # Convert to RGB if needed (Gemini handles RGB best)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            return image
        except Exception as e:
            st.error(f"Invalid image format: {str(e)}")
            return None

class PDFExtractor:
    @staticmethod
    def extract_text(file_bytes: bytes) -> Optional[str]:
        """Extracts raw text from a PDF file."""
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for i, page in enumerate(reader.pages):
                extracted = page.extract_text()
                if extracted:
                    text += f"--- Page {i+1} ---\n{extracted}\n"
            return text if text.strip() else None
        except Exception as e:
            st.error(f"Failed to read PDF: {str(e)}")
            return None
