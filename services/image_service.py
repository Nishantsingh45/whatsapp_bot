import openai
import logging
from config import Config
from datetime import datetime
from openai import OpenAI
import base64
import requests, json
import os,json

def encode_image(image_url):
    """
    Encode an image to base64

    Args:
        image_url (str): Path or URL of the image

    Returns:
        str: Base64 encoded image or None if error occurs
    """
    try:
        
        # Remove 'file://' prefix

        # Read and encode the file
        with open(image_url, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    except Exception as e:
        #logger.error(f"Error encoding image to base64: {e}")
        return None


class AIReceiptService:
    @staticmethod
    def process_receipt_image(image_url):
        """
        Process receipt image using OpenAI Vision
        """
        try:
            openai.api_key = Config.OPENAI_API_KEY
            base64_image = encode_image(image_url)
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            response = client.chat.completions.create(
                response_format={"type": "json_object"},
                model=Config.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ''''Extract detailed information from this receipt: date, total amount, seller name, items summary, and category (choose from: food, shopping, travel, utilities, other).Return a JSON-formatted response.
                         {
                            "Date": "Date and time",
                            "total amount": "total amount",
                            "seller name": "name of seller",
                            "item summary": "summary of all item",
                         "category": "category
                           
                        }'''},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )
            
            #receipt_text = response.choices[0].message.content
            content = json.loads(response.choices[0].message.content)
            return AIReceiptService._parse_receipt_info(content)
            return content
        except Exception as e:
            logging.error(f"OpenAI Processing Error: {e}")
            return None

    @staticmethod
    def _parse_receipt_info(content):
        """
        Parse OpenAI's response into structured data
        """
        try:
            raw_amount = content['total amount']
            sanitized_amount = float(raw_amount.replace('$', '').replace(',', ''))  # Remove $ and commas
            return {
                'date_time': content['Date'],  # Rename 'Date' to 'date_time'
                'amount': sanitized_amount,  # Convert 'total amount' to a float
                'seller': content['seller name'],  # Rename 'seller name' to 'seller'
                'summary': content['item summary'],  # Rename 'item summary' to 'summary'
                'category': content['category']  # No change for 'category'
            }
        except Exception as e:
            logging.error(f"Receipt Parsing Error: {e}")
            return None

    @staticmethod
    def _extract_amount(text):
        # TODO: Implement precise amount extraction
        return 0.0

    @staticmethod
    def _extract_seller(text):
        # TODO: Implement seller extraction
        return "Unknown Seller"

    @staticmethod
    def _extract_category(text):
        # TODO: Implement category extraction
        return "other"
