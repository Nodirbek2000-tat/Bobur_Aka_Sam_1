from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from loader import dp
from states.states import PhoneRegisterState
from utils.youthguard_api import phone_lookup


async def request_phone(message: types.Message, state: FSMContext):
    """Telefon raqam so'raydi (contact tugma)."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Tizimga kirish uchun telefon raqamingizni yuboring.\n"
        "Quyidagi tugmani bosing 👇",
        reply_markup=kb
    )
    await PhoneRegisterState.waiting_phone.set()


@dp.message_handler(content_types=types.ContentType.CONTACT, state=PhoneRegisterState.waiting_phone)
async def process_contact(message: types.Message, state: FSMContext):
    contact = message.contact
    # Faqat o'z raqamini yuborishi mumkin
    if contact.user_id and contact.user_id != message.from_user.id:
        await message.answer("⚠️ Iltimos, faqat o'zingizning raqamingizni yuboring!")
        return

    phone = contact.phone_number
    user = message.from_user

    await message.answer("⏳ Tekshirilmoqda...", reply_markup=ReplyKeyboardRemove())

    try:
        data = await phone_lookup(user.id, phone, user.full_name, user.username)
    except Exception as e:
        await message.answer(f"❌ Server bilan bog'lanishda xato: {e}")
        await state.finish()
        return

    role = data.get("role", "user")
    token = data.get("token")
    me = data.get("user", {})

    await state.finish()

    if role in ("super_admin", "admin", "rahbar", "yetakchi"):
        # YouthGuard xodimi — rol menyusi
        from handlers.users.youthguard import show_yg_menu
        await show_yg_menu(message, me, token)
    else:
        # Oddiy foydalanuvchi — so'rovnoma oqimiga o'tadi
        await message.answer(
            "✅ Raqamingiz qabul qilindi!\n\n"
            "Botdan foydalanish uchun davom etamiz..."
        )
        from handlers.users.start import survey_start
        await survey_start(message, state)


@dp.message_handler(state=PhoneRegisterState.waiting_phone)
async def phone_not_shared(message: types.Message, state: FSMContext):
    """Telefon o'rniga matn yuborsa — eslatma."""
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True))
    await message.answer(
        "⚠️ Iltimos, pastdagi <b>📱 Telefon raqamni yuborish</b> tugmasini bosing.",
        reply_markup=kb
    )
