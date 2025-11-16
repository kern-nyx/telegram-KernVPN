from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню
main = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💰 Тарифы", callback_data="tariffs")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="ℹ️ О нас", callback_data="about")],
        [InlineKeyboardButton(text="📞 Обратная связь", callback_data="feedback")],
    ]
)

# Клавиатура тарифов
tariffs_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц — 180₽", callback_data="buy_1")],
        [InlineKeyboardButton(text="3 месяца — 486₽ (-10%)", callback_data="buy_3")],
        [InlineKeyboardButton(text="6 месяцев — 810₽ (-25%)", callback_data="buy_6")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]
)

# Клавиатура для профиля БЕЗ тарифа
profile_no_tariff = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="💰 Перейти к тарифам", callback_data="tariffs")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back")]
    ]
)

# Клавиатура для профиля С активным тарифом
profile_active = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Получить ключ ещё раз", callback_data="get_key")],
        [InlineKeyboardButton(text="🔄 Продлить тариф", callback_data="tariffs")],
        [InlineKeyboardButton(text="🔙 В меню", callback_data="back")]
    ]
)

# Клавиатура "Назад"
back_menu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
    ]
)

# Клавиатура для админа (принять/отклонить платеж)
def admin_payment_keyboard(user_id, tariff_months, price):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"approve_{user_id}_{tariff_months}_{price}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"decline_{user_id}")]
        ]
    )