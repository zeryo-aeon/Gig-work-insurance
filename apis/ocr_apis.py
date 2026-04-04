import os
import requests
from dotenv import load_dotenv

try:
    from utils.logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger("OCRWrapper")

class OCRWrapper:
    def __init__(self, api_token: str = None):
        """Initialize OCR wrapper with Hugging Face API token."""
        self.env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(self.env_path)
        
        self.api_token = api_token or os.getenv("HF_TOKEN")
        self.api_url = "https://router.huggingface.co/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
        }

    def query(self, payload: dict) -> dict:
        """Query the OCR/VLM model with a payload."""
        app_logger.info(f"OCR: Querying VLM model: {payload.get('model')}")
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            app_logger.debug(f"OCR: API Response Status: {response.status_code}")
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
                app_logger.info(f"OCR: Successfully extracted content ({len(content)} chars)")
            
            return result
        except Exception as e:
            app_logger.error(f"OCR: API Error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def bytes_to_base64_data_url(image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Convert image bytes to a base64 Data URL."""
        import base64
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"

if __name__ == "__main__":
    ocr = OCRWrapper()
    
    # Test Payload
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Describe this image in one sentence."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"
                        }
                    }
                ]
            }
        ],
        "model": "Qwen/Qwen2.5-VL-72B-Instruct:ovhcloud"
    }

    result = ocr.query(payload)
    if "choices" in result:
        print("\n✅ OCR API Response:")
        print(result["choices"][0]["message"]["content"])
    else:
        print("\n❌ Error in OCR API:", result)