import json

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                           WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove)

from loader import dp
from data.config import YOUTHGUARD_API_URL
from states.states import YouthGuardMeetingState

ROLE_NAMES = {
    "super_admin": "Super Admin",
    "admin": "Admin",
    "rahbar": "Rahbar",
    "yetakchi": "Yetakchi",
    "user": "Foydalanuvchi",
}
ROLE_ICONS = {
    "super_admin": "👑",
    "admin": "🛡",
    "rahbar": "👔",
    "yetakchi": "✅",
    "user": "👤",
}
# Rolga qarab ochiluvchi web sahifa
ROLE_PATHS = {
    "super_admin": "",
    "admin": "",
    "rahbar": "/yoshlar/",
    "yetakchi": "/yoshlar/",
}


def webapp_kb(text: str, token: str, path: str = "") -> InlineKeyboardMarkup:
    """Telegram ichida ochiladigan Web App tugmasi."""
    url = f"{YOUTHGUARD_API_URL}/accounts/magic/{token}/"
    if path:
        url += f"?next={path}"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text, web_app=WebAppInfo(url=url)))
    return kb


async def show_yg_menu(message: types.Message, me: dict, token: str):
    """Faqat web app tugmasini ko'rsatadi — boshqa tugmalar yo'q."""
    user = message.from_user
    role = me.get("role", "")
    name = me.get("full_name") or user.full_name
    path = ROLE_PATHS.get(role, "")
    org = me.get("organization")
    org_name = org.get("name", "") if isinstance(org, dict) else ""

    lines = [
        f"👤 Ism: <b>{name}</b>",
        f"{ROLE_ICONS.get(role, '🎭')} Rol: <b>{ROLE_NAMES.get(role, role)}</b>",
    ]
    if org_name:
        lines.append(f"🏢 Tashkilot: <b>{org_name}</b>")

    await message.answer(
        "🌟 <b>YouthGuard tizimiga xush kelibsiz!</b>\n\n" + "\n".join(lines),
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "🖥 Web botni ochish uchun tugmani bosing:",
        reply_markup=webapp_kb("🖥 Web botni ochish", token, path)
    )


# ──── /yg buyrug'i ────

