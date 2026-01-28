import telebot
from telebot import types
import sqlite3
from datetime import datetime, time, timedelta
import logging
import threading
import time as time_module
import requests
import json
import random
import pytz
import schedule
from typing import Optional, Dict, List, Tuple, Any
import os

# ==================== ВСТАВЬТЕ ВАШ ТОКЕН ЗДЕСЬ ====================
# ЗАМЕНИТЕ ЭТУ СТРОКУ НА ВАШ ТОКЕН ОТ @BotFather
TOKEN = "7984392310:AAHpfcsdAgzxt3NYIYld_HPGctg4YmZwUwk"  # ← ЗАМЕНИТЕ ЭТО

# Создаем бота
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# Московское время (UTC+3)
MOSCOW_TZ = pytz.timezone('Europe/Moscow')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Словарь для хранения состояний пользователей
user_states = {}
user_data = {}  # Временное хранение данных пользователей

# ==================== РУССКИЕ ЦИТАТЫ И ПРИВЫЧКИ ====================
RUSSIAN_QUOTES = [
    {"text": "Счастье не в том, чтобы делать всегда, что хочешь, а в том, чтобы всегда хотеть того, что делаешь.", "author": "Лев Толстой"},
    {"text": "Чтобы поверить в добро, надо начать делать его.", "author": "Лев Толстой"},
    {"text": "Идти вперёд — значит потерять душевный покой, остаться на месте — значит потерять себя.", "author": "Фёдор Достоевский"},
    {"text": "Надо любить жизнь больше, чем смысл жизни.", "author": "Фёдор Достоевский"},
    {"text": "Человек — это то, во что он верит.", "author": "Антон Чехов"},
    {"text": "Дела определяются их целями; то дело называется великим, у которого велика цель.", "author": "Антон Чехов"},
    {"text": "Не ошибается тот, кто ничего не делает. Не бойтесь ошибаться — бойтесь повторять ошибки.", "author": "Теодор Рузвельт"},
    {"text": "Самый лучший способ взяться за что-то — перестать говорить и начать делать.", "author": "Уолт Дисней"},
    {"text": "Ваше время ограничено, не тратьте его, живя чужой жизнью.", "author": "Стив Джобс"},
    {"text": "Если ты не готов рискнуть, ты не сможешь вырасти.", "author": "Робин Шарма"},
    {"text": "Лучший момент, чтобы посадить дерево, был 20 лет назад. Следующий лучший момент — сегодня.", "author": "Китайская пословица"},
    {"text": "Успех — это не ключ к счастью. Счастье — это ключ к успеху.", "author": "Альберт Швейцер"},
    {"text": "Не бойся расти медленно, бойся только стоять на месте.", "author": "Китайская пословица"},
    {"text": "Путь в тысячу ли начинается с первого шага.", "author": "Лао-цзы"},
    {"text": "Мечтайте о великом, начинайте с малого, действуйте сейчас.", "author": "Робин Шарма"},
    {"text": "Не ждите. Время никогда не будет подходящим.", "author": "Наполеон Хилл"},
    {"text": "Действие — это основополагающий ключ ко всякому успеху.", "author": "Пабло Пикассо"},
    {"text": "Будущее зависит от того, что вы делаете сегодня.", "author": "Махатма Ганди"},
    {"text": "Каждый день — это чистый лист. Пишите свою историю смело и красиво.", "author": "Нет автора"},
    {"text": "Самодисциплина — это когда ваши мечты сильнее ваших отговорок.", "author": "Нет автора"},
    {"text": "Не ищите идеальное время — создавайте его сами.", "author": "Нет автора"},
    {"text": "Цель — это мечта с дедлайном.", "author": "Наполеон Хилл"},
    {"text": "Ты можешь всё, если у тебя есть вера, план и упорство.", "author": "Нет автора"},
    {"text": "Сегодняшние усилия — завтрашние результаты.", "author": "Нет автора"},
    {"text": "Трудности закаляют характер и приближают к цели.", "author": "Нет автора"},
]

# Список привычек (запасной вариант, если нейросеть не работает)
HABITS_LIST = [
    "Просыпайтесь каждый день в одно и то же время, даже в выходные.",
    "Начните день со стакана теплой воды с лимоном.",
    "Выделяйте 10 минут утром для планирования дня.",
    "Ежедневно читайте хотя бы 20 минут профессиональную литературу.",
    "Выполняйте 15-минутную зарядку каждое утро.",
    "Практикуйте глубокое дыхание 5 минут в день для снижения стресса.",
    "Выпивайте 8 стаканов воды в день.",
    "Записывайте 3 вещи, за которые вы благодарны, перед сном.",
    "Ограничьте время в соцсетях 30 минутами в день.",
    "Делайте 5-минутную растяжку каждый час сидячей работы.",
    "Ежедневно учите 5 новых слов на иностранном языке.",
    "Выполняйте одно важное дело до обеда.",
    "Проводите 15 минут на свежем воздухе ежедневно.",
    "Убирайтесь на рабочем столе в конце каждого дня.",
    "Выключайте все устройства за час до сна.",
    "Составляйте список дел на завтра с вечера.",
    "Практикуйте осознанное питание - ешьте без телефона и ТВ.",
    "Делайте 10-минутную медитацию утром или вечером.",
    "Раз в неделю пробуйте что-то новое.",
    "Записывайте свои успехи и достижения в дневник.",
]

