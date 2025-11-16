from aiogram import F, types, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
import os
import kbds.keyboards as kb
from dataBase.database import get_user, add_user, activate_tariff

from pathlib import Path
from aiogram.types import FSInputFile

user_private_router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID"))
CARD_NUMBER = os.getenv("CARD_NUMBER")

user_tariff_selection = {}

@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    add_user(user_id, username)
    
    await message.answer(
        f"👋 Добро пожаловать, {username}!\n\n"
        "Это KernVPN — твой приватный и быстрый VPN на базе AmneziaVPN.\n\n"
        "Выбери раздел:",
        reply_markup=kb.main
    )

@user_private_router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    """Обработчик вкладки Профиль"""
    await callback.answer()
    
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if not user or user[2] == 0:
        # is_active = 0 означает либо никогда не покупал, либо подписка истекла
        if user and user[3]:  # Если есть tariff_name, значит она была
            text = (
                "👤 Ваш профиль\n"
                "Статус: ❌ Подписка истекла\n\n"
                f"Ваша подписка: {user[3]}\n"
                f"Завершилась: {user[6]}\n\n"
                f"Чтобы продолжить использовать VPN — выберите новый тариф или продлите подписку."
            )
        else:
            text = (
                "👤 Ваш профиль\n"
                "Статус: 🔻 Тариф не активирован\n\n"
                "У вас пока нет подписки KernVPN.\n"
                "Чтобы начать пользоваться приватным VPN — выберите тариф 👇"
            )
        await callback.message.answer(text, reply_markup=kb.profile_no_tariff)
    else:
        # Активная подписка
        tariff_name = user[3]
        tariff_months = user[4]
        buy_date = user[5]
        end_date = user[6]
        price = user[7]
        
        text = (
            "👤 Ваш профиль\n"
            "Статус: 🟢 Активный тариф\n\n"
            f"Тариф: {tariff_months} месяца\n"
            f"Дата покупки: {buy_date}\n"
            f"Действует до: {end_date}\n"
            f"Стоимость: {price} рублей\n\n"
            "🔑 Ваш ключ получен.\n"
            "Если нужно — можете запросить повторную выдачу.\n\n"
            "🌍 Сервер KernVPN: Нидерланды\n"
            "⚡ Технология: AmneziaVPN"
        )
        await callback.message.answer(text, reply_markup=kb.profile_active)

@user_private_router.callback_query(F.data == "get_key")
async def get_key_callback(callback: CallbackQuery):
    """Повторная выдача ключа"""
    await callback.answer()
    
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    if user and user[2] == 1:
        vpn_key = user[8]
        await callback.message.answer(
            f"🔑 Ваш VPN-ключ:\n\n{vpn_key}\n\n"
            "Скопируйте его и используйте в приложении AmneziaVPN."
        )
    else:
        await callback.message.answer("❌ У вас нет активного тарифа.")

@user_private_router.callback_query(F.data == "tariffs")
async def tariffs_callback(callback: CallbackQuery):
    """Обработчик вкладки Тарифы"""
    await callback.answer()
    text = (
        "💰 Тарифы KernVPN\n\n"
        "Выберите подходящий вам тариф:\n"
        "• 1 месяц — 180 рублей\n"
        "• 3 месяца — 486 рублей (скидка 10%)\n"
        "• 6 месяцев — 810 рублей (скидка 25%)\n\n"
        "VPN-ключ на базе AmneziaVPN, сервер в Нидерландах."
    )
    await callback.message.answer(text, reply_markup=kb.tariffs_keyboard)

