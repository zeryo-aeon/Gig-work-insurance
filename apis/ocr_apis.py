import os
import requests
from dotenv import load_dotenv

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
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

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