COURSES = [
    ("Python для начинающих", "https://stepik.org/course/58852"),
    ("Тайм-менеджмент", "https://stepik.org/course/59398"),
    ("Самодисциплина", "https://stepik.org/course/62178"),
    ("Основы программирования", "https://stepik.org/course/67"),
    ("Психология достижений", "https://stepik.org/course/48103"),
]

STATUS_ICONS = {
    "planned": "🕒",
    "progress": "⏳",
    "done": "✅",
    "cancelled": "❌"
}

STATUS_TEXT = {
    "planned": "Запланирована",
    "progress": "В процессе",
    "done": "Выполнено",
    "cancelled": "Отменено"
}

# ==================== БАЗА ДАННЫХ ====================
def get_db_connection():
    """Создает соединение с базой данных"""
    conn = sqlite3.connect("success_planner.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Инициализация базы данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица целей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        goal TEXT NOT NULL,
        status TEXT DEFAULT 'planned',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Таблица настроек пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        reminders_enabled BOOLEAN DEFAULT 1,
        reminder_time TEXT DEFAULT '09:00',
        last_reminder_sent DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Создаем индексы для ускорения запросов
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_user_id ON goals (user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_date ON goals (date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_goals_status ON goals (status)")
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

init_db()

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_moscow_time() -> datetime:
    """Получает текущее время по Москве"""
    return datetime.now(MOSCOW_TZ)

def get_moscow_date_str() -> str:
    """Получает текущую дату по Москве в формате YYYY-MM-DD"""
    return get_moscow_time().strftime("%Y-%m-%d")

def format_date_for_display(date_str: str) -> str:
    """Форматирует дату для отображения"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today = get_moscow_time().date()
        
        if date_obj.date() == today:
            return "Сегодня"
        elif date_obj.date() == today + timedelta(days=1):
            return "Завтра"
        elif date_obj.date() == today - timedelta(days=1):
            return "Вчера"
        else:
            return date_obj.strftime("%d.%m.%Y")
    except:
        return date_str

def get_motivational_quote() -> str:
    """Получает мотивационную цитату на русском"""
    try:
        quote_data = random.choice(RUSSIAN_QUOTES)
        quote_text = quote_data["text"]
        author = quote_data["author"]
        
        if author == "Нет автора":
            return f'"{quote_text}"'
        else:
            return f'"{quote_text}"\n\n— {author}'
    except Exception as e:
        logger.warning(f"Не удалось получить цитату: {e}")
        return '"Сегодняшние усилия — завтрашние результаты."\n\n— Планировщик Успеха'

def get_ai_habit() -> str:
    """Получает сгенерированную привычку"""
    try:
        # Используем OpenAI API (если установлен)
        try:
            import openai
            # Замените на ваш ключ OpenAI
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
            
            if openai.api_key:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Ты помощник по саморазвитию. Предложи одну полезную привычку для ежедневного выполнения. Опиши её кратко и мотивирующе."},
                        {"role": "user", "content": "Предложи одну полезную привычку"}
                    ],
                    max_tokens=100
                )
                return response.choices[0].message.content.strip()
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"Не удалось получить привычку от OpenAI: {e}")
        
        # Запасной вариант - случайная привычка из списка
        return random.choice(HABITS_LIST)
        
    except Exception as e:
        logger.error(f"Ошибка при получении привычки: {e}")
        return "Начните день с планирования 3 самых важных задач на сегодня."

def validate_date(date_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Проверяет корректность даты"""
    try:
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return True, date_obj.strftime("%Y-%m-%d"), ""
            except ValueError:
                continue
        
        return False, None, "Неверный формат даты! Используйте ДД.ММ.ГГГГ"
    except Exception as e:
        logger.error(f"Ошибка при валидации даты: {e}")
        return False, None, f"Ошибка: {str(e)}"

def validate_time(time_str: str) -> Tuple[bool, Optional[str]]:
    """Проверяет корректность времени"""
    try:
        datetime.strptime(time_str, "%H:%M")
        return True, time_str
    except ValueError:
        return False, None

def save_user_info(user_id: int, username: str = "", first_name: str = "", last_name: str = ""):
    """Сохраняет информацию о пользователе"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO user_settings 
        (user_id, username, first_name, last_name, updated_at) 
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, username, first_name, last_name))
    
    conn.commit()
    conn.close()

def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Получает статистику пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_goals,
            SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) as done_goals,
            SUM(CASE WHEN status = 'progress' THEN 1 ELSE 0 END) as progress_goals,
            SUM(CASE WHEN status = 'planned' THEN 1 ELSE 0 END) as planned_goals,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_goals
        FROM goals 
        WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    
    today = get_moscow_date_str()
    cursor.execute("""
        SELECT COUNT(*) as today_goals
        FROM goals 
        WHERE user_id = ? AND date = ? AND status IN ('planned', 'progress')
    """, (user_id, today))
    
    today_row = cursor.fetchone()
    conn.close()
    
    if row:
        total_goals = row['total_goals'] if row['total_goals'] is not None else 0
        done_goals = row['done_goals'] if row['done_goals'] is not None else 0
        progress_goals = row['progress_goals'] if row['progress_goals'] is not None else 0
        planned_goals = row['planned_goals'] if row['planned_goals'] is not None else 0
        cancelled_goals = row['cancelled_goals'] if row['cancelled_goals'] is not None else 0
    else:
        total_goals = done_goals = progress_goals = planned_goals = cancelled_goals = 0
    
    today_goals = today_row['today_goals'] if today_row and today_row['today_goals'] is not None else 0
    
    completion_rate = (done_goals / total_goals * 100) if total_goals > 0 else 0
    
    return {
        "total_goals": total_goals,
        "done_goals": done_goals,
        "progress_goals": progress_goals,
        "planned_goals": planned_goals,
        "cancelled_goals": cancelled_goals,
        "today_goals": today_goals,
        "completion_rate": completion_rate
    }

# ==================== КЛАВИАТУРЫ ====================
def main_menu():
    """Главное меню"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("🎯 Мои цели", "📅 Добавить цель")
    kb.add("📊 Прогресс", "💪 Привычка дня")
    kb.add("📚 Курсы", "💫 Мотивация")
    kb.add("⚙️ Настройки")
    return kb

def goals_menu():
    """Меню целей"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("📅 Сегодня", "🗓️ Завтра", "📋 Все цели", "✅ Выполненные")
    kb.add("🔙 Главное меню")
    return kb

def settings_menu():
    """Меню настроек"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add("⏰ Время напоминаний", "🔔 Вкл/Выкл напоминания")
    kb.add("👤 Профиль", "📊 Статистика")
    kb.add("🔄 Сбросить всё", "🔙 Главное меню")
    return kb

def time_selection_menu():
    """Меню выбора времени"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=4)
    times = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", 
             "13:00", "14:00", "15:00", "16:00", "17:00", "18:00",
             "19:00", "20:00", "21:00"]
    
    rows = [times[i:i+4] for i in range(0, len(times), 4)]
    for row in rows:
        kb.row(*row)
    
    kb.add("🔙 Назад в настройки")
    return kb

def cancel_menu():
    """Меню отмены"""
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("❌ Отмена")
    return kb

# ==================== МЕНЕДЖЕР НАПОМИНАНИЙ ====================
class ReminderManager:
    """Управление напоминаниями пользователей"""
    
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.running = False
        self.scheduler_thread = None
        self.start_scheduler()
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Получает настройки пользователя"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT reminders_enabled, reminder_time, last_reminder_sent 
            FROM user_settings 
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "enabled": bool(row['reminders_enabled']),
                "time": row['reminder_time'],
                "last_sent": row['last_reminder_sent']
            }
        else:
            self.update_user_settings(user_id, enabled=True, reminder_time="09:00")
            return {"enabled": True, "time": "09:00", "last_sent": None}
    
    def update_user_settings(self, user_id: int, enabled: bool = None, reminder_time: str = None):
        """Обновляет настройки пользователя"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        current = cursor.fetchone()
        
        if current:
            updates = []
            params = []
            
            if enabled is not None:
                updates.append("reminders_enabled = ?")
                params.append(int(enabled))
            
            if reminder_time is not None:
                updates.append("reminder_time = ?")
                params.append(reminder_time)
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(user_id)
            
            query = f"UPDATE user_settings SET {', '.join(updates)} WHERE user_id = ?"
            cursor.execute(query, params)
        else:
            cursor.execute("""
                INSERT INTO user_settings 
                (user_id, reminders_enabled, reminder_time) 
                VALUES (?, ?, ?)
            """, (user_id, int(enabled or True), reminder_time or "09:00"))
        
        conn.commit()
        conn.close()
    
    def get_today_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает цели пользователя на сегодня"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        today = get_moscow_date_str()
        cursor.execute("""
            SELECT id, goal, status 
            FROM goals 
            WHERE user_id = ? AND date = ? AND status IN ('planned', 'progress')
            ORDER BY created_at
        """, (user_id, today))
        
        goals = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return goals
    
    def send_reminder(self, user_id: int, force: bool = False) -> bool:
        """Отправляет напоминание пользователю"""
        try:
            settings = self.get_user_settings(user_id)
            
            if not force and not settings["enabled"]:
                return False
            
            today = get_moscow_date_str()
            if not force and settings["last_sent"] == today:
                return True
            
            today_goals = self.get_today_goals(user_id)
            
            message = "🔔 *Ежедневное напоминание!*\n\n"
            
            if today_goals:
                message += "🎯 *Цели на сегодня:*\n\n"
                for i, goal in enumerate(today_goals[:5], 1):
                    icon = STATUS_ICONS.get(goal['status'], '📝')
                    message += f"{i}. {icon} {goal['goal'][:50]}"
                    if len(goal['goal']) > 50:
                        message += "..."
                    message += "\n"
                
                if len(today_goals) > 5:
                    message += f"\n...и еще {len(today_goals) - 5} целей\n"
                
                message += f"\nВсего на сегодня: *{len(today_goals)}* целей\n\n"
            else:
                message += "📝 *Сегодня у вас нет запланированных целей*\n\n"
                message += "Добавьте цели через меню '📅 Добавить цель'\n\n"
            
            message += "💫 *Мотивация на сегодня:*\n"
            message += get_motivational_quote()
            
            self.bot.send_message(user_id, message)
            
            if not force:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_settings 
                    SET last_reminder_sent = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (today, user_id))
                conn.commit()
                conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания: {e}")
            return False
    
    def check_and_send_reminders(self):
        """Проверяет и отправляет напоминания"""
        try:
            current_time = get_moscow_time()
            current_hour_min = current_time.strftime("%H:%M")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, reminder_time 
                FROM user_settings 
                WHERE reminders_enabled = 1
            """)
            
            users = cursor.fetchall()
            conn.close()
            
            for user in users:
                user_id = user['user_id']
                reminder_time = user['reminder_time']
                
                if reminder_time == current_hour_min:
                    threading.Thread(
                        target=self.send_reminder,
                        args=(user_id, False),
                        daemon=True
                    ).start()
                    
        except Exception as e:
            logger.error(f"Ошибка в check_and_send_reminders: {e}")
    
    def start_scheduler(self):
        """Запускает планировщик"""
        if self.running:
            return
        
        self.running = True
        schedule.every(1).minutes.do(self.check_and_send_reminders)
        
        def scheduler_loop():
            logger.info("Планировщик напоминаний запущен")
            while self.running:
                try:
                    schedule.run_pending()
                except Exception as e:
                    logger.error(f"Ошибка в планировщике: {e}")
                time_module.sleep(30)
        
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Останавливает планировщик"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Планировщик напоминаний остановлен")

reminder_manager = ReminderManager(bot)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=["start", "help"])
def start_command(message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_info = message.from_user
    
    save_user_info(
        user_id, 
        user_info.username or "", 
        user_info.first_name or "", 
        user_info.last_name or ""
    )
    
    user_states[user_id] = None
    settings = reminder_manager.get_user_settings(user_id)
    
    welcome_text = (
        f"👋 *Привет, {user_info.first_name or 'друг'}!*\n\n"
        "Я — *Планировщик Успеха* 🚀\n\n"
        "Я помогу тебе:\n"
        "• 🎯 Ставить и достигать цели\n"
        "• 💪 Формировать полезные привычки\n"
        "• 📊 Отслеживать прогресс\n"
        "• 🔔 Получать напоминания\n"
        "• 💫 Мотивироваться каждый день\n\n"
        f"⏰ *Напоминания:* {'✅ Включены' if settings['enabled'] else '❌ Выключены'}\n"
        f"🕐 *Время:* {settings['time']} (МСК)\n\n"
        "*Используй кнопки ниже:*"
    )
    
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=main_menu()
    )

# ==================== ОБРАБОТЧИКИ МЕНЮ ====================
@bot.message_handler(func=lambda m: m.text == "🔙 Главное меню")
def back_to_main(message):
    """Возврат в главное меню"""
    user_id = message.from_user.id
    user_states[user_id] = None
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🎯 Мои цели")
def my_goals_menu(message):
    """Меню целей"""
    user_id = message.from_user.id
    user_states[user_id] = None
    bot.send_message(message.chat.id, "🎯 *Управление целями*", reply_markup=goals_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📅 Добавить цель")
def add_goal_start(message):
    """Начало добавления цели"""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_goal_date"
    bot.send_message(
        message.chat.id,
        "📅 *Шаг 1: Введите дату цели*\n\nФормат: *ДД.ММ.ГГГГ*\nПример: *" + get_moscow_time().strftime("%d.%m.%Y") + "*",
        reply_markup=cancel_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "📅 Сегодня")
def today_goals(message):
    """Показывает цели на сегодня"""
    user_id = message.from_user.id
    show_today_goals(user_id)

@bot.message_handler(func=lambda m: m.text == "🗓️ Завтра")
def tomorrow_goals(message):
    """Показывает цели на завтра"""
    user_id = message.from_user.id
    tomorrow = (get_moscow_time() + timedelta(days=1)).strftime("%Y-%m-%d")
    show_goals_by_date(user_id, tomorrow, "завтра")

@bot.message_handler(func=lambda m: m.text == "📋 Все цели")
def all_goals(message):
    """Показывает все цели с меню"""
    user_id = message.from_user.id
    show_all_goals_menu(user_id)

@bot.message_handler(func=lambda m: m.text == "✅ Выполненные")
def completed_goals(message):
    """Показывает выполненные цели"""
    user_id = message.from_user.id
    show_completed_goals_with_buttons(user_id)

@bot.message_handler(func=lambda m: m.text == "📊 Прогресс")
def progress_menu(message):
    """Показывает прогресс"""
    user_id = message.from_user.id
    show_user_stats(user_id)

@bot.message_handler(func=lambda m: m.text == "💪 Привычка дня")
def habits_menu(message):
    """Показывает сгенерированную привычку"""
    user_id = message.from_user.id
    user_states[user_id] = None
    
    habit = get_ai_habit()
    habits_text = (
        "💪 *Привычка дня!*\n\n"
        f"{habit}\n\n"
        "*Совет:* Попробуйте выполнять эту привычку каждый день в течение 21 дня. "
        "Именно столько времени нужно для формирования новой привычки!"
    )
    
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💪 Ещё привычку", callback_data="another_habit"))
    
    bot.send_message(user_id, habits_text, reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📚 Курсы")
def courses_menu(message):
    """Показывает полезные курсы"""
    user_id = message.from_user.id
    user_states[user_id] = None
    
    courses_text = "📚 *Полезные курсы для развития:*\n\n"
    for i, (name, url) in enumerate(COURSES, 1):
        courses_text += f"{i}. *{name}*\n{url}\n\n"
    
    courses_text += "💡 *Совет:* Выберите 1-2 курса и пройдите их до конца!"
    bot.send_message(message.chat.id, courses_text)

@bot.message_handler(func=lambda m: m.text == "💫 Мотивация")
def motivation_menu(message):
    """Отправляет мотивацию"""
    user_id = message.from_user.id
    user_states[user_id] = None
    
    quote = get_motivational_quote()
    stats = get_user_stats(user_id)
    
    motivation_text = (
        "💫 *Мотивация на сегодня:*\n\n"
        f"{quote}\n\n"
        f"🎯 *Ваш прогресс:* {stats['done_goals']}/{stats['total_goals']} целей выполнено\n"
        f"📈 *Процент выполнения:* {stats['completion_rate']:.1f}%"
    )
    
    bot.send_message(message.chat.id, motivation_text)

@bot.message_handler(func=lambda m: m.text == "⚙️ Настройки")
def settings_main_menu(message):
    """Главное меню настроек"""
    user_id = message.from_user.id
    user_states[user_id] = None
    bot.send_message(message.chat.id, "⚙️ *Настройки бота*", reply_markup=settings_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "⏰ Время напоминаний")
def set_reminder_time_menu(message):
    """Установка времени напоминаний"""
    user_id = message.from_user.id
    user_states[user_id] = "waiting_reminder_time"
    
    settings = reminder_manager.get_user_settings(user_id)
    bot.send_message(
        message.chat.id,
        f"⏰ *Текущее время напоминаний:* {settings['time']}\n\nВыберите новое время:",
        reply_markup=time_selection_menu(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "🔔 Вкл/Выкл напоминания")
def toggle_reminders_menu(message):
    """Включение/выключение напоминаний"""
    user_id = message.from_user.id
    
    settings = reminder_manager.get_user_settings(user_id)
    new_state = not settings["enabled"]
    
    reminder_manager.update_user_settings(user_id, enabled=new_state)
    
    status_text = "✅ включены" if new_state else "❌ выключены"
    bot.send_message(message.chat.id, f"Напоминания теперь {status_text}!", reply_markup=settings_menu())

@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile_menu(message):
    """Показывает профиль пользователя"""
    user_id = message.from_user.id
    user_info = message.from_user
    stats = get_user_stats(user_id)
    
    profile_text = (
        f"👤 *Профиль пользователя*\n\n"
        f"• Имя: {user_info.first_name or 'Не указано'}\n"
        f"• Фамилия: {user_info.last_name or 'Не указана'}\n"
        f"• Username: @{user_info.username or 'Не указан'}\n\n"
        f"📊 *Статистика:*\n"
        f"• Всего целей: {stats['total_goals']}\n"
        f"• Выполнено: {stats['done_goals']}\n"
        f"• В процессе: {stats['progress_goals']}\n"
        f"• Запланировано: {stats['planned_goals']}\n"
        f"• На сегодня: {stats['today_goals']}\n"
        f"• Процент выполнения: {stats['completion_rate']:.1f}%"
    )
    
    bot.send_message(message.chat.id, profile_text)

@bot.message_handler(func=lambda m: m.text == "📊 Статистика")
def statistics_menu(message):
    """Показывает статистику"""
    user_id = message.from_user.id
    show_user_stats(user_id)

@bot.message_handler(func=lambda m: m.text == "🔄 Сбросить всё")
def reset_data_menu(message):
    """Меню сброса данных"""
    user_id = message.from_user.id
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🗑️ Все цели", callback_data="reset:goals"),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data="reset:settings"),
        types.InlineKeyboardButton("📊 Статистику", callback_data="reset:stats"),
        types.InlineKeyboardButton("❌ Отмена", callback_data="reset:cancel")
    )
    
    bot.send_message(
        message.chat.id,
        "⚠️ *Внимание!*\n\nВыберите, что вы хотите сбросить:\n\n"
        "• *Все цели* - удалит все ваши цели\n"
        "• *Статистику* - обнулит статистику\n"
        "• *Настройки* - сбросит настройки\n\n"
        "*Это действие нельзя отменить!*",
        reply_markup=kb,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "❌ Отмена")
def cancel_action(message):
    """Отмена текущего действия"""
    user_id = message.from_user.id
    user_states[user_id] = None
    bot.send_message(message.chat.id, "❌ Действие отменено.", reply_markup=main_menu())

# ==================== ФУНКЦИИ ДЛЯ РАБОТЫ С ЦЕЛЯМИ ====================
def show_today_goals(user_id: int):
    """Показывает цели на сегодня с кнопками"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    today = get_moscow_date_str()
    cursor.execute("""
        SELECT id, goal, status 
        FROM goals 
        WHERE user_id = ? AND date = ?
        ORDER BY 
            CASE status 
                WHEN 'progress' THEN 1
                WHEN 'planned' THEN 2
                WHEN 'done' THEN 3
                ELSE 4
            END,
            created_at
    """, (user_id, today))
    
    goals = cursor.fetchall()
    conn.close()
    
    if not goals:
        bot.send_message(
            user_id,
            "📭 *На сегодня целей нет*\n\nДобавьте цели через меню '📅 Добавить цель'",
            reply_markup=goals_menu()
        )
        return
    
    message = f"🎯 *Цели на сегодня ({format_date_for_display(today)})*:\n\n"
    
    for i, goal in enumerate(goals, 1):
        icon = STATUS_ICONS.get(goal['status'], '📝')
        status_text = STATUS_TEXT.get(goal['status'], goal['status'])
        message += f"{i}. {icon} *{status_text}*\n"
        message += f"   {goal['goal'][:80]}"
        if len(goal['goal']) > 80:
            message += "..."
        message += "\n\n"
    
    message += f"Всего: *{len(goals)}* целей"
    
    # Уменьшенные кнопки
    kb = types.InlineKeyboardMarkup(row_width=1)
    for goal in goals[:10]:  # Ограничиваем 10 целями
        icon = STATUS_ICONS.get(goal['status'], '📝')
        goal_text = f"{icon} {goal['goal'][:25]}"
        if len(goal['goal']) > 25:
            goal_text += "..."
        kb.add(types.InlineKeyboardButton(goal_text, callback_data=f"goal:{goal['id']}"))
    
    bot.send_message(user_id, message, reply_markup=kb, parse_mode="Markdown")

def show_goals_by_date(user_id: int, date_str: str, date_display: str):
    """Показывает цели на указанную дату с кнопками"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, goal, status 
        FROM goals 
        WHERE user_id = ? AND date = ?
        ORDER BY status, created_at
    """, (user_id, date_str))
    
    goals = cursor.fetchall()
    conn.close()
    
    if not goals:
        bot.send_message(
            user_id,
            f"📭 *На {date_display} целей нет*",
            reply_markup=goals_menu()
        )
        return
    
    message = f"🎯 *Цели на {date_display}:*\n\n"
    
    for i, goal in enumerate(goals, 1):
        icon = STATUS_ICONS.get(goal['status'], '📝')
        message += f"{i}. {icon} {goal['goal'][:80]}"
        if len(goal['goal']) > 80:
            message += "..."
        message += "\n"
    
    message += f"\nВсего: *{len(goals)}* целей"
    
    # Уменьшенные кнопки
    kb = types.InlineKeyboardMarkup(row_width=1)
    for goal in goals[:10]:
        icon = STATUS_ICONS.get(goal['status'], '📝')
        goal_text = f"{icon} {goal['goal'][:25]}"
        if len(goal['goal']) > 25:
            goal_text += "..."
        kb.add(types.InlineKeyboardButton(goal_text, callback_data=f"goal:{goal['id']}"))
    
    bot.send_message(user_id, message, reply_markup=kb, parse_mode="Markdown")

def show_all_goals_menu(user_id: int):
    """Показывает все цели с меню как в разделе Мои цели"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, goal, status, id 
        FROM goals 
        WHERE user_id = ? 
        ORDER BY date DESC, 
            CASE status 
                WHEN 'progress' THEN 1
                WHEN 'planned' THEN 2
                WHEN 'done' THEN 3
                ELSE 4
            END
        LIMIT 30
    """, (user_id,))
    
    goals = cursor.fetchall()
    conn.close()
    
    if not goals:
        bot.send_message(
            user_id,
            "📭 *У вас пока нет целей*",
            reply_markup=goals_menu()
        )
        return
    
    # Группируем по датам
    goals_by_date = {}
    for goal in goals:
        date_str = goal['date']
        if date_str not in goals_by_date:
            goals_by_date[date_str] = []
        goals_by_date[date_str].append(goal)
    
    # Формируем сообщение
    message = "📋 *Все ваши цели:*\n\n"
    
    for date_str, date_goals in sorted(goals_by_date.items(), reverse=True):
        date_display = format_date_for_display(date_str)
        message += f"📅 *{date_display}:*\n"
        
        for goal in date_goals:
            icon = STATUS_ICONS.get(goal['status'], '📝')
            message += f"  {icon} {goal['goal'][:60]}"
            if len(goal['goal']) > 60:
                message += "..."
            message += "\n"
        
        message += "\n"
    
    message += f"Всего: *{len(goals)}* целей (показано последние 30)"
    
    # Создаем инлайн-клавиатуру для перехода к датам
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопки для просмотра по датам
    unique_dates = sorted(set(goal['date'] for goal in goals))
    today = get_moscow_date_str()
    
    if today in unique_dates:
        kb.add(types.InlineKeyboardButton("📅 Сегодня", callback_data="view_today_from_all"))
    
    tomorrow = (get_moscow_time() + timedelta(days=1)).strftime("%Y-%m-%d")
    if tomorrow in unique_dates:
        kb.add(types.InlineKeyboardButton("🗓️ Завтра", callback_data="view_tomorrow_from_all"))
    
    # Добавляем кнопки для отдельных дат
    for date_str in unique_dates[:6]:  # Ограничиваем 6 датами
        if date_str != today and date_str != tomorrow:
            date_display = format_date_for_display(date_str)
            kb.add(types.InlineKeyboardButton(f"📅 {date_display}", callback_data=f"view_date:{date_str}"))
    
    bot.send_message(user_id, message, reply_markup=kb, parse_mode="Markdown")

