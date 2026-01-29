from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ==================== ADMIN PANEL TUGMALARI ====================

def get_admin_menu():
    """Admin panel asosiy menyu"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📊 Statistika", callback_data="admin:stats"),
        InlineKeyboardButton("📋 So'rovnomalar", callback_data="admin:surveys"),
    )
    keyboard.add(
        InlineKeyboardButton("📢 Kanallar", callback_data="admin:channels"),
        InlineKeyboardButton("👥 Adminlar", callback_data="admin:admins"),
    )
    keyboard.add(
        InlineKeyboardButton("❌ Yopish", callback_data="admin:close")
    )
    return keyboard


def get_back_to_admin():
    """Admin panelga qaytish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")]
        ]
    )


# ==================== STATISTIKA ====================

def get_stats_menu():
    """Statistika menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📥 Excel yuklash", callback_data="stats:download"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


# ==================== SO'ROVNOMALAR ====================

def get_surveys_menu():
    """So'rovnomalar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Yangi so'rovnoma", callback_data="survey:create"),
        InlineKeyboardButton("📋 So'rovnomalar ro'yxati", callback_data="survey:list"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_survey_list_keyboard(surveys: list):
    """So'rovnomalar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for survey in surveys:
        status = "✅" if survey['is_active'] else "⏸"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {survey['name']}",
                callback_data=f"survey:view:{survey['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:surveys")
    )
    return keyboard


def get_survey_actions(survey_id: int, is_active: bool):
    """So'rovnoma bilan amallar"""
    keyboard = InlineKeyboardMarkup(row_width=2)

    if is_active:
        keyboard.add(
            InlineKeyboardButton("⏸ Deaktiv qilish", callback_data=f"survey:deactivate:{survey_id}")
        )
    else:
        keyboard.add(
            InlineKeyboardButton("✅ Aktiv qilish", callback_data=f"survey:activate:{survey_id}")
        )

    keyboard.add(
        InlineKeyboardButton("📥 Excel", callback_data=f"survey:excel:{survey_id}"),
        InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"survey:edit:{survey_id}"),
    )
    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"survey:delete:{survey_id}"),
    )
    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="survey:list")
    )
    return keyboard


def get_survey_delete_confirm(survey_id: int):
    """So'rovnomani o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"survey:delete_confirm:{survey_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"survey:view:{survey_id}")
    )
    return keyboard


# ==================== SO'ROVNOMA YARATISH ====================

def get_field_type_keyboard():
    """Maydon turini tanlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📝 Matn", callback_data="field_type:text"),
        InlineKeyboardButton("🔘 Variantlar", callback_data="field_type:choice")
    )
    keyboard.add(
        InlineKeyboardButton("❌ Bekor qilish", callback_data="survey:cancel_create")
    )
    return keyboard


def get_add_more_fields_keyboard():
    """Yana ustun qo'shish"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Yana ustun qo'shish", callback_data="field:add_more"),
        InlineKeyboardButton("✅ Tayyor - Yakunlash", callback_data="field:finish"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="survey:cancel_create")
    )
    return keyboard


def get_add_option_keyboard():
    """Variant qo'shish"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Yana variant qo'shish", callback_data="option:add_more"),
        InlineKeyboardButton("✅ Variantlar tayyor", callback_data="option:finish"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="survey:cancel_create")
    )
    return keyboard


def get_survey_confirm_keyboard():
    """So'rovnomani tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="survey:confirm_create"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="survey:cancel_create")
    )
    return keyboard


# ==================== KANALLAR ====================

def get_channels_menu():
    """Kanallar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Kanal qo'shish", callback_data="channel:add"),
        InlineKeyboardButton("📋 Kanallar ro'yxati", callback_data="channel:list"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_channel_list_keyboard(channels: list):
    """Kanallar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for channel in channels:
        keyboard.add(
            InlineKeyboardButton(
                f"📢 {channel['channel_name']}",
                callback_data=f"channel:view:{channel['id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:channels")
    )
    return keyboard


def get_channel_actions(channel_id: int):
    """Kanal bilan amallar"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"channel:delete:{channel_id}"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="channel:list")
    )
    return keyboard


def get_channel_delete_confirm(channel_id: int):
    """Kanalni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"channel:delete_confirm:{channel_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"channel:view:{channel_id}")
    )
    return keyboard


# ==================== ADMINLAR ====================

def get_admins_menu():
    """Adminlar menyu"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("➕ Admin qo'shish", callback_data="admin_manage:add"),
        InlineKeyboardButton("📋 Adminlar ro'yxati", callback_data="admin_manage:list"),
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:back")
    )
    return keyboard


def get_admin_list_keyboard(admins: list, current_user_id: int):
    """Adminlar ro'yxati"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for admin in admins:
        status = "👑" if admin['is_super'] else "👤"
        keyboard.add(
            InlineKeyboardButton(
                f"{status} {admin['telegram_id']}",
                callback_data=f"admin_manage:view:{admin['telegram_id']}"
            )
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin:admins")
    )
    return keyboard


def get_admin_actions(admin_id: int, is_super: bool):
    """Admin bilan amallar"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    if not is_super:
        keyboard.add(
            InlineKeyboardButton("🗑 O'chirish", callback_data=f"admin_manage:delete:{admin_id}")
        )

    keyboard.add(
        InlineKeyboardButton("🔙 Orqaga", callback_data="admin_manage:list")
    )
    return keyboard


def get_admin_delete_confirm(admin_id: int):
    """Adminni o'chirishni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"admin_manage:delete_confirm:{admin_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"admin_manage:view:{admin_id}")
    )
    return keyboard


# ==================== USER TUGMALARI ====================

def get_register_keyboard():
    """Ro'yxatdan o'tish tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("📝 Ro'yxatdan o'tish", callback_data="user:register")
    )
    return keyboard


def get_options_keyboard(options: list, field_order: int):
    """Variantlarni tanlash tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)

    for i, option in enumerate(options):
        keyboard.add(
            InlineKeyboardButton(
                option,
                callback_data=f"answer:{field_order}:{i}"
            )
        )

    return keyboard


def get_confirm_response_keyboard():
    """Javoblarni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data="response:confirm"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="response:cancel")
    )
    return keyboard