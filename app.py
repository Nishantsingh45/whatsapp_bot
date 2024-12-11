from flask import Flask, request, jsonify
from models import db, User, Receipt
from services.meta_service import MetaWhatsAppService
from services.image_service import AIReceiptService
from services.storage_service import SupabaseStorageService
from config import Config
import logging
from sqlalchemy import func

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
# @app.route('/webhook', methods=['POST'])
# def webhook():
#     # if request.method == 'GET':
#     #     # Webhook verification
#     #     if request.args.get('hub.verify_token') == Config.WEBHOOK_VERIFY_TOKEN:
#     #         return request.args.get('hub.challenge'), 200
#     #     return 'Invalid verification token', 403

#     if request.method == 'POST':
#         try:
#             data = request.get_json()
            
#             # Extract message details
#             message = data['entry'][0]['changes'][0]['value']['messages'][0]
#             from_number = message['from']
            
#             # Check if message contains media
#             if 'type' in message and message['type'] == 'text':
#                 with app.app_context():
#                     user = User.query.filter_by(phone=from_number).first()
#                     if not user:
#                         user = User(phone=from_number)
#                         db.session.add(user)
#                         db.session.commit()
#                 MetaWhatsAppService.send_whatsapp_message(from_number, "Please Provide your Receipt Image to get the Expense details")
#             if 'type' in message and message['type'] == 'image':
#                 media_id = message['image']['id']
                
#                 # Find or create user
#                 with app.app_context():
#                     user = User.query.filter_by(phone=from_number).first()
#                     if not user:
#                         user = User(phone=from_number)
#                         db.session.add(user)
#                         db.session.commit()
                
#                 # Download and process image
#                 media_content = MetaWhatsAppService.download_media(media_id)
#                 print(media_content)
#                 # storage_service = SupabaseStorageService()
#                 # image_url = storage_service.upload_image(media_content)
#                 # Process receipt
#                 receipt_info = AIReceiptService.process_receipt_image(media_content)
#                 print(receipt_info)
#                 if receipt_info:
#                     # Create receipt entry
#                     with app.app_context():
#                         receipt = Receipt(
#                             user_id=user.id,
#                             image_url=media_content,
#                             **receipt_info
#                         )
#                         db.session.add(receipt)
#                         db.session.commit()
                    
#                     # Send success message
#                     confirmation_msg = f"""
# 📋 Receipt Processed Successfully! 
# 💰 Amount: ${receipt_info['amount']:.2f}
# 🏪 Seller: {receipt_info['seller']}
# 📝 Summary: {receipt_info['summary']}
# 📅 Date: {receipt_info['date_time']}
# 🏷️ Category: {receipt_info['category']}

# Thank you for uploading your receipt! 🎉
# """
#                     MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
#                 else:
#                     MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your receipt. Please try again.")
            
#             return jsonify(success=True), 200
        
#         except Exception as e:
#             logging.error(f"Webhook Processing Error: {e}")
#             return jsonify(error=str(e)), 500

from datetime import datetime, timedelta
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        try:
            data = request.get_json()
            print(data)
            # Extract message details
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            
            # Determine message type
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                
                # Handle different message types
                if message.get('type') == 'text' or 'interactive' in message:
                    # Check if it's a reply to interactive buttons
                    if 'interactive' in message:
                        interactive_type = message['interactive'].get('type')
                        
                        if interactive_type == 'button_reply':
                            button_id = message['interactive']['button_reply'].get('id')
                            
                            # Handle button selections
                            if button_id == 'current_month_expense':
                                current_month_expense = calculate_current_month_expense(from_number)
                                response_message = f"🧾 Current Month Expenses:\n💰 Total: ${current_month_expense:.2f}"
                                send_interactive_menu(from_number, response_message)
                            
                            elif button_id == 'last_3_months_summary':
                                quarterly_expenses = calculate_quarterly_expenses(from_number)
                                print("quarter_expense: ",quarterly_expenses)
                                response_message = f"""📊 Last 3 Months Summary:
💰 Total Expenses: ${quarterly_expenses['total']:.2f}
📈 Trend: {quarterly_expenses['trend']}
🔍 Breakdown:
- Month 1: ${quarterly_expenses['month1']:.2f}
- Month 2: ${quarterly_expenses['month2']:.2f}
- Month 3: ${quarterly_expenses['month3']:.2f}"""
                                send_interactive_menu(from_number, response_message)
                    
                    else:
                        # Initial interaction or text message
                        send_initial_interactive_menu(from_number)
                
                # Existing image processing logic
                elif message.get('type') == 'image':
                    # Your existing image processing code here
                    process_receipt_image(message, from_number)
            
            return jsonify(success=True), 200
        
        except Exception as e:
            logging.error(f"Webhook Processing Error: {e}")
            return jsonify(error=str(e)), 500