def show_completed_goals_with_buttons(user_id: int):
    """Показывает выполненные цели с возможностью изменения статуса"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, date, goal, updated_at 
        FROM goals 
        WHERE user_id = ? AND status = 'done'
        ORDER BY updated_at DESC
        LIMIT 20
    """, (user_id,))
    
    goals = cursor.fetchall()
    conn.close()
    
    if not goals:
        bot.send_message(
            user_id,
            "📭 *У вас пока нет выполненных целей*",
            reply_markup=goals_menu()
        )
        return
    
    message = "✅ *Выполненные цели:*\n\n"
    
    for i, goal in enumerate(goals, 1):
        date_display = format_date_for_display(goal['date'])
        try:
            completed_date = datetime.strptime(goal['updated_at'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m")
        except:
            completed_date = goal['updated_at']
        
        message += f"{i}. *{date_display}:* {goal['goal'][:70]}"
        if len(goal['goal']) > 70:
            message += "..."
        message += f"\n   🎉 Выполнено: {completed_date}\n\n"
    
    message += f"Всего выполнено: *{len(goals)}* целей"
    
    # Кнопки для выполненных целей
    kb = types.InlineKeyboardMarkup(row_width=1)
    for goal in goals[:10]:  # Ограничиваем 10 целями
        goal_text = f"✅ {goal['goal'][:25]}"
        if len(goal['goal']) > 25:
            goal_text += "..."
        kb.add(types.InlineKeyboardButton(goal_text, callback_data=f"goal:{goal['id']}"))
    
    bot.send_message(user_id, message, reply_markup=kb, parse_mode="Markdown")

def show_user_stats(user_id: int):
    """Показывает статистику пользователя"""
    stats = get_user_stats(user_id)
    
    def create_progress_bar(percentage, width=20):
        filled = int(percentage * width / 100)
        empty = width - filled
        return "▓" * filled + "░" * empty
    
    progress_bar = create_progress_bar(stats['completion_rate'])
    
    stats_text = (
        "📊 *Ваша статистика:*\n\n"
        f"🎯 *Цели всего:* {stats['total_goals']}\n"
        f"✅ Выполнено: {stats['done_goals']}\n"
        f"⏳ В процессе: {stats['progress_goals']}\n"
        f"🕒 Запланировано: {stats['planned_goals']}\n"
        f"❌ Отменено: {stats['cancelled_goals']}\n"
        f"📅 На сегодня: {stats['today_goals']}\n\n"
        f"📈 *Процент выполнения:* {stats['completion_rate']:.1f}%\n"
        f"{progress_bar}\n\n"
        "💪 *Продолжайте двигаться к успеху!*"
    )
    
    bot.send_message(user_id, stats_text, reply_markup=main_menu())

# ==================== ОБРАБОТКА СООБЩЕНИЙ ====================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    """Обработчик всех текстовых сообщений"""
    user_id = message.from_user.id
    text = message.text.strip()
    state = user_states.get(user_id)
    
    if state == "waiting_goal_date":
        try:
            if text.lower() == "сегодня":
                date_str = get_moscow_date_str()
                date_display = "сегодня"
                formatted_date = date_str
            elif text.lower() == "завтра":
                tomorrow = get_moscow_time() + timedelta(days=1)
                date_str = tomorrow.strftime("%Y-%m-%d")
                date_display = "завтра"
                formatted_date = date_str
            else:
                is_valid, formatted_date, error_msg = validate_date(text)
                
                if not is_valid:
                    bot.send_message(user_id, f"❌ {error_msg}", reply_markup=cancel_menu())
                    return
                
                date_obj = datetime.strptime(formatted_date, "%Y-%m-%d")
                date_display = date_obj.strftime("%d.%m.%Y")
            
            user_data[user_id] = {"date": formatted_date, "date_display": date_display}
            user_states[user_id] = "waiting_goal_text"
            
            bot.send_message(
                user_id,
                f"📅 Дата сохранена: *{date_display}*\n\n📝 *Шаг 2: Опишите вашу цель*",
                reply_markup=cancel_menu(),
                parse_mode="Markdown"
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обработке даты: {e}")
            bot.send_message(user_id, "❌ Ошибка при обработке даты", reply_markup=cancel_menu())
    
    elif state == "waiting_goal_text":
        try:
            if len(text) < 3:
                bot.send_message(user_id, "❌ Цель слишком короткая!", reply_markup=cancel_menu())
                return
            
            if user_id not in user_data:
                bot.send_message(user_id, "❌ Ошибка: данные не найдены", reply_markup=main_menu())
                user_states[user_id] = None
                return
            
            goal_data = user_data[user_id]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO goals (user_id, date, goal, status) VALUES (?, ?, ?, ?)",
                (user_id, goal_data["date"], text, "planned")
            )
            goal_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            user_states[user_id] = None
            if user_id in user_data:
                del user_data[user_id]
            
            bot.send_message(
                user_id,
                f"✅ *Цель успешно добавлена!*\n\n📅 *Дата:* {goal_data['date_display']}\n🎯 *Цель:* {text}",
                reply_markup=main_menu()
            )
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении цели: {e}")
            bot.send_message(user_id, "❌ Ошибка при сохранении цели", reply_markup=main_menu())
            user_states[user_id] = None
            if user_id in user_data:
                del user_data[user_id]
    
    elif state == "waiting_reminder_time":
        is_valid, time_str = validate_time(text)
        
        if not is_valid:
            bot.send_message(
                user_id,
                "❌ Неверный формат времени!\nИспользуйте ЧЧ:ММ",
                reply_markup=time_selection_menu()
            )
            return
        
        reminder_manager.update_user_settings(user_id, reminder_time=time_str)
        user_states[user_id] = None
        
        bot.send_message(
            user_id,
            f"✅ Время напоминаний установлено на *{time_str}*",
            reply_markup=settings_menu(),
            parse_mode="Markdown"
        )
    
    else:
        bot.send_message(user_id, "Выберите действие из меню:", reply_markup=main_menu())

# ==================== ОБРАБОТКА CALLBACK-ЗАПРОСОВ ====================
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    """Обработчик callback-запросов"""
    user_id = call.from_user.id
    data = call.data
    
    try:
        if data.startswith("goal:"):
            goal_id = data.split(":")[1]
            show_goal_details(user_id, goal_id, call.message.message_id)
        
        elif data.startswith("status:"):
            _, status, goal_id = data.split(":")
            update_goal_status(user_id, goal_id, status, call.message.message_id)
        
        elif data.startswith("reset:"):
            action = data.split(":")[1]
            handle_reset_action(user_id, action, call.message.message_id)
        
        elif data == "another_habit":
            habit = get_ai_habit()
            habits_text = f"💪 *Ещё одна привычка:*\n\n{habit}"
            
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("💪 Ещё привычку", callback_data="another_habit"))
            
            bot.edit_message_text(
                habits_text,
                user_id,
                call.message.message_id,
                reply_markup=kb,
                parse_mode="Markdown"
            )
        
        elif data == "view_today_from_all":
            show_today_goals(user_id)
        
        elif data == "view_tomorrow_from_all":
            tomorrow = (get_moscow_time() + timedelta(days=1)).strftime("%Y-%m-%d")
            show_goals_by_date(user_id, tomorrow, "завтра")
        
        elif data.startswith("view_date:"):
            date_str = data.split(":")[1]
            date_display = format_date_for_display(date_str)
            show_goals_by_date(user_id, date_str, date_display)
        
        elif data == "back_to_goals":
            bot.edit_message_text(
                "Возврат к списку целей...",
                user_id,
                call.message.message_id
            )
            bot.send_message(user_id, "🎯 Управление целями", reply_markup=goals_menu())
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        logger.error(f"Ошибка в обработке callback: {e}")
        bot.answer_callback_query(call.id, "❌ Произошла ошибка")

def show_goal_details(user_id: int, goal_id: int, message_id: int):
    """Показывает детали цели и кнопки управления"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, goal, status, created_at 
        FROM goals 
        WHERE id = ? AND user_id = ?
    """, (goal_id, user_id))
    
    goal = cursor.fetchone()
    conn.close()
    
    if not goal:
        bot.edit_message_text("❌ Цель не найдена", user_id, message_id)
        return
    
    date_display = format_date_for_display(goal['date'])
    try:
        created_date = datetime.strptime(goal['created_at'], "%Y-%m-%d %H:%M:%S").strftime("%d.%m.%Y %H:%M")
    except:
        created_date = goal['created_at']
    
    icon = STATUS_ICONS.get(goal['status'], '📝')
    status_text = STATUS_TEXT.get(goal['status'], goal['status'])
    
    message = (
        f"{icon} *Детали цели*\n\n"
        f"📅 *Дата:* {date_display}\n"
        f"📊 *Статус:* {status_text}\n"
        f"🕐 *Создана:* {created_date}\n\n"
        f"🎯 *Цель:*\n{goal['goal']}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=2)
    
    # В зависимости от текущего статуса показываем соответствующие кнопки
    if goal['status'] != 'done':
        kb.add(types.InlineKeyboardButton("✅ Выполнено", callback_data=f"status:done:{goal_id}"))
    
    if goal['status'] != 'progress':
        kb.add(types.InlineKeyboardButton("⏳ В процессе", callback_data=f"status:progress:{goal_id}"))
    
    if goal['status'] != 'planned':
        kb.add(types.InlineKeyboardButton("🕒 Запланировать", callback_data=f"status:planned:{goal_id}"))
    
    if goal['status'] != 'cancelled':
        kb.add(types.InlineKeyboardButton("❌ Отменить", callback_data=f"status:cancelled:{goal_id}"))
    
    bot.edit_message_text(
        message,
        user_id,
        message_id,
        reply_markup=kb,
        parse_mode="Markdown"
    )

def update_goal_status(user_id: int, goal_id: int, status: str, message_id: int):
    """Обновляет статус цели"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE goals 
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (status, goal_id, user_id))
    
    conn.commit()
    conn.close()
    
    status_text = STATUS_TEXT.get(status, status)
    icon = STATUS_ICONS.get(status, '📝')
    
    bot.edit_message_text(
        f"{icon} Статус цели обновлен на: *{status_text}*",
        user_id,
        message_id,
        parse_mode="Markdown"
    )

def handle_reset_action(user_id: int, action: str, message_id: int):
    """Обрабатывает сброс данных"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if action == "goals":
        cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        message = "✅ Все цели удалены!"
    
    elif action == "stats":
        # Статистика обновляется автоматически
        message = "📊 Статистика обновляется на основе целей"
    
    elif action == "settings":
        cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
        message = "✅ Настройки сброшены!"
    
    elif action == "cancel":
        bot.delete_message(user_id, message_id)
        return
    
    conn.commit()
    conn.close()
    
    bot.edit_message_text(
        message,
        user_id,
        message_id,
        parse_mode="Markdown"
    )

# ==================== ЗАПУСК БОТА ====================
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 БОТ 'ПЛАНИРОВЩИК УСПЕХА' ЗАПУСКАЕТСЯ...")
    print("=" * 60)
    
    if TOKEN == "ВАШ_ТОКЕН_ЗДЕСЬ":
        print("❌ ОШИБКА: Токен бота не установлен!")
        print("=" * 60)
        print("Замените 'ВАШ_ТОКЕН_ЗДЕСЬ' на ваш токен от @BotFather")
        print("=" * 60)
        exit(1)
    
    try:
        bot_info = bot.get_me()
        print(f"✅ Бот авторизован: @{bot_info.username}")
    except Exception as e:
        print(f"❌ Ошибка авторизации: {e}")
        print("Проверьте правильность токена!")
        exit(1)
    
    current_time = get_moscow_time().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ Текущее время (МСК): {current_time}")
    print(f"📊 База данных: success_planner.db")
    print("✅ Система напоминаний запущена")
    print("=" * 60)
    
    try:
        print("\n🤖 Бот запущен и готов к работе!")
        print("⚠️  Для остановки нажмите Ctrl+C\n")
        bot.polling(none_stop=True, interval=0, timeout=60)
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        reminder_manager.stop_scheduler()
        print("✅ Бот остановлен корректно")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        reminder_manager.stop_scheduler()
