from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, db, bot
from states.states import RegisterState
from utils.subscription import check_and_request_subscription
from keyboards.inline.buttons import get_options_keyboard, get_confirm_response_keyboard


@dp.callback_query_handler(text="user:register", state='*')
async def start_register(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    if not await check_and_request_subscription(bot, db, callback.message):
        await callback.answer()
        return

    survey = await db.get_active_survey()

    if not survey:
        await callback.message.edit_text(
            "⚠️ Hozirda aktiv so'rovnoma yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        await callback.answer()
        return

    fields = await db.get_survey_fields(survey['id'])

    if not fields:
        await callback.message.edit_text(
            "⚠️ So'rovnomada savollar yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        await callback.answer()
        return

    await state.update_data(
        survey_id=survey['id'],
        survey_name=survey['name'],
        fields=[dict(f) for f in fields],
        current_field=0,
        answers={}
    )

    await send_question(callback.message, state, edit=True)
    await RegisterState.answering.set()
    await callback.answer()


@dp.message_handler(commands=['register'], state='*')
async def cmd_register(message: types.Message, state: FSMContext):
    await state.finish()

    if not await check_and_request_subscription(bot, db, message):
        return

    survey = await db.get_active_survey()

    if not survey:
        await message.answer(
            "⚠️ Hozirda aktiv so'rovnoma yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    fields = await db.get_survey_fields(survey['id'])

    if not fields:
        await message.answer(
            "⚠️ So'rovnomada savollar yo'q.\n"
            "Iltimos, keyinroq qayta urinib ko'ring."
        )
        return

    await state.update_data(
        survey_id=survey['id'],
        survey_name=survey['name'],
        fields=[dict(f) for f in fields],
        current_field=0,
        answers={}
    )

    await send_question(message, state, edit=False)
    await RegisterState.answering.set()


async def send_question(message: types.Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    fields = data['fields']
    current = data['current_field']

    if current >= len(fields):
        await show_confirmation(message, state, edit)
        return

    field = fields[current]
    question_num = current + 1
    total = len(fields)

    text = (
        f"📋 <b>{data['survey_name']}</b>\n\n"
        f"❓ Savol {question_num}/{total}:\n\n"
        f"<b>{field['question_text']}</b>"
    )

    if field['field_type'] == 'choice' and field['options']:
        keyboard = get_options_keyboard(field['options'], current)
        if edit:
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
    else:
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)


async def show_confirmation(message: types.Message, state: FSMContext, edit: bool = False):
    data = await state.get_data()
    fields = data['fields']
    answers = data['answers']

    text = f"📋 <b>{data['survey_name']}</b>\n\n"
    text += "✅ <b>Javoblaringizni tekshiring:</b>\n\n"

    for i, field in enumerate(fields):
        answer = answers.get(str(i), "—")
        text += f"<b>{field['column_name']}:</b> {answer}\n"

    text += "\n❓ Tasdiqlaysizmi?"

    if edit:
        await message.edit_text(text, reply_markup=get_confirm_response_keyboard())
    else:
        await message.answer(text, reply_markup=get_confirm_response_keyboard())


@dp.callback_query_handler(lambda c: c.data.startswith("answer:"), state=RegisterState.answering)
async def process_choice_answer(callback: types.CallbackQuery, state: FSMContext):
    _, field_order, option_index = callback.data.split(":")
    field_order = int(field_order)
    option_index = int(option_index)

    data = await state.get_data()
    fields = data['fields']

    field = fields[field_order]
    answer = field['options'][option_index]

    answers = data.get('answers', {})
    answers[str(field_order)] = answer

    await state.update_data(
        answers=answers,
        current_field=field_order + 1
    )

    await send_question(callback.message, state, edit=True)
    await callback.answer()


@dp.message_handler(state=RegisterState.answering)
async def process_text_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current = data['current_field']

    answers = data.get('answers', {})
    answers[str(current)] = message.text

    await state.update_data(
        answers=answers,
        current_field=current + 1
    )

    await send_question(message, state, edit=False)


@dp.callback_query_handler(text="response:confirm", state=RegisterState.answering)
async def confirm_response(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    response_data = {}
    for i, field in enumerate(data['fields']):
        response_data[field['column_name']] = data['answers'].get(str(i), "")

    await db.add_survey_response(
        survey_id=data['survey_id'],
        user_id=callback.from_user.id,
        response_data=response_data
    )

    await callback.message.edit_text(
        "✅ <b>Rahmat!</b>\n\n"
        "Sizning javoblaringiz muvaffaqiyatli saqlandi! 🎉"
    )

    await state.finish()
    await callback.answer("Muvaffaqiyatli saqlandi!")


@dp.callback_query_handler(text="response:cancel", state=RegisterState.answering)
async def cancel_response(callback: types.CallbackQuery, state: FSMContext):
    await state.finish()

    await callback.message.edit_text(
        "❌ Bekor qilindi.\n\n"
        "Qaytadan boshlash uchun /register buyrug'ini bosing."
    )
    await callback.answer()