@user_private_router.callback_query(F.data.startswith("buy_"))
async def buy_tariff_callback(callback: CallbackQuery):
    """Обработчик покупки/продления тарифа"""
    await callback.answer()
    
    tariff_months = int(callback.data.split("_")[1])
    prices = {1: 180, 3: 486, 6: 810}
    price = prices.get(tariff_months, 180)
    
    user_tariff_selection[callback.from_user.id] = {"months": tariff_months, "price": price}
    
    text = (
        f"💳 Оплата тарифа: {tariff_months} месяца\n\n"
        f"Стоимость: {price} рублей\n\n"
        f"Переведите указанную сумму на карту:\n"
        f"{CARD_NUMBER}\n\n"
        f"После перевода отправьте скриншот платежа в этот чат.\n\n"
        f"Важно: платеж будет проверен администратором вручную."
    )
    
    await callback.message.answer(text)

@user_private_router.message(F.photo)
async def handle_payment_screenshot(message: Message):
    """Обработчик скриншота платежа"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    if user_id not in user_tariff_selection:
        await message.answer("Сначала выберите тариф в разделе 'Тарифы'.")
        return
    
    tariff_info = user_tariff_selection[user_id]
    tariff_months = tariff_info["months"]
    price = tariff_info["price"]
    
    await message.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=(
            f"Новый платеж от пользователя:\n\n"
            f"ID: {user_id}\n"
            f"Ник: @{username}\n"
            f"Тариф: {tariff_months} месяцев\n"
            f"Сумма: {price} рублей\n\n"
            f"Нажмите на кнопки ниже, чтобы принять или отклонить платеж"
        ),
        reply_markup=kb.admin_payment_keyboard(user_id, tariff_months, price)
    )
    
    await message.answer(
        "Ваш скриншот отправлен на проверку администратору.\n"
        "Ожидайте подтверждения оплаты."
    )

@user_private_router.callback_query(F.data == "about")
async def about_callback(callback: CallbackQuery):
    """О нас"""
    await callback.answer()
    text = (
        "ℹ️ О нас\n\n"
        "KernVPN — часть экосистемы Kern.\n"
        "Мы предоставляем безопасный и быстрый VPN на базе технологии AmneziaVPN.\n\n"
        "Каждый ключ уникален и защищён. Без логов, без лишнего шума — только чистая скорость и приватность."
    )
    await callback.message.answer(text, reply_markup=kb.back_menu)

@user_private_router.callback_query(F.data == "feedback")
async def feedback_callback(callback: CallbackQuery):
    """Обратная связь"""
    await callback.answer()
    text = (
        "📞 Обратная связь\n\n"
        "Если у вас возникли вопросы или проблемы — пишите:\n"
        "Электронная почта: imceodud@gmail.com\n"
        "Телеграм: @feedback_nyx"
    )
    await callback.message.answer(text, reply_markup=kb.back_menu)

@user_private_router.callback_query(F.data == "back")
async def back_callback(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()
    await callback.message.answer("Главное меню:", reply_markup=kb.main)


@user_private_router.callback_query(F.data == "instructions")
async def instructions_callback(callback: CallbackQuery):
    await callback.answer()
    
    instruction_file = Path("instructions/instruction.txt")
    
    # Текст с кликабельными ссылками
    caption_text = (
        "📖 Инструкция по использованию KernVPN\n\n"
        "<b>Ссылки для скачивания:</b>\n\n"
        "🍎 <a href='https://apps.apple.com/us/app/amneziavpn/id1600529900'>iOS - AmneziaVPN</a>\n"
        "🤖 <a href='https://play.google.com/store/apps/details?id=org.amnezia.vpn'>Android</a>\n"
        "💻 <a href='https://m-1-9-3w5hsuiikq-ez.a.run.app/downloads'>Windows</a>\n"
        "🍎 <a href='https://m-1-9-3w5hsuiikq-ez.a.run.app/downloads'>macOS</a>\n"
        "🐧 <a href='https://m-1-9-3w5hsuiikq-ez.a.run.app/downloads'>Linux</a>\n\n"
        "📥 Откройте файл ниже для полной инструкции"
    )
    
    await callback.message.answer_document(
        document=FSInputFile(str(instruction_file)),
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=kb.back_menu
    )