def send_initial_interactive_menu(phone_number):
    """Send initial interactive menu with options"""
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "Welcome! What would you like to do today?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "current_month_expense",
                            "title": "This Month Expense"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "last_3_months_summary",
                            "title": "3 Months Summary"
                        }
                    }
                ]
            }
        }
    }
    
    # Use your Meta WhatsApp Service to send the message
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number,interactive_message)

def send_interactive_menu(phone_number, previous_response):
    """Send interactive menu after showing previous results"""
    interactive_message = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"{previous_response}\n\nWhat would you like to do next?"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "current_month_expense",
                            "title": "This Month Expense"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "last_3_months_summary",
                            "title": "3 Months Summary"
                        }
                    }
                ]
            }
        }
    }
    
    # Use your Meta WhatsApp Service to send the message
    MetaWhatsAppService.send_whatsapp_interactive_message(phone_number,interactive_message)


def calculate_current_month_expense(phone_number):
    """Calculate total expenses for the current month"""
    with app.app_context():
        # Get current user
        user = User.query.filter_by(phone=phone_number).first()
        
        if not user:
            return 0.0
        
        # Calculate start of the current month
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Query receipts for the current month
        current_month_receipts = Receipt.query.filter(
            Receipt.user_id == user.id,
            # SQLite conversion for datetime comparison
            func.datetime(Receipt.date_time) >= start_of_month
        ).all()
        
        # Sum the amounts
        total_expense = sum(receipt.amount for receipt in current_month_receipts)
        return total_expense


def calculate_quarterly_expenses(phone_number):
    """Calculate expenses for the last 3 months"""
    with app.app_context():
        # Get current user
        user = User.query.filter_by(phone=phone_number).first()
        
        if not user:
            return {
                'total': 0.0,
                'month1': 0.0,
                'month2': 0.0,
                'month3': 0.0,
                'trend': 'No data'
            }
        
        # Calculate start dates for last 3 months
        now = datetime.now()
        month1_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month2_start = (month1_start - timedelta(days=1)).replace(day=1)
        month3_start = (month2_start - timedelta(days=1)).replace(day=1)
        
        # Calculate expenses for each month
        def calculate_month_expense(start_date, end_date):
            month_receipts = Receipt.query.filter(
                Receipt.user_id == user.id,
                # SQLite conversion for datetime comparison
                func.datetime(Receipt.date_time) >= start_date,
                func.datetime(Receipt.date_time) < end_date
            ).all()
            return sum(receipt.amount for receipt in month_receipts)
        
        month1_expense = calculate_month_expense(month1_start, now)
        month2_expense = calculate_month_expense(month2_start, month1_start)
        month3_expense = calculate_month_expense(month3_start, month2_start)
        
        # Determine trend
        if month1_expense > month2_expense and month2_expense > month3_expense:
            trend = "📈 Increasing"
        elif month1_expense < month2_expense and month2_expense < month3_expense:
            trend = "📉 Decreasing"
        else:
            trend = "↔️ Stable"
        
        return {
            'total': month1_expense + month2_expense + month3_expense,
            'month1': month1_expense,
            'month2': month2_expense,
            'month3': month3_expense,
            'trend': trend
        }


def process_receipt_image(message, from_number):
    """Process receipt image (your existing logic)"""
    media_id = message['image']['id']
    
    with app.app_context():
        user = User.query.filter_by(phone=from_number).first()
        if not user:
            user = User(phone=from_number)
            db.session.add(user)
            db.session.commit()
    
    # Download and process image
    media_content = MetaWhatsAppService.download_media(media_id)
    receipt_info = AIReceiptService.process_receipt_image(media_content)
    
    if receipt_info:
        with app.app_context():
            receipt = Receipt(
                user_id=user.id,
                image_url=media_content,
                **receipt_info
            )
            db.session.add(receipt)
            db.session.commit()
        
        confirmation_msg = f"""📋 Receipt Processed Successfully! 
💰 Amount: ${receipt_info['amount']:.2f}
🏪 Seller: {receipt_info['seller']}
📝 Summary: {receipt_info['summary']}
📅 Date: {receipt_info['date_time']}
🏷️ Category: {receipt_info['category']}

Thank you for uploading your receipt! 🎉
"""
        # Send confirmation and interactive menu
        MetaWhatsAppService.send_whatsapp_message(from_number, confirmation_msg)
        send_initial_interactive_menu(from_number)
    else:
        MetaWhatsAppService.send_whatsapp_message(from_number, "Sorry, I couldn't process your receipt. Please try again.")
        send_initial_interactive_menu(from_number)

if __name__ == '__main__':
    app.run(debug=True)
