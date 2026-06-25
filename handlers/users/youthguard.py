from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from loader import dp
from data.config import YOUTHGUARD_API_URL


def webapp_kb(text: str, token: str, path: str = "") -> InlineKeyboardMarkup:
    """Telegram ichida ochiladigan Web App tugmasi (link emas)."""
    url = f"{YOUTHGUARD_API_URL}/accounts/magic/{token}/"
    if path:
        url += f"?next={path}"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text, web_app=WebAppInfo(url=url)))
    return kb
from states.states import YouthGuardMeetingState, YouthGuardVerifyState
from utils.youthguard_api import (get_token, get_my_youth, create_meeting, get_pending_verifications,
                                  verify_meeting, get_my_meetings, get_my_youth_stats, get_youth_stats,
                                  get_my_yetakchilar, get_my_stats)

_user_cache = {}
_photo_cache = {}
_youth_list_cache = {}

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


def main_keyboard(role: str) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if role == "yetakchi":
        kb.row(KeyboardButton("📊 Umumiy statistika"), KeyboardButton("👥 Biriktirilgan yoshlar"))
        kb.row(KeyboardButton("➕ Uchrashuv o'tkazish"), KeyboardButton("🤝 Uchrashuvlar"))
        kb.add(KeyboardButton("🖥 Web bot"))
    elif role == "rahbar":
        kb.row(KeyboardButton("📊 Umumiy statistika"), KeyboardButton("👥 Biriktirilgan yoshlar"))
        kb.row(KeyboardButton("➕ Uchrashuv o'tkazish"), KeyboardButton("👨‍🏫 Yoshlar yetakchilari"))
        kb.row(KeyboardButton("🤝 Uchrashuvlar"), KeyboardButton("🖥 Web bot"))
    elif role in ("admin", "super_admin"):
        kb.row(KeyboardButton("📊 Umumiy statistika"), KeyboardButton("👨‍🏫 Yoshlar yetakchilari"))
        kb.row(KeyboardButton("👥 Foydalanuvchilar"), KeyboardButton("✅ Tasdiqlash"))
        kb.add(KeyboardButton("🖥 Web bot"))
    kb.add(KeyboardButton("ℹ️ Mening profilim"))
    return kb


async def show_yg_menu(message: types.Message, me: dict, token: str):
    """YouthGuard rol menyusini ko'rsatadi (rahbar/yetakchi/admin/super_admin)."""
    user = message.from_user
    _user_cache[user.id] = me
    role = me.get("role", "")

    await message.answer(
        f"🌟 <b>YouthGuard tizimiga xush kelibsiz!</b>\n\n"
        f"👤 Ism: <b>{me.get('full_name') or user.full_name}</b>\n"
        f"{ROLE_ICONS.get(role, '🎭')} Rol: <b>{ROLE_NAMES.get(role, role)}</b>\n\n"
        f"Quyidagi amallardan birini tanlang:",
        reply_markup=main_keyboard(role)
    )
    if role in ("super_admin", "admin"):
        await message.answer(
            "🖥 Boshqaruv panelini ochish uchun tugmani bosing:",
            reply_markup=webapp_kb("🖥 Web botni ochish", token)
        )
    else:
        await message.answer(
            "🖥 Web botni ochish uchun tugmani bosing:",
            reply_markup=webapp_kb("🖥 Web botni ochish", token)
        )


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
            # YouthGuard xodimi — telefon shart emas, to'g'ridan menyu
            if role in ("super_admin", "admin", "rahbar", "yetakchi"):
                await show_yg_menu(message, info.get("user", {}), token)
                return
            if info.get("has_phone"):
                await message.answer(
                    "👤 Siz oddiy foydalanuvchi sifatida ro'yxatdasiz.\n"
                    "So'rovnomalarni to'ldirish uchun /start bosing."
                )
                return
        # Aks holda — telefon so'raymiz
        from handlers.users.yg_phone import request_phone
        await request_phone(message, state)
    except Exception as e:
        await message.answer(f"❌ YouthGuard tizimiga ulanib bo'lmadi: {e}")


