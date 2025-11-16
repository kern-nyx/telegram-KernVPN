from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import os
from dataBase.database import get_expiring_users, deactivate_expired_subscriptions, get_user_by_id_for_notification
from datetime import datetime

bot = Bot(token=os.getenv("TOKEN"))
scheduler = AsyncIOScheduler()

async def check_expiring_subscriptions():
    """Проверять подписки и отправлять напоминания за 1 день"""
    users = get_expiring_users()
    
    for user_id, username, end_date in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"⏰ Напоминание!\n\n"
                    f"Ваша подписка KernVPN заканчивается: {end_date}\n\n"
                    f"Пожалуйста, продлите подписку, чтобы продолжить использовать VPN.\n\n"
                    f"Нажмите 'Профиль' или выберите 'Тарифы' для продления."
                )
            )
            print(f"✅ Напоминание отправлено юзеру {user_id}")
        except Exception as e:
            print(f"❌ Ошибка при отправке напоминания юзеру {user_id}: {e}")

async def deactivate_expired_subs():
    """Деактивировать истёкшие подписки и отправить уведомления"""
    print("🔍 Проверка истёкших подписок...")
    
    expired_users = deactivate_expired_subscriptions()
    
    if not expired_users:
        print("✅ Истёкших подписок не найдено")
        return
    
    print(f"⚠️ Найдено истёкших подписок: {len(expired_users)}")
    
    for user_id in expired_users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ Ваша подписка KernVPN истекла!\n\n"
                    f"Вы больше не можете использовать VPN.\n\n"
                    f"Чтобы продолжить, пожалуйста, продлите подписку.\n\n"
                    f"Выберите новый тариф в меню 'Тарифы'."
                )
            )
            print(f"✅ Уведомление об истечении отправлено юзеру {user_id}")
        except Exception as e:
            print(f"❌ Ошибка при отправке уведомления юзеру {user_id}: {e}")

def start_scheduler():
    """Запустить планировщик задач"""
    
    # Проверка истёкших подписок каждый день в 00:01
    scheduler.add_job(
        deactivate_expired_subs,
        "cron",
        hour=0,
        minute=1,
        id="deactivate_expired"
    )
    
    # Напоминание за 1 день до истечения каждый день в 10:00
    scheduler.add_job(
        check_expiring_subscriptions,
        "cron",
        hour=10,
        minute=0,
        id="check_expiring"
    )
    
    scheduler.start()
    print("📅 Планировщик запущен")
