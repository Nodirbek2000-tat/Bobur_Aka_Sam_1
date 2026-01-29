from aiogram.dispatcher.filters.state import State, StatesGroup


# ==================== USER STATES ====================

class RegisterState(StatesGroup):
    """So'rovnoma to'ldirish uchun state"""
    answering = State()  # Savollarga javob berish


# ==================== ADMIN STATES ====================

class AdminState(StatesGroup):
    """Admin qo'shish/o'chirish"""
    add_admin = State()
    remove_admin = State()


class ChannelState(StatesGroup):
    """Kanal qo'shish/o'chirish"""
    add_channel = State()
    remove_channel = State()


class SurveyCreateState(StatesGroup):
    """So'rovnoma yaratish"""
    name = State()              # So'rovnoma nomi
    column_name = State()       # Ustun nomi
    question_text = State()     # Savol matni
    field_type = State()        # Maydon turi (text/choice)
    add_option = State()        # Variant qo'shish
    file_name = State()         # Fayl nomi


class SurveyEditState(StatesGroup):
    """So'rovnomani tahrirlash"""
    edit_name = State()
    edit_field = State()