@dp.message_handler(commands=["yg"], state="*")
async def cmd_youthguard(message: types.Message, state: FSMContext):
    await state.finish()
    user = message.from_user
    try:
        from utils.youthguard_api import check_telegram
        info = await check_telegram(user.id)
        if info.get("exists"):
            role = info.get("role")
            token = info.get("token")
            if role in ("super_admin", "admin", "rahbar", "yetakchi"):
                await show_yg_menu(message, info.get("user", {}), token)
                return
            if info.get("has_phone"):
                await message.answer(
                    "👤 Siz oddiy foydalanuvchi sifatida ro'yxatdasiz.\n"
                    "Tizimda sizga rol biriktirilgandan so'ng imkoniyatlar ochiladi.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return
        from handlers.users.yg_phone import request_phone
        await request_phone(message, state)
    except Exception as e:
        await message.answer(f"❌ YouthGuard tizimiga ulanib bo'lmadi: {e}")


# ──── Web App dan kelgan ma'lumotlar ────

@dp.message_handler(content_types=types.ContentType.WEB_APP_DATA, state="*")
async def handle_webapp_data(message: types.Message, state: FSMContext):
    """Web botdagi 'Uchrashuvni boshlash' tugmasidan kelgan signal."""
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        return

    if data.get("action") == "start_meeting":
        youth_id = data.get("youth_id")
        youth_name = data.get("youth_name", "Yosh")
        if not youth_id:
            await message.answer("❌ Yosh ma'lumoti topilmadi.")
            return

        user = message.from_user
        try:
            from utils.youthguard_api import get_token, get_active_survey
            token = await get_token(user.id, user.full_name, user.username)

            # Faol so'rovnomani olish
            survey = await get_active_survey(token)
            if survey and survey.get("active") and survey.get("questions"):
                questions = survey["questions"]
                await state.update_data(
                    youth_id=youth_id,
                    youth_name=youth_name,
                    token=token,
                    survey_id=survey.get("id"),
                    survey_questions=questions,
                    current_q=0,
                    answers={},
                )
                await YouthGuardMeetingState.answering_survey.set()
                await _ask_question(message, questions, 0, youth_name)
            else:
                # Standart oqim: lokatsiya → rasm → izoh
                await state.update_data(
                    youth_id=youth_id,
                    youth_name=youth_name,
                    token=token,
                )
                kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
                kb.add(KeyboardButton("❌ Bekor qilish"))
                await message.answer(
                    f"🤝 <b>{youth_name}</b> bilan uchrashuv!\n\n"
                    "📍 Hozirgi lokatsiyangizni yuboring:",
                    reply_markup=kb
                )
                await YouthGuardMeetingState.sending_location.set()
        except Exception as e:
            await message.answer(f"❌ Xato: {e}")


# ──── So'rovnoma savollari ────

async def _ask_question(message: types.Message, questions: list, idx: int, youth_name: str):
    if idx >= len(questions):
        return
    q = questions[idx]
    q_type = q.get("type", "text")
    q_text = q.get("text", "")
    required = q.get("required", True)
    total = len(questions)

    header = f"❓ {idx + 1}/{total}: <b>{q_text}</b>"
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    if q_type == "location":
        kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    elif q_type == "choice":
        for ch in (q.get("choices") or []):
            kb.add(KeyboardButton(str(ch)))
    else:
        pass  # text/photo/number — foydalanuvchi o'zi yozadi/yuboradi

    if not required:
        kb.add(KeyboardButton("➡️ O'tkazib yuborish"))
    kb.add(KeyboardButton("❌ Bekor qilish"))

    if q_type == "photo":
        await message.answer(f"{header}\n📸 Rasm yuboring:", reply_markup=kb)
    elif q_type == "location":
        await message.answer(f"{header}", reply_markup=kb)
    else:
        await message.answer(f"{header}", reply_markup=kb)


@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state="*")
async def cancel_any(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    # Web app tugmasini qayta ko'rsatish
    try:
        from utils.youthguard_api import check_telegram
        info = await check_telegram(message.from_user.id)
        if info.get("exists") and info.get("role") in ("rahbar", "yetakchi", "admin", "super_admin"):
            await show_yg_menu(message, info.get("user", {}), info.get("token"))
    except Exception:
        pass


@dp.message_handler(content_types=types.ContentType.LOCATION,
                    state=YouthGuardMeetingState.answering_survey)
async def survey_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("survey_questions", [])
    current_q = data.get("current_q", 0)
    answers = data.get("answers", {})

    answers[str(current_q)] = {
        "type": "location",
        "lat": message.location.latitude,
        "lng": message.location.longitude,
        "question": questions[current_q].get("text") if current_q < len(questions) else "",
    }
    await _next_question(message, state, questions, current_q, answers)


@dp.message_handler(content_types=types.ContentType.PHOTO,
                    state=YouthGuardMeetingState.answering_survey)
async def survey_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("survey_questions", [])
    current_q = data.get("current_q", 0)
    answers = data.get("answers", {})

    answers[str(current_q)] = {
        "type": "photo",
        "file_id": message.photo[-1].file_id,
        "question": questions[current_q].get("text") if current_q < len(questions) else "",
    }
    await _next_question(message, state, questions, current_q, answers)


@dp.message_handler(state=YouthGuardMeetingState.answering_survey)
async def survey_text(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_any(message, state)
        return
    data = await state.get_data()
    questions = data.get("survey_questions", [])
    current_q = data.get("current_q", 0)
    answers = data.get("answers", {})

    val = "" if message.text == "➡️ O'tkazib yuborish" else message.text
    answers[str(current_q)] = {
        "type": questions[current_q].get("type", "text") if current_q < len(questions) else "text",
        "value": val,
        "question": questions[current_q].get("text") if current_q < len(questions) else "",
    }
    await _next_question(message, state, questions, current_q, answers)


async def _next_question(message, state, questions, current_q, answers):
    current_q += 1
    await state.update_data(current_q=current_q, answers=answers)
    if current_q >= len(questions):
        await _save_survey_meeting(message, state)
    else:
        data = await state.get_data()
        await _ask_question(message, questions, current_q, data.get("youth_name", ""))


async def _save_survey_meeting(message: types.Message, state: FSMContext):
    """So'rovnoma tugagach uchrashuvni saqlaydi."""
    from utils.youthguard_api import create_meeting

    data = await state.get_data()
    user = message.from_user
    token = data.get("token") or ""
    if not token:
        from utils.youthguard_api import get_token
        token = await get_token(user.id, user.full_name, user.username)

    youth_id = data.get("youth_id")
    youth_name = data.get("youth_name", "")
    answers = data.get("answers", {})

    lat, lng = None, None
    photo_bytes = None
    notes_parts = []

    for ans in answers.values():
        t = ans.get("type")
        if t == "location":
            lat, lng = ans.get("lat"), ans.get("lng")
        elif t == "photo":
            file_id = ans.get("file_id")
            if file_id:
                from loader import bot
                file = await bot.get_file(file_id)
                photo_bytes = await bot.download_file(file.file_path)
        elif ans.get("value"):
            notes_parts.append(f"{ans.get('question', '')}: {ans.get('value')}")

    payload = {"youth": youth_id, "notes": "\n".join(notes_parts)}
    if lat is not None:
        payload["latitude"] = lat
        payload["longitude"] = lng
    if photo_bytes:
        payload["photo"] = {"data": photo_bytes.read(), "filename": "meeting.jpg"}

    await message.answer("⏳ Uchrashuv saqlanmoqda...")
    try:
        result = await create_meeting(token, payload)
        if result.get("id"):
            await message.answer(
                f"✅ <b>Uchrashuv saqlandi!</b>\n\n"
                f"🆔 ID: {result['id']}\n"
                f"👤 Yosh: {youth_name}\n"
                f"⏳ Yetakchi tasdiqlashini kutmoqda",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(f"❌ Xato: {result}")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    finally:
        await state.finish()

    # Qayta web app tugmasi
    try:
        from utils.youthguard_api import check_telegram
        info = await check_telegram(user.id)
        if info.get("exists") and info.get("role") in ("rahbar", "yetakchi", "admin", "super_admin"):
            await show_yg_menu(message, info.get("user", {}), info.get("token"))
    except Exception:
        pass


# ──── Standart oqim: lokatsiya → rasm → izoh ────

@dp.message_handler(content_types=types.ContentType.LOCATION,
                    state=YouthGuardMeetingState.sending_location)
async def process_location(message: types.Message, state: FSMContext):
    lat, lng = message.location.latitude, message.location.longitude
    await state.update_data(latitude=lat, longitude=lng)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("❌ Bekor qilish"))
    await message.answer(
        f"✅ Lokatsiya qabul qilindi ({lat:.4f}, {lng:.4f})\n\n"
        "📸 Uchrashuv rasmini yuboring:",
        reply_markup=kb
    )
    await YouthGuardMeetingState.sending_photo.set()


@dp.message_handler(content_types=types.ContentType.PHOTO,
                    state=YouthGuardMeetingState.sending_photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("➡️ O'tkazib yuborish"))
    kb.add(KeyboardButton("❌ Bekor qilish"))
    await message.answer(
        "✅ Rasm qabul qilindi.\n\n📝 Izoh qo'shing (yoki o'tkazib yuboring):",
        reply_markup=kb
    )
    await YouthGuardMeetingState.adding_notes.set()


@dp.message_handler(state=YouthGuardMeetingState.adding_notes)
async def process_notes(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await cancel_any(message, state)
        return
    notes = "" if message.text == "➡️ O'tkazib yuborish" else message.text
    data = await state.get_data()
    user = message.from_user
    token = data.get("token") or ""
    if not token:
        from utils.youthguard_api import get_token
        token = await get_token(user.id, user.full_name, user.username)

    photo_bytes = None
    if data.get("photo_file_id"):
        from loader import bot
        file = await bot.get_file(data["photo_file_id"])
        photo_bytes = await bot.download_file(file.file_path)

    payload = {
        "youth": data["youth_id"],
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "notes": notes,
    }
    if photo_bytes:
        payload["photo"] = {"data": photo_bytes.read(), "filename": "meeting.jpg"}

    await message.answer("⏳ Uchrashuv saqlanmoqda...")
    try:
        from utils.youthguard_api import create_meeting
        result = await create_meeting(token, payload)
        if result.get("id"):
            await message.answer(
                f"✅ <b>Uchrashuv saqlandi!</b>\n\n"
                f"🆔 ID: {result['id']}\n"
                f"👤 Yosh: {data.get('youth_name', '')}\n"
                f"⏳ Yetakchi tasdiqlashini kutmoqda",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await message.answer(f"❌ Xato: {result}")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    finally:
        await state.finish()

    try:
        from utils.youthguard_api import check_telegram
        info = await check_telegram(user.id)
        if info.get("exists") and info.get("role") in ("rahbar", "yetakchi", "admin", "super_admin"):
            await show_yg_menu(message, info.get("user", {}), info.get("token"))
    except Exception:
        pass
