from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
import os
from dataBase.database import get_all_active_users, get_all_users, activate_tariff, get_free_vpn_key, mark_key_as_used, add_vpn_key, get_key_statistics, extend_tariff, get_user

import kbds.keyboards as kb

admin_private_router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID"))

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id == ADMIN_ID

@admin_private_router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ-панель"""
    if not is_admin(message.from_user.id):
        await message.answer("Нет доступа к админ-панели.")
        return
    
    text = (
        "Админ-панель KernVPN\n\n"
        "Доступные команды:\n"
        "/users — список всех пользователей\n"
        "/active — список активных подписок\n"
        "/addkey ключ — добавить VPN-ключ в пул"
    )
    await message.answer(text)

@admin_private_router.message(Command("users"))
async def list_all_users(message: Message):
    """Список всех пользователей"""
    if not is_admin(message.from_user.id):
        return
    
    users = get_all_users()
    
    if not users:
        await message.answer("Пользователей пока нет.")
        return
    
    text = "Все пользователи:\n\n"
    for user in users:
        user_id, username, is_active, tariff_name, end_date = user
        status = "Активен" if is_active else "Не активен"
        tariff_info = f"Тариф: {tariff_name} (до {end_date})" if tariff_name else "Без тарифа"
        text += f"ID: {user_id}\n@{username or 'Без ника'}\nСтатус: {status}\n{tariff_info}\n\n"
    
    await message.answer(text)

@admin_private_router.message(Command("active"))
async def list_active_users(message: Message):
    """Список пользователей с активными подписками"""
    if not is_admin(message.from_user.id):
        return
    
    users = get_all_active_users()
    
    if not users:
        await message.answer("Активных подписок пока нет.")
        return
    
    text = "Активные подписки:\n\n"
    for user in users:
        user_id, username, tariff_name, buy_date, end_date, price, vpn_key = user
        text += (
            f"ID: {user_id}\n"
            f"@{username or 'Без ника'}\n"
            f"Тариф: {tariff_name}\n"
            f"Куплен: {buy_date}\n"
            f"До: {end_date}\n"
            f"Цена: {price} рублей\n"
            f"Ключ: {vpn_key}\n\n"
        )
    
    await message.answer(text)

@admin_private_router.message(Command("addkey"))
async def add_key_command(message: Message):
    """Добавить VPN-ключ в пул"""
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Использование: /addkey <vpn_key>")
        return
    
    vpn_key = parts[1].strip()
    
    if add_vpn_key(vpn_key):
        await message.answer(f"Ключ добавлен в пул: {vpn_key}")
    else:
        await message.answer("Ключ уже существует в базе.")

@admin_private_router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    """Принять платеж"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    
    await callback.answer()
    
    parts = callback.data.split("_")
    user_id = int(parts[1])
    tariff_months = int(parts[2])
    price = int(parts[3])
    
    user = get_user(user_id)
    
    if user and user[2] == 1:
        # У пользователя уже есть активная подписка — продляем
        extend_tariff(user_id, tariff_months)
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"Ваша подписка продлена!\n\n"
                f"Добавлено: {tariff_months} месяцев\n"
                f"Стоимость: {price} рублей\n\n"
                f"Спасибо за покупку!"
            )
        )
        await callback.message.answer(f"Платеж от {user_id} принят. Подписка продлена на {tariff_months} месяцев.")
    else:
        # Первая покупка
        key_data = get_free_vpn_key()
        
        if not key_data:
            await callback.message.answer("Нет свободных VPN-ключей! Добавьте ключи через /addkey")
            return
        
        key_id, vpn_key = key_data
        
        tariff_name = f"{tariff_months} месяцев"
        activate_tariff(user_id, tariff_name, tariff_months, price, vpn_key)
        mark_key_as_used(key_id, user_id)
        
        await callback.bot.send_message(
            chat_id=user_id,
            text=(
                f"Ваш платеж принят!\n\n"
                f"Тариф: {tariff_name}\n"
                f"Стоимость: {price} рублей\n\n"
                f"Ваш VPN-ключ:\n{vpn_key}\n\n"
                f"Используйте его в приложении AmneziaVPN.\n\n"
                f"Спасибо за покупку!"
            )
        )
        
        await callback.message.answer(f"Платеж от {user_id} принят. Выдан ключ: {vpn_key}")
@admin_private_router.callback_query(F.data.startswith("decline_"))
async def decline_payment(callback: CallbackQuery):
    """Отклонить платеж"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Недостаточно прав", show_alert=True)
        return
    
    await callback.answer()
    
    user_id = int(callback.data.split("_")[1])
    
    await callback.bot.send_message(
        chat_id=user_id,
        text=(
            "Ваш платеж отклонен.\n\n"
            "Возможные причины:\n"
            "• Неверная сумма перевода\n"
            "• Нечитаемый скриншот\n"
            "• Другие проблемы\n\n"
            "Свяжитесь с поддержкой через 'Обратная связь'."
        )
    )
    
    await callback.message.answer(f"Платеж от {user_id} отклонен.")

@admin_private_router.message(Command("keystat"))
async def key_statistics(message: Message):
    """Статистика по VPN-ключам"""
    if not is_admin(message.from_user.id):
        return
    
    stats = get_key_statistics()
    
    text = (
        "Статистика VPN-ключей:\n\n"
        f"Всего ключей: {stats['total']}\n"
        f"Используется: {stats['used']}\n"
        f"Свободно: {stats['free']}"
    )
    
    if stats['free'] < 5:
        text += "\n\n⚠️ Мало свободных ключей! Добавьте новые через /addkey"
    
    await message.answer(text)
