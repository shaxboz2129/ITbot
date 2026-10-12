import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web
import asyncio

TOKEN = "8526475774:AAHCkbLaqwbvEremOykACXYwR4b9a4ZC7SA" 
ADMIN_ID =8865017290  # O'zingizning Telegram ID raqamingiz

bot = telebot.TeleBot(TOKEN)

# Vaqtinchalik saqlash uchun lug'at
user_data = {}

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🛠 Murojaat yuborish"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        f"Assalomu alaykum, **{message.from_user.full_name}**!\n\n"
        "Kompyuteringizda nosozlik bo'lsa, pastdagi tugmani bosib IT bo'limiga murojaat yuboring.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "🛠 Murojaat yuborish")
def ask_room(message):
    sent = bot.send_message(message.chat.id, "📍 Iltimos, kompyuter buzilgan **xona raqamini** yuboring (masalan: *304-xona*):", parse_mode="Markdown")
    bot.register_next_step_handler(sent, process_room)

def process_room(message):
    user_data[message.from_user.id] = {"room": message.text}
    sent = bot.send_message(message.chat.id, "👤 Iltimos, **Ism va familiyangizni** kiriting:")
    bot.register_next_step_handler(sent, process_name)

def process_name(message):
    user_data[message.from_user.id]["name"] = message.text
    sent = bot.send_message(message.chat.id, "⚠️ Kompyuterda qanday **muammo** borligini qisqacha yozib yuboring:")
    bot.register_next_step_handler(sent, process_problem)

def process_problem(message):
    user_id = message.from_user.id
    user_data[user_id]["problem"] = message.text
    
    data = user_data[user_id]
    username = message.from_user.username
    user_link = f"@{username}" if username else f"ID: {user_id}"

    inline_kb = InlineKeyboardMarkup()
    inline_kb.add(InlineKeyboardButton("🛠 Qabul qilish", callback_data=f"accept_{user_id}"))

    admin_text = (
        f"🚨 **Yangi Kompyuter Nosozligi!**\n\n"
        f"🏢 **Xona:** {data['room']}\n"
        f"👤 **Xodim:** {data['name']} ({user_link})\n"
        f"💬 **Muammo:** {data['problem']}\n\n"
        f"⏳ *Holat: Kutilmoqda...*"
    )
    
    try:
        bot.send_message(ADMIN_ID, admin_text, reply_markup=inline_kb, parse_mode="Markdown")
        bot.send_message(
            user_id,
            "📩 **Arizangiz muhandislarga jo'natildi.**\n\n"
            "Arizangiz qabul qilinsa, sizga xabar beramiz!",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(user_id, "❌ Xatolik yuz berdi. Iltimos keyinroq qayta urinib ko'ring.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def callback_accept(call):
    it_worker_name = call.from_user.full_name
    user_id = int(call.data.split("_")[1])
    
    new_text = call.message.text.replace(
        "⏳ *Holat: Kutilmoqda...*", 
        f"✅ **Holat:** Qabul qilindi ({it_worker_name})"
    )
    
    bot.edit_message_text(new_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    bot.answer_callback_query(call.id, "Ariza qabul qilindi!")

    try:
        bot.send_message(
            chat_id=user_id,
            text=f"✅ **Arizangiz qabul qilindi!**\n\n👨‍💻 Muhandis **{it_worker_name}** yo'lda, tez orada xonangizga yetib boradi.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Xatolik: {e}")

# Render uchun veb-server qismi
async def handle(request):
    return web.Response(text="Bot ishlayapti!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000)))
    await site.start()

async def main():
    asyncio.create_task(web_server())
    # Botni polling qilish
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
