from aiogram import executor

from loader import dp, db
from data.config import ADMINS
import handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    # Database ulanishini sinab ko'rish (PostgreSQL ishlamasa ham bot ishlaydi)
    try:
        await db.create()
        await db.create_all_tables()
        for admin_id in ADMINS:
            await db.add_admin(telegram_id=int(admin_id), is_super=True)
        print("✅ PostgreSQL ulandi!")
    except Exception as e:
        print(f"⚠️  PostgreSQL ulanmadi: {e}")
        print("⚠️  DB funksiyalar ishlamaydi, lekin bot ishlaydi!")

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
