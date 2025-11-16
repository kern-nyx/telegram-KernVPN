import sqlite3
from datetime import datetime, timedelta

DB_NAME = "vpn_bot.db"

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        is_active INTEGER DEFAULT 0,
        tariff_name TEXT,
        tariff_months INTEGER,
        buy_date TEXT,
        end_date TEXT,
        price INTEGER,
        vpn_key TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Таблица VPN-ключей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vpn_keys (
        key_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vpn_key TEXT UNIQUE NOT NULL,
        is_used INTEGER DEFAULT 0,
        assigned_to INTEGER,
        assigned_at TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ База данных инициализирована")

def get_user(user_id):
    """Получить данные пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_user(user_id, username):
    """Добавить нового пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO users (user_id, username) 
        VALUES (?, ?)
        """, (user_id, username))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def get_all_active_users():
    """Получить всех пользователей с активной подпиской"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, tariff_name, buy_date, end_date, price, vpn_key 
    FROM users 
    WHERE is_active = 1
    ORDER BY end_date DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users

def get_all_users():
    """Получить всех пользователей"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT user_id, username, is_active, tariff_name, end_date 
    FROM users
    ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users

def get_free_vpn_key():
    """Получить свободный VPN-ключ из пула"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT key_id, vpn_key FROM vpn_keys WHERE is_used = 0 LIMIT 1")
    key = cursor.fetchone()
    conn.close()
    return key

def mark_key_as_used(key_id, user_id):
    """Отметить ключ как использованный"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE vpn_keys 
    SET is_used = 1, assigned_to = ?, assigned_at = ? 
    WHERE key_id = ?
    """, (user_id, datetime.now().strftime("%d.%m.%Y %H:%M"), key_id))
    conn.commit()
    conn.close()

def add_vpn_key(vpn_key):
    """Добавить новый VPN-ключ в пул"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO vpn_keys (vpn_key) VALUES (?)", (vpn_key,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def activate_tariff(user_id, tariff_name, months, price, vpn_key):
    """Активировать тариф для пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    buy_date = datetime.now()
    end_date = buy_date + timedelta(days=30 * months)
    
    cursor.execute("""
    UPDATE users 
    SET is_active = 1,
        tariff_name = ?,
        tariff_months = ?,
        buy_date = ?,
        end_date = ?,
        price = ?,
        vpn_key = ?
    WHERE user_id = ?
    """, (tariff_name, months, buy_date.strftime("%d.%m.%Y"), 
          end_date.strftime("%d.%m.%Y"), price, vpn_key, user_id))
    
    conn.commit()
    conn.close()

def deactivate_user(user_id):
    """Деактивировать тариф пользователя"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
def extend_tariff(user_id, additional_months):
    """Продлить существующий тариф (прибавить дни к текущему концу)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем текущий end_date
    cursor.execute("SELECT end_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    # Парсим дату
    current_end_date = datetime.strptime(result[0], "%d.%m.%Y")
    
    # Прибавляем дни
    new_end_date = current_end_date + timedelta(days=30 * additional_months)
    
    # Обновляем
    cursor.execute("""
    UPDATE users 
    SET end_date = ?
    WHERE user_id = ?
    """, (new_end_date.strftime("%d.%m.%Y"), user_id))
    
    conn.commit()
    conn.close()
    return True

def get_expiring_users():
    """Получить пользователей, подписка которых истекает в течение 1 дня"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    
    cursor.execute("""
    SELECT user_id, username, end_date 
    FROM users 
    WHERE is_active = 1 
    AND end_date <= ?
    """, (tomorrow.strftime("%d.%m.%Y"),))
    
    users = cursor.fetchall()
    conn.close()
    return users

def get_key_statistics():
    """Получить статистику по ключам"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM vpn_keys")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM vpn_keys WHERE is_used = 1")
    used = cursor.fetchone()[0]
    
    free = total - used
    
    conn.close()
    return {"total": total, "used": used, "free": free}

def deactivate_expired_subscriptions():
    """Деактивировать все истёкшие подписки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    today = datetime.now().strftime("%d.%m.%Y")
    
    # Находим всех с истёкшей подпиской
    cursor.execute("""
    SELECT user_id 
    FROM users 
    WHERE is_active = 1 
    AND end_date <= ?
    """, (today,))
    
    expired_users = cursor.fetchall()
    
    # Деактивируем их
    for user in expired_users:
        user_id = user[0]
        cursor.execute("""
        UPDATE users 
        SET is_active = 0
        WHERE user_id = ?
        """, (user_id,))
    
    conn.commit()
    conn.close()
    
    return [user[0] for user in expired_users]

def get_user_by_id_for_notification(user_id):
    """Получить данные юзера для уведомления"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, end_date FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user
