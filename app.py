from aiogram import executor

from loader import dp, db
from data.config import ADMINS
import handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    # Database jadvallarini yaratish
    await db.create()
    await db.create_all_tables()

    # Super adminni qo'shish
    for admin_id in ADMINS:
        await db.add_admin(telegram_id=int(admin_id), is_super=True)

    # Bot buyruqlarini o'rnatish
    await set_default_commands(dispatcher)

    # Adminga xabar berish
    await on_startup_notify(dispatcher)

    print("Bot ishga tushdi!")


async def on_shutdown(dispatcher):
    print("Bot to'xtatildi!")


if __name__ == '__main__':
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
