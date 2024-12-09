import requests
import logging
from config import Config
import os
class MetaWhatsAppService:
    @staticmethod
    def download_media(media_id, save_path='downloads'):
        """
        Download media from Meta WhatsApp API and save it locally.
        
        :param media_id: The ID of the media to download.
        :param save_path: The directory where the file will be saved.
        :return: The local file path if saved successfully, None otherwise.
        """
        try:
            # Define the URL and headers
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {Config.META_WA_TOKEN}"}

            # Make the request to get the media URL
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                media_url = response.json().get('url')
                if not media_url:
                    logging.error("No media URL found in the response.")
                    return None

                # Make the request to download the media file
                media_response = requests.get(media_url, headers=headers)
                if media_response.status_code == 200:
                    # Ensure the save_path directory exists
                    os.makedirs(save_path, exist_ok=True)
                    content_type = media_response.headers.get('Content-Type', '').lower()
                    file_extension = content_type.split('/')[-1]
                    # Generate the file path
                    file_name = f"{media_id}.{file_extension}"  # Replace with proper file extension if known
                    file_path = os.path.join(save_path, file_name)

                    # Save the file locally
                    with open(file_path, 'wb') as file:
                        file.write(media_response.content)
                    
                    logging.info(f"Media file saved at: {file_path}")
                    return file_path

                logging.error(f"Failed to download media content: {media_response.status_code}")
            else:
                logging.error(f"Failed to fetch media URL: {response.status_code}")
            return None

        except Exception as e:
            logging.error(f"Media Download Error: {e}")
            return None

    @staticmethod
    def send_whatsapp_message(phone_number, message):
        """
        Send WhatsApp message via Meta API
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{Config.META_WA_PHONE_NUMBER_ID}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": phone_number,
                "type": "text",
                "text": {"body": message}
            }
            
            headers = {
                "Authorization": f"Bearer {Config.META_WA_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            logging.error(f"WhatsApp Message Send Error: {e}")
            return False