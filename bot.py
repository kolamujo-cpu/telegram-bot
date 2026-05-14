import telebot
import base64
from PIL import Image
from google import genai

# ======================
# KEYS
# ======================
BOT_TOKEN = "8862764456:AAEHchsavPHdXP2ucd0NSTuvnT3VZScgMjA"
GEMINI_KEY = "AIzaSyDFLEb0dvNaX8DYRqQMXNphwzzBjFh6t0U"

# ======================
# INIT
# ======================
bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_KEY)

# ======================
# START COMMAND
# ======================
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "📊 Smart Money AI Bot Ready\n\nSend a chart screenshot for analysis."
    )

# ======================
# IMAGE ANALYSIS
# ======================
@bot.message_handler(content_types=['photo', 'document'])
def handle_photo(message):

    print("IMAGE RECEIVED")

    try:
        bot.send_chat_action(message.chat.id, "typing")

        bot.reply_to(message, "📊 Analyzing chart...")

        # ======================
        # GET FILE
        # ======================
        file_id = (
            message.photo[-1].file_id
            if message.photo
            else message.document.file_id
        )

        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        image_path = "chart.jpg"

        # ======================
        # SAVE IMAGE
        # ======================
        with open(image_path, "wb") as f:
            f.write(downloaded_file)

        # ======================
        # COMPRESS IMAGE
        # ======================
        img = Image.open(image_path)

        img = img.convert("RGB")

        # Resize large screenshots
        img.thumbnail((1280, 1280))

        # Save compressed image
        img.save(image_path, format="JPEG", quality=70)

        # ======================
        # CONVERT IMAGE TO BASE64
        # ======================
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(
                img_file.read()
            ).decode("utf-8")

        # ======================
        # CAPTION
        # ======================
        caption = (
            message.caption
            or "Analyze this trading chart professionally"
        )

        # ======================
        # PROMPT
        # ======================
        prompt = f"""
Analyze this trading chart using Smart Money Concept.

User request:
{caption}

Reply shortly in this format:

Trend:
Structure:
Liquidity:
Entry:
Stop Loss:
Take Profit:
Confidence:
Risk:
"""

        # ======================
        # GEMINI REQUEST
        # ======================
        try:

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=[
                    prompt,
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            )

            final_text = response.text

            # ======================
            # AUTO SIGNAL TAG
            # ======================
            if "bullish" in final_text.lower():
                final_text = "🟢 BUY BIAS\n\n" + final_text

            elif "bearish" in final_text.lower():
                final_text = "🔴 SELL BIAS\n\n" + final_text

            else:
                final_text = "🟡 WAIT / NEUTRAL\n\n" + final_text

            bot.reply_to(message, final_text)

        except Exception as e:

            print("MAIN MODEL ERROR:", e)

            bot.reply_to(
                message,
                "⚠ Main model busy... trying backup model"
            )

            # ======================
            # BACKUP MODEL
            # ======================
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    prompt,
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            )

            bot.reply_to(message, response.text)

    except Exception as e:

        print("ERROR:", e)

        error_text = str(e)

        # Gemini quota / overload errors
        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:

            bot.reply_to(
                message,
                "⚠ Server busy right now.\n\nPlease wait about 30 minutes before sending another chart."
            )

        # Gemini temporary overload
        elif "503" in error_text or "UNAVAILABLE" in error_text:

            bot.reply_to(
                message,
                "⚠ Analysis servers are currently busy.\n\nTry again in a few minutes."
            )

        # Other errors
        else:

            bot.reply_to(
                message,
                "❌ Something went wrong while analyzing the chart."
            )
   
   
# ======================
# RUN BOT
# ======================
print("Bot is running...")
bot.infinity_polling()