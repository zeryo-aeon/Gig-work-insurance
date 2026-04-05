import os
import json
import base64
from typing import Dict, Any
from dotenv import load_dotenv

try:
    from utils.logger import app_logger
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    app_logger = logging.getLogger("OllamaOCR")

# ✅ Safe import for Ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    app_logger.warning("Ollama library not installed. Run 'pip install ollama'")

class OCRWrapper:
    def __init__(self, model_name: str = "glm-ocr:q8_0"):
        """Initialize Ollama OCR pipeline."""
        load_dotenv()
        self.model_name = model_name

    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Uses GLM-OCR to extract and structure data in one pass.
        Replaces both EasyOCR and Groq.
        """
        if not OLLAMA_AVAILABLE:
            return {"error": "Ollama library not installed"}

        if not os.path.exists(image_path):
            app_logger.error(f"File not found: {image_path}")
            return {"error": "File not found", "file": image_path}

        try:
            app_logger.info(f"Ollama: Processing {image_path} with {self.model_name}")

            # GLM-OCR can handle extraction and structuring in one prompt
            prompt = """
            Extract text from this image and return it as structured JSON.
            The JSON should include:
            - platform
            - order_id
            - date
            - total_amount
            - items (list of names and prices)
            Return ONLY the raw JSON object.
            """

            response = ollama.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_path]
                }],
                options={'temperature': 0} # Keep it deterministic
            )

            content = response['message']['content']
            
            # Clean potential markdown backticks from the response
            clean_json = content.replace("```json", "").replace("```", "").strip()
            structured_data = json.loads(clean_json)

            return {
                "file": os.path.basename(image_path),
                "status": "success",
                "structured": structured_data
            }

        except json.JSONDecodeError:
            app_logger.error("Failed to parse JSON from model response.")
            return {
                "file": os.path.basename(image_path),
                "status": "partial_success",
                "raw_content": content,
                "error": "JSON parsing error"
            }
        except Exception as e:
            app_logger.error(f"Ollama Error: {e}")
            return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    # Initialize with the model you pulled
    ocr = OCRWrapper(model_name="glm-ocr:q8_0")

    images = ["IMG_5173.jpg"]

    for img in images:
        result = ocr.process_image(img)
        print(f"\n--- Results for {img} ---")
        print(json.dumps(result, indent=2))