from flask import Flask, request, jsonify
from models import db, User, Receipt
from services.meta_service import MetaWhatsAppService
from services.image_service import AIReceiptService
from services.storage_service import SupabaseStorageService
from config import Config
import logging

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    with app.app_context():
        db.create_all()
    logging.basicConfig(level=logging.INFO)
    
    return app

app = create_app()
print("created")
@app.route('/webhook', methods=['GET'])
def waba_verify():
  # Webhook verification
  if request.args.get("hub.mode") == "subscribe" and request.args.get(
      "hub.challenge"):
    if not request.args.get("hub.verify_token") == 'hello':
      return "Verification token mismatch", 403
    return request.args["hub.challenge"], 200
  return "Hello world", 200
@app.route('/webhook', methods=['POST'])
def webhook():
    # if request.method == 'GET':
    #     # Webhook verification
    #     if request.args.get('hub.verify_token') == Config.WEBHOOK_VERIFY_TOKEN:
    #         return request.args.get('hub.challenge'), 200
    #     return 'Invalid verification token', 403

    if request.method == 'POST':
        try:
            data = request.get_json()
            
            # Extract message details
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_number = message['from']
            
            # Check if message contains media
            if 'type' in message and message['type'] == 'text':
                with app.app_context():
                    user = User.query.filter_by(phone=from_number).first()
                    if not user:
                        user = User(phone=from_number)
                        db.session.add(user)
                        db.session.commit()
                MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your Receipt Image to get the Expense details")
            if 'type' in message and message['type'] == 'image':
                media_id = message['image']['id']
                
                # Find or create user
                with app.app_context():
                    user = User.query.filter_by(phone=from_number).first()
                    if not user:
                        user = User(phone=from_number)
                        db.session.add(user)
                        db.session.commit()
                
                # Download and process image
                media_content = MetaWhatsAppService.download_media(media_id)
                print(media_content)
                # storage_service = SupabaseStorageService()
                # image_url = storage_service.upload_image(media_content)
                # Process receipt
                receipt_info = AIReceiptService.process_receipt_image(media_content)
                print(receipt_info)
                if receipt_info:
                    # Create receipt entry
                    with app.app_context():
                        receipt = Receipt(
                            user_id=user.id,
                            image_url=media_content,
                            **receipt_info
                        )
                        db.session.add(receipt)
                        db.session.commit()
                    
                    # Send success message
                    confirmation_msg = f"""
📋 Receipt Processed Successfully! 
💰 Amount: ${receipt_info['amount']:.2f}
🏪 Seller: {receipt_info['seller']}
📝 Summary: {receipt_info['summary']}
📅 Date: {receipt_info['date_time']}
🏷️ Category: {receipt_info['category']}

Thank you for uploading your receipt! 🎉
"""
                    MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
                else:
                    MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your receipt. Please try again.")
            
            return jsonify(success=True), 200
        
        except Exception as e:
            logging.error(f"Webhook Processing Error: {e}")
            return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
