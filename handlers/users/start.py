from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from utils.subscription import check_subscription, get_subscribe_keyboard, check_and_request_subscription
from keyboards.inline.buttons import get_register_keyboard


@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()

    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name
    )

    if not await check_and_request_subscription(bot, db, message):
        return

    await message.answer(
        f"👋 Assalomu alaykum, <b>{message.from_user.full_name}</b>!\n\n"
        "📝 Ro'yxatdan o'tish uchun quyidagi tugmani bosing:",
        reply_markup=get_register_keyboard()
    )


@dp.callback_query_handler(text="check_subscription", state='*')
async def callback_check_subscription(callback: types.CallbackQuery, state: FSMContext):
    result = await check_subscription(bot, db, callback.from_user.id)

    if result["is_subscribed"]:
        await callback.message.edit_text(
            "✅ <b>Rahmat! Siz barcha kanallarga obuna bo'ldingiz.</b>\n\n"
            "📝 Ro'yxatdan o'tish uchun quyidagi tugmani bosing:",
            reply_markup=get_register_keyboard()
        )
    else:
        await callback.message.edit_text(
            "⚠️ <b>Siz hali barcha kanallarga obuna bo'lmadingiz!</b>\n\n"
            "Quyidagi kanallarga obuna bo'ling:",
            reply_markup=get_subscribe_keyboard(result["not_subscribed"])
        )

    await callback.answer()


@dp.message_handler(commands=['cancel'], state='*')
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer("🤷 Bekor qiladigan narsa yo'q.")
        return

    await state.finish()
    await message.answer(
        "❌ Bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /start buyrug'ini bosing."
    )