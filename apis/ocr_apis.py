import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

try:
    from utils.logger import app_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    app_logger = logging.getLogger("OCRWrapper")

# ✅ Safe imports (won’t break app startup)
try:
    import easyocr
    EASY_OCR_AVAILABLE = True
except Exception as e:
    EASY_OCR_AVAILABLE = False
    app_logger.warning(f"EasyOCR not available: {e}")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except Exception as e:
    GROQ_AVAILABLE = False
    app_logger.warning(f"Groq not available: {e}")


class OCRWrapper:
    def __init__(self, groq_api_key: str = None):
        """Initialize OCR + Groq pipeline safely."""
        load_dotenv()
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")

        self.reader = None
        self.client = None

    # ✅ Lazy load EasyOCR (only when needed)
    def _init_ocr(self):
        if not EASY_OCR_AVAILABLE:
            app_logger.error("EasyOCR not installed.")
            return False

        if self.reader is None:
            try:
                app_logger.info("Initializing EasyOCR...")
                self.reader = easyocr.Reader(['en'], gpu=False)
            except Exception as e:
                app_logger.error(f"EasyOCR Init Error: {e}")
                return False
        return True

    # ✅ Lazy load Groq
    def _init_groq(self):
        if not GROQ_AVAILABLE:
            app_logger.error("Groq SDK not installed.")
            return False

        if self.client is None:
            try:
                self.client = Groq(api_key=self.groq_api_key)
            except Exception as e:
                app_logger.error(f"Groq Init Error: {e}")
                return False
        return True

    def extract_text(self, image_path: str) -> str:
        """Extract raw text using EasyOCR safely."""
        if not os.path.exists(image_path):
            app_logger.error(f"File not found: {image_path}")
            return ""

        if not self._init_ocr():
            return ""

        try:
            app_logger.info(f"OCR: Reading {image_path}")
            results = self.reader.readtext(image_path)

            extracted_text = " ".join([r[1] for r in results])

            if not extracted_text.strip():
                app_logger.warning("No text detected.")
                return ""

            return extracted_text

        except Exception as e:
            app_logger.error(f"OCR Error: {e}")
            return ""

    def refine_with_groq(self, raw_text: str) -> Dict[str, Any]:
        """Structure text using Groq safely."""

        if not raw_text.strip():
            return {
                "platform": "Unknown",
                "order_id": None,
                "date": None,
                "total_amount": 0.0,
                "items": [],
                "error": "No OCR text"
            }

        if not self._init_groq():
            return {
                "error": "Groq not available",
                "raw_text": raw_text
            }

        try:
            prompt = f"""
            Extract structured information from this OCR text.
            Return ONLY JSON.

            OCR TEXT:
            {raw_text}
            """

            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Return strict JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            app_logger.error(f"Groq Error: {e}")
            return {
                "error": "Groq processing failed",
                "details": str(e)
            }

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """Full pipeline"""
        raw_text = self.extract_text(image_path)
        structured = self.refine_with_groq(raw_text)

        return {
            "file": os.path.basename(image_path),
            "status": "success" if raw_text else "failed",
            "raw_text": raw_text,
            "structured": structured
        }


if __name__ == "__main__":
    ocr = OCRWrapper()

    images = ["receipt1.png", "receipt2.jpg"]

    for img in images:
        result = ocr.process_image(img)
        print(f"\n--- {result['file']} ---")
        print(json.dumps(result, indent=2))