@dp.message_handler(lambda m: m.text == "👥 Foydalanuvchilar", state="*")
async def yg_users_list(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me or me.get("role") not in ("admin", "super_admin"):
        await message.answer("Bu bo'lim faqat Admin/Super Admin uchun.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    await message.answer(
        "👥 <b>Foydalanuvchilar ro'yxati</b>\n\n"
        "Barcha admin, rahbar, yetakchi va oddiy foydalanuvchilarni "
        "ko'rish va boshqarish uchun tugmani bosing:",
        reply_markup=webapp_kb("👥 Foydalanuvchilarni ochish", token, "/accounts/users/")
    )


@dp.message_handler(lambda m: m.text == "📊 Umumiy statistika", state="*")
async def yg_statistika(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /start bosing.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        s = await get_my_stats(token)
        await message.answer(
            f"📊 <b>Umumiy statistika</b>\n\n"
            f"👥 Biriktirilgan yoshlar: <b>{s.get('youth_count', 0)}</b>\n"
            f"🤝 Jami uchrashuvlar: <b>{s.get('total_meetings', 0)}</b>\n"
            f"📅 Bu oyda: <b>{s.get('this_month', 0)}</b>\n"
            f"✅ Tasdiqlangan: <b>{s.get('verified', 0)}</b>\n"
            f"⏳ Kutilmoqda: <b>{s.get('pending', 0)}</b>",
            reply_markup=webapp_kb("📊 Batafsil (web bot)", token, "/uchrashuvlar/statistika/")
        )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


@dp.message_handler(lambda m: m.text == "👥 Biriktirilgan yoshlar", state="*")
async def yg_my_youth(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /start bosing.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        youths = await get_my_youth_stats(token)
        if not youths:
            await message.answer("Sizga biriktirilgan yoshlar yo'q.")
            return
        await message.answer(f"👥 <b>Biriktirilgan yoshlar:</b> {len(youths)} ta\n\nBatafsil ko'rish uchun bosing:")
        for y in youths[:30]:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton(
                f"🤝 {y.get('this_month', 0)} (bu oy) · jami {y.get('total_meetings', 0)}",
                callback_data=f"yg_youth:{y['id']}"
            ))
            last = y.get("last_date")
            last_txt = f"📅 oxirgi: {last} ({y.get('days_ago')} kun oldin)" if last else "📅 hali uchrashuv yo'q"
            await message.answer(
                f"👤 <b>{y['full_name']}</b>\n{last_txt}",
                reply_markup=kb
            )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("yg_youth:"))
async def yg_youth_detail(call: types.CallbackQuery):
    youth_id = int(call.data.split(":")[1])
    user = call.from_user
    token = await get_token(user.id, user.full_name, user.username)
    try:
        d = await get_youth_stats(token, youth_id)
        text = (
            f"👤 <b>{d.get('full_name', '-')}</b>\n"
            f"🎂 Yosh: {d.get('age', '-')} | 📁 {d.get('category', '-')}\n"
            f"🏢 {d.get('organization', '-')}\n\n"
            f"🤝 Jami uchrashuvlar: <b>{d.get('total_meetings', 0)}</b>\n"
            f"📅 Bu oyda: <b>{d.get('this_month', 0)}</b>\n\n"
        )
        meetings = d.get("meetings", [])
        if meetings:
            text += "<b>So'nggi uchrashuvlar:</b>\n"
            for m in meetings[:10]:
                text += f"• {m['date']} — {m['status']} ({m['days_ago']} kun oldin)\n"
        else:
            text += "Hali uchrashuv o'tkazilmagan."
        await call.message.answer(text)
    except Exception as e:
        await call.answer(f"Xato: {e}", show_alert=True)
    await call.answer()


@dp.message_handler(lambda m: m.text == "👨‍🏫 Yoshlar yetakchilari", state="*")
async def yg_yetakchilar(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me or me.get("role") not in ("rahbar", "admin", "super_admin"):
        await message.answer("Bu bo'lim faqat Rahbar/Admin uchun.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        yetakchilar = await get_my_yetakchilar(token)
        if not yetakchilar:
            await message.answer("Yetakchilar topilmadi.")
            return
        text = f"👨‍🏫 <b>Yoshlar yetakchilari:</b> {len(yetakchilar)} ta\n\n"
        for i, y in enumerate(yetakchilar[:30], 1):
            text += (
                f"{i}. <b>{y['name']}</b>\n"
                f"   👥 {y['youth_count']} yosh · 🤝 {y['total_meetings']} uchrashuv "
                f"(bu oy: {y['this_month']})\n\n"
            )
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


@dp.message_handler(lambda m: m.text == "🤝 Uchrashuvlar", state="*")
async def yg_uchrashuvlar(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /start bosing.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    await message.answer(
        "🤝 <b>Uchrashuvlar</b>\n\n"
        "Barcha uchrashuvlar, rasmlar, holatlar va hujjatlarni "
        "ko'rish uchun web botni oching:",
        reply_markup=webapp_kb("🤝 Uchrashuvlarni ochish", token, "/uchrashuvlar/")
    )


@dp.message_handler(lambda m: m.text == "🖥 Web bot", state="*")
async def yg_webbot(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /start bosing.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    await message.answer(
        "🖥 <b>Web bot</b>\n\nTo'liq boshqaruv panelini Telegram ichida oching:",
        reply_markup=webapp_kb("🖥 Web botni ochish", token)
    )


@dp.message_handler(lambda m: m.text == "ℹ️ Mening profilim", state="*")
async def my_profile(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /yg buyrug'i bilan tizimga kiring.")
        return
    role_names = {"super_admin": "Super Admin", "admin": "Admin", "rahbar": "Rahbar", "yetakchi": "Yetakchi"}
    await message.answer(
        f"👤 <b>Profil</b>\n\n"
        f"Ism: <b>{me.get('full_name', '')}</b>\n"
        f"Rol: <b>{role_names.get(me.get('role', ''), me.get('role', ''))}</b>\n"
        f"Telegram: @{me.get('telegram_username', '-')}\n"
        f"Tashkilot: <b>{me.get('organization', {}).get('name', '-') if me.get('organization') else '-'}</b>"
    )


# ==================== UCHRASHUV O'TKAZISH (rahbar va yetakchi) ====================

@dp.message_handler(lambda m: m.text == "➕ Uchrashuv o'tkazish", state="*")
async def start_create_meeting(message: types.Message, state: FSMContext):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me or me.get("role") not in ("rahbar", "yetakchi"):
        await message.answer("Bu funksiya faqat Rahbar va Yetakchilar uchun.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        youth_list = await get_my_youth_stats(token)
        if not youth_list:
            await message.answer("Sizga biriktirilgan yoshlar yo'q. Admin bilan bog'laning.")
            return
        _youth_list_cache[user.id] = youth_list
        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for y in youth_list[:10]:
            kb.add(KeyboardButton(f"{y['full_name']} [{y['id']}]"))
        kb.add(KeyboardButton("❌ Bekor qilish"))
        await message.answer("Uchrashuv o'tkaziladigan yoshni tanlang:", reply_markup=kb)
        await YouthGuardMeetingState.choosing_youth.set()
    except Exception as e:
        await message.answer(f"❌ Yoshlar ro'yxatini olishda xato: {e}")


@dp.message_handler(lambda m: m.text == "❌ Bekor qilish", state="*")
async def cancel_meeting(message: types.Message, state: FSMContext):
    await state.finish()
    me = _user_cache.get(message.from_user.id)
    role = me.get("role", "rahbar") if me else "rahbar"
    await message.answer("❌ Bekor qilindi.", reply_markup=main_keyboard(role))


@dp.message_handler(state=YouthGuardMeetingState.choosing_youth)
async def process_choose_youth(message: types.Message, state: FSMContext):
    text = message.text
    try:
        youth_id = int(text.split("[")[-1].rstrip("]"))
    except (ValueError, IndexError):
        await message.answer("Noto'g'ri tanlov. Ro'yxatdan tanlang.")
        return
    await state.update_data(youth_id=youth_id, youth_name=text.split("[")[0].strip())
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))
    kb.add(KeyboardButton("❌ Bekor qilish"))
    await message.answer(
        f"✅ Yoshlash tanlandi: <b>{text.split('[')[0].strip()}</b>\n\n"
        "📍 Endi hozirgi lokatsiyangizni yuboring:",
        reply_markup=kb
    )
    await YouthGuardMeetingState.sending_location.set()


@dp.message_handler(content_types=types.ContentType.LOCATION, state=YouthGuardMeetingState.sending_location)
async def process_location(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lng = message.location.longitude
    await state.update_data(latitude=lat, longitude=lng)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("❌ Bekor qilish"))
    await message.answer(
        f"✅ Lokatsiya qabul qilindi ({lat:.4f}, {lng:.4f})\n\n"
        "📸 Uchrashuv rasmini yuboring:",
        reply_markup=kb
    )
    await YouthGuardMeetingState.sending_photo.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=YouthGuardMeetingState.sending_photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    file_id = photo.file_id
    await state.update_data(photo_file_id=file_id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("➡️ O'tkazib yuborish"))
    kb.add(KeyboardButton("❌ Bekor qilish"))
    await message.answer(
        "✅ Rasm qabul qilindi.\n\n"
        "📝 Izoh qo'shing (yoki o'tkazib yuboring):",
        reply_markup=kb
    )
    await YouthGuardMeetingState.adding_notes.set()


@dp.message_handler(state=YouthGuardMeetingState.adding_notes)
async def process_notes(message: types.Message, state: FSMContext):
    notes = "" if message.text == "➡️ O'tkazib yuborish" else message.text
    data = await state.get_data()
    user = message.from_user

    await message.answer("⏳ Uchrashuv saqlanmoqda...")

    token = await get_token(user.id, user.full_name, user.username)

    # Rasmni yuklab olamiz
    photo_file_id = data.get("photo_file_id")
    photo_bytes = None
    if photo_file_id:
        from loader import bot
        file = await bot.get_file(photo_file_id)
        photo_bytes = await bot.download_file(file.file_path)

    payload = {
        "youth": data["youth_id"],
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "notes": notes,
    }
    if photo_bytes:
        payload["photo"] = {"data": photo_bytes.read(), "filename": "meeting.jpg"}

    try:
        result = await create_meeting(token, payload)
        me = _user_cache.get(user.id, {})
        if result.get("id"):
            await message.answer(
                f"✅ <b>Uchrashuv muvaffaqiyatli saqlandi!</b>\n\n"
                f"🆔 ID: {result['id']}\n"
                f"👤 Yosh: {data['youth_name']}\n"
                f"📍 GPS: {data['latitude']:.4f}, {data['longitude']:.4f}\n"
                f"⏳ Status: Yetakchi tasdiqlashini kutmoqda",
                reply_markup=main_keyboard(me.get("role", "rahbar"))
            )
        else:
            err = str(result)
            await message.answer(
                f"❌ Saqlashda xato: {err}",
                reply_markup=main_keyboard(me.get("role", "rahbar"))
            )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    finally:
        await state.finish()


# ==================== RAHBAR: O'Z UCHRASHUVLARI ====================

@dp.message_handler(lambda m: m.text == "📋 Mening uchrashuvlarim", state="*")
async def my_meetings(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /yg buyrug'i bilan tizimga kiring.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        meetings = await get_my_meetings(token)
        if not meetings:
            await message.answer("Hali hech qanday uchrashuv yo'q.")
            return
        status_icons = {
            "pending": "⏳", "verified": "✅", "rejected": "❌",
            "impossible": "🚫", "force_approved": "💪"
        }
        text = "📋 <b>Mening uchrashuvlarim:</b>\n\n"
        for m in meetings[:10]:
            icon = status_icons.get(m.get("status", ""), "❓")
            text += f"{icon} {m.get('youth_name', '-')} — {m.get('date', '-')}\n"
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


# ==================== YETAKCHI: TASDIQLASH ====================

@dp.message_handler(lambda m: m.text in ("✅ Tasdiqlash", "✅ Tasdiqlash kutmoqda", "📋 Barcha uchrashuvlar"), state="*")
async def pending_verifications(message: types.Message):
    user = message.from_user
    me = _user_cache.get(user.id)
    if not me:
        await message.answer("Avval /yg buyrug'i bilan tizimga kiring.")
        return
    token = await get_token(user.id, user.full_name, user.username)
    try:
        verifications = await get_pending_verifications(token)
        if not verifications:
            await message.answer("✅ Hozircha tasdiqlash kutayotgan uchrashuv yo'q.")
            return
        for v in verifications[:5]:
            mid = v.get("meeting_id") or v.get("id")
            youth = v.get("youth_name", "-")
            rahbar = v.get("rahbar_name", "-")
            date = v.get("date", "-")
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"yg_verify:{mid}:approve"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"yg_verify:{mid}:reject"),
            )
            await message.answer(
                f"📋 <b>Uchrashuv #{mid}</b>\n"
                f"👤 Yosh: {youth}\n"
                f"👨 Rahbar: {rahbar}\n"
                f"📅 Sana: {date}",
                reply_markup=kb
            )
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")


@dp.callback_query_handler(lambda c: c.data.startswith("yg_verify:"))
async def callback_verify(call: types.CallbackQuery, state: FSMContext):
    _, meeting_id, action = call.data.split(":")
    if action == "approve":
        user = call.from_user
        token = await get_token(user.id, user.full_name, user.username)
        try:
            result = await verify_meeting(token, int(meeting_id), "approve")
            if result.get("status") == "verified" or result.get("success"):
                await call.message.edit_text(f"✅ Uchrashuv #{meeting_id} tasdiqlandi!")
            else:
                await call.message.edit_text(f"❌ Xato: {result}")
        except Exception as e:
            await call.answer(f"Xato: {e}")
    elif action == "reject":
        await state.update_data(reject_meeting_id=int(meeting_id))
        await call.message.answer("❌ Rad etish sababini yozing:")
        await YouthGuardVerifyState.reject_reason.set()
        await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()


@dp.message_handler(state=YouthGuardVerifyState.reject_reason)
async def process_reject_reason(message: types.Message, state: FSMContext):
    data = await state.get_data()
    meeting_id = data.get("reject_meeting_id")
    user = message.from_user
    token = await get_token(user.id, user.full_name, user.username)
    try:
        result = await verify_meeting(token, meeting_id, "reject", message.text)
        me = _user_cache.get(user.id, {})
        if result.get("status") == "rejected" or result.get("success"):
            await message.answer(
                f"❌ Uchrashuv #{meeting_id} rad etildi.",
                reply_markup=main_keyboard(me.get("role", "yetakchi"))
            )
        else:
            await message.answer(f"Xato: {result}")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    finally:
        await state.finish()
