from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
import gspread
from datetime import datetime
import os
import json
from io import BytesIO
from PIL import Image
import base64
import re

app = Flask(__name__)

# ตั้งค่า LINE Bot
CHANNEL_ACCESS_TOKEN = "2010093991"  # ← เปลี่ยนเป็น Token ของคุณ
CHANNEL_SECRET = "921adc7ca6b2d99ba859f578374284a8"  # ← เปลี่ยนเป็น Secret ของคุณ

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ตั้งค่า Google Sheets
GOOGLE_SHEETS_ID = "1I8h18IBgrxsLTU37N8LeoHP3W1njAsn7a4w2ZAIA7tA"  # ← Sheet ID ของคุณ

# JSON Key ของ Service Account (ใส่ลงไป)
GOOGLE_CREDENTIALS_JSON = {
    "type": "service_account",
    "project_id": "line-bot-496404",
    "private_key_id": "7a2f6a1d20ed15beb9060b59d1615ebaf2a50971",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQCwkwdvEyBcg3Np\ncSQ0BcPekcycjL2bo4LbjC/yHqh9FxfF9B7I5mRQ5ygPcgpKW0gUxtNvk3y0crLU\nksRzM4+0bzEbapxC+frdlRpL8tdRIksH9+7Tyj4F6obwYjw9vJm7GVMMGUTXaIRn\npAnflNXXoZWIMVcqP6ZSV+y95hN2IpDST3A0eamNEWT04jy4JgwlKwB57Wcp4/EG\n/Enyuqtb1dr37CknsxMHBLuPISC5JrmHYQ2m4JBnP/J62Ry1qzImAhYmS9M2XxcQ\n5MU+oNzzKXGbwFP1YkO3YQp1dbYKYSdIXZDobHMgIZi+mFcrKD+aBec7aSeu9vTx\nSKH4EOqPAgMBAAECgf9WrStOWxUyVKn9beICUid+xL4BcGpNpvZAJOYO9FMWaepB\nlz7atOiJeO8xUHRnYRJWde3/LLxf1+3xFhquckvDRtHUTiu8Ck9wdhYdMhfVZqrD\nk/FTWvPB87Oe90SbCaRtM6vl7ywxPB0YGG4Vp/n7ilYyL1uaYaRDcjsZp4HmJZYr\nqRt3bwDcL62uNl3RK/JS/iBQNcBIpx1im6AGwkDhtP8xnp7dNRVagDaXfTonfrOe\n3Dez9M7JJjw4PP+j4grj+TxCyuJ1CMZzqylKTr1aFZDf4N8pblyO7KQ8sQXQMZy5\nc+6HlGs09ZGTxebVKd1LfB9XQButZVE5xkLFJokCgYEA2MNyW0G5pdEPv8IsoZX8\nXEljH7KHHz3io1h4VWh8kv0CKbxTjlEWCVbOAYKp6+1WpXYY49g9DFsXGjr+GjtE\nGP0kD+1/EGQ8rPZoLK6XDo/E4zuMwA+ZhYhwkahLTK193jIhcoYJytTh54g6Upv/\n/1Okr0i+LzV86gUNMkU+KF0CgYEA0IlEaOQROMfXzjZTuk893FgrdYujQ4VTVcC8\nS4YQtUh/vPqCkxAA9uP9NiAVyumT79fGy6F3shGt5RQcbrGlianaX2DOgHHgEt/d\nISJvmh3PVWuE5qi7dDBk3ErKIxJuTVPlOOcdf/xjdbi6EkOmfdAxg61TI2bLif8O\n/IJzv9sCgYADdNJc/CZOq4+5ugnmJbMZcZ4gAkO/TshPXHjGu9zIpzoimjsm2Mom\nKfks8v1soqMwDjsFXwxSJx2uMGSe3HUQhPDPRDUzeLWy+Fbe54XHGKnGCcwLv/Pt\nuig5WlqhBV8tbNU1s0dysYRModJ0QMKLOrU0ik9mB09Pl/cG5y2/jQKBgQCCxoKD\nMPtn21OHu2QYg5cstpJSfcZeEp9nOJ4c0q9psFSDI6p9JV0ld2aU6dwgywh+MZg2\nnUTeA95Eua728Cr6wOz0QVZfEIrP61nWbK0GPkmGrQ3ERO6Bd9PYnoJTKjzH+6PV\nYoKKf7Gz4qu1xn0Di2txw2FO4ykjmjNAwWJrXwKBgHZS/MWeWsBJhKfBBKiIy3EY\nR/QYHHc9XDdCQgZhhjDfIdm9CWgOJJDBGk9gw8LPuOpcd49b6a7WgwfwNqsLsN49\n1MNEoeKO9aTREmenhzeuetbZ5JWCtccZeNxBIqXABpYDYSBxTvdBryAijWBHQuPU\nWJvhtwm3GNsnCOl9Zd3+\n-----END PRIVATE KEY-----\n",
    "client_email": "line-bot-service@line-bot-496404.iam.gserviceaccount.com",
    "client_id": "109258179229148496592",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/line-bot-service%40line-bot-496404.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

# เก็บข้อมูลชั่วคราวต่อ user
user_data = {}

def get_google_sheet():
    """เชื่อมต่อ Google Sheets"""
    credentials = Credentials.from_service_account_info(
        GOOGLE_CREDENTIALS_JSON,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(GOOGLE_SHEETS_ID)
    return sheet.worksheet(0)

def send_message(user_id, text):
    """ส่งข้อความไปยัง User"""
    line_bot_api.push_message(user_id, {'type': 'text', 'text': text})

@app.route('/callback', methods=['POST'])
def callback():
    """รับข้อมูลจาก LINE Webhook"""
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    """เมื่อ User ส่งรูปมา"""
    user_id = event.source.user_id
    message_id = event.message.id
    
    # ดาวน์โหลดรูปจาก LINE
    message_content = line_bot_api.get_message_content(message_id)
    image_data = base64.b64encode(message_content.content).decode()
    
    # เก็บข้อมูลรูป
    if user_id not in user_data:
        user_data[user_id] = {}
    
    user_data[user_id]['slip_image'] = image_data
    user_data[user_id]['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ขอข้อมูลเพิ่มเติม
    send_message(user_id, "✅ รับรูปสลิปแล้ว!\n\nต่อไปส่งข้อมูลการโอนเงิน เช่น:\nจำนวนเงิน: 1000\nผู้โอน: คุณสมชาย\nผู้รับเงิน: ร้านเอก\nอู่: ทั่วไป")

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    """เมื่อ User ส่อข้อความมา"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # ตรวจสอบการส่ง
    if "จำนวนเงิน:" in text or "ผู้โอน:" in text or "ผู้รับ" in text or "อู่:" in text:
        # แยกข้อมูล
        data = user_data[user_id]
        
        # ดึงข้อมูลจาก message
        lines = text.split('\n')
        for line in lines:
            if "จำนวนเงิน:" in line:
                data['amount'] = line.split("จำนวนเงิน:")[1].strip()
            elif "ผู้โอน:" in line:
                data['sender'] = line.split("ผู้โอน:")[1].strip()
            elif "ผู้รับเงิน:" in line or "ผู้รับ:" in line:
                data['receiver'] = line.split("ผู้รับ")[1].strip().replace("เงิน:", "")
            elif "อู่:" in line:
                data['shop'] = line.split("อู่:")[1].strip()
        
        # ตรวจสอบความครบถ้วน
        required_fields = {
            'amount': 'จำนวนเงิน',
            'sender': 'ผู้โอน',
            'receiver': 'ผู้รับเงิน',
            'shop': 'ชื่ออู่'
        }
        
        missing = [v for k, v in required_fields.items() if k not in data or not data[k]]
        
        if missing:
            msg = "⚠️ ข้อมูลขาด:\n" + "\n".join([f"- {m}" for m in missing])
            msg += "\n\nกรุณาส่งข้อมูลให้ครบถ้วน"
            send_message(user_id, msg)
        else:
            # บันทึกลง Google Sheets
            try:
                worksheet = get_google_sheet()
                row = [
                    data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    data.get('amount', ''),
                    data.get('sender', ''),
                    data.get('receiver', ''),
                    data.get('shop', '')
                ]
                worksheet.append_row(row)
                
                send_message(user_id, "✅ บันทึกการโอนเงินเรียบร้อยแล้ว!\n\nข้อมูล:\n" +
                           f"วันที่: {row[0]}\nจำนวนเงิน: {row[1]} บาท\nผู้โอน: {row[2]}\nผู้รับ: {row[3]}\nอู่: {row[4]}")
                
                # ลบข้อมูลเก่า
                del user_data[user_id]
            except Exception as e:
                send_message(user_id, f"❌ เกิดข้อผิดพลาด: {str(e)}")
    else:
        send_message(user_id, "ส่งข้อมูลการโอนเงินมาครับ เช่น:\nจำนวนเงิน: 1000\nผู้โอน: คุณสมชาย\nผู้รับเงิน: ร้านเอก\nอู่: ทั่วไป")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
