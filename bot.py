import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# 1. BotFather'dan olgan Tokeningizni yozing
TOKEN = "8526475774:AAHCkbLaqwbvEremOykACXYwR4b9a4ZC7SA" 

# 2. IT Guruhingiz ID raqami (masalan: -1001234567890)
GROUP_ID = -1003921854512  

class TicketForm(StatesGroup):
    room = State()
    name = State()
    problem = State()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Asosiy menyu
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛠 Murojaat yuborish")]],
        resize_keyboard=True
    )

# /start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, **{message.from_user.full_name}**!\n\n"
        "Kompyuteringizda nosozlik bo'lsa, pastdagi tugmani bosib IT bo'limiga murojaat yuboring.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Murojaatni boshlash
@dp.message(F.text == "🛠 Murojaat yuborish")
async def start_ticket(message: types.Message, state: FSMContext):
    await state.set_state(TicketForm.room)
    await message.answer("📍 Iltimos, kompyuter buzilgan **xona raqamini** yuboring (masalan: *304-xona*):", parse_mode="Markdown")

# Xona raqamini qabul qilish
@dp.message(TicketForm.room)
async def process_room(message: types.Message, state: FSMContext):
    await state.update_data(room=message.text)
    await state.set_state(TicketForm.name)
    await message.answer("👤 Iltimos, **Ism va familiyangizni** kiriting:")

# Ismni qabul qilish
@dp.message(TicketForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(TicketForm.problem)
    await message.answer("⚠️ Kompyuterda qanday **muammo** borligini qisqacha yozib yuboring (masalan: *Internet ishlamayapti*):")

# Muammoni qabul qilish va IT guruhiga yuborish
@dp.message(TicketForm.problem)
async def process_problem(message: types.Message, state: FSMContext):
    data = await state.get_data()
    room = data.get("room")
    name = data.get("name")
    problem = message.text
    user_id = message.from_user.id
    username = message.from_user.username
    user_link = f"@{username}" if username else f"ID: {user_id}"

    # IT guruhidagi muhandislar uchun tugma
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠 Qabul qilish", callback_data=f"accept_{user_id}")]
    ])

    group_text = (
        f"🚨 **Yangi Kompyuter Nosozligi!**\n\n"
        f"🏢 **Xona:** {room}\n"
        f"👤 **Xodim:** {name} ({user_link})\n"
        f"💬 **Muammo:** {problem}\n\n"
        f"⏳ *Holat: Kutilmoqda...*"
    )
    
    try:
        # IT guruhiga yuborish
        await bot.send_message(GROUP_ID, group_text, reply_markup=inline_kb, parse_mode="Markdown")
        
        # Xodimga boradigan xabar
        await message.answer(
            "📩 **Arizangiz muhandislarga jo'natildi.**\n\n"
            "Arizangiz qabul qilinsa, sizga xabar beramiz!",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi. Bot IT guruhiga xabar yubora olmadi. Bot guruhga qo'shilganini va GROUP_ID to'g'riligini tekshiring.")
    
    await state.clear()

# Muhandis guruhda "Qabul qilish" tugmasini bosganda
@dp.callback_query(F.data.startswith("accept_"))
async def accept_ticket(callback: types.CallbackQuery):
    it_worker_name = callback.from_user.full_name
    user_id = int(callback.data.split("_")[1])
    
    # Guruhdagi xabarni yangilash
    new_text = callback.message.text.replace(
        "⏳ *Holat: Kutilmoqda...*", 
        f"✅ **Holat:** Muhandis {it_worker_name} tomonidan qabul qilindi!"
    )
    
    await callback.message.edit_text(new_text, parse_mode="Markdown")
    await callback.answer("Ariza qabul qilindi!")

    # Xodimga shaxsiy xabar yuborish (Arizangiz qabul qilindi deb)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ **Arizangiz qabul qilindi!**\n\n👨‍💻 Muhandis **{it_worker_name}** yo'lda, tez orada xonangizga yetib boradi.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"Xodimga xabar yuborishda xatolik: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())