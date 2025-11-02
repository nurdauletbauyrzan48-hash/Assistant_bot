from translations import translations
import os
import json
import telebot
from datetime import datetime
import traceback
from logger import setup_logger
from file_processor import FileProcessor
import time
from telebot import types


# Логгерді орнату
logger = setup_logger()

# Telegram бот токені және әкімші ID-лері
API_TOKEN = '7921711703:AAEGkF3wKFlY8e39APao28js7CDvK0jeYL8'
ADMIN_IDS = [5032693846, 5266898576]  # Changed to integers

bot = telebot.TeleBot(API_TOKEN)
file_processor = FileProcessor()

# Қолданушылар файлын басқару
USERS_FILE = 'allowed_users.json'

#Қолданушылар тілін и басқада данныйларын басқару
USERS_LANGUAGE = "users_info.json"

def load_allowed_users():
    try:
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
            logger.info(f"Рұқсат етілген қолданушылар жүктелді: {users}")
            return set(map(int, users))  # Convert to integers
    except FileNotFoundError:
        logger.warning("Рұқсат етілген қолданушылар файлы табылмады. Жаңа файл құрылады.")
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
        return set()
    except Exception as e:
        logger.error(f"Қолданушыларды жүктеу кезінде қате: {str(e)}")
        return set()

def save_allowed_users(users):
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(list(users), f)
            logger.info("Рұқсат етілген қолданушылар сақталды")
    except Exception as e:
        logger.error(f"Қолданушыларды сақтау кезінде қате: {str(e)}")

allowed_users = load_allowed_users()

def send_log_to_admin(message, action):
    try:
        user_id = message.chat.id
        username = message.from_user.username if message.from_user.username else "Белгісіз"
        full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_text = (
            f"📝 **Жаңа хабарлама**\n"
            f"📌 **Айди:** `{user_id}`\n"
            f"👤 **Аты:** {full_name} (@{username})\n"
            f"⏳ **Уақыты:** {timestamp}\n"
            f"🔹 **Хабарлама:** {action}"
        )

        for admin_id in ADMIN_IDS:
            try:
                bot.send_message(admin_id, log_text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Әкімшіге хабарлама жіберу кезінде қате (ID: {admin_id}): {str(e)}")
    except Exception as e:
        logger.error(f"Лог жіберу кезінде қате: {str(e)}")





# Файлдан қолданушыларды жүктеу
def load_users():
    try:
        with open(USERS_LANGUAGE, "r", encoding="utf-8") as file:
            data = json.load(file)
            if isinstance(data, list):  # Егер тізім болса, оны сөздікке ауыстыру
                return {str(user_id): {"language": "Қазақша"} for user_id in data}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Файлға қолданушыларды сақтау
def save_users(users):
    with open(USERS_LANGUAGE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)

users = load_users()


@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    language = get_user_language(user_id)
    if user_id not in users:
        # Егер пайдаланушы алғаш рет кірсе, оны сақтаймыз
        users[user_id] = {"language": "None", "last_name": message.from_user.last_name, "first_name": message.from_user.first_name, "username": f"@{message.from_user.username}" if message.from_user.username else None}
        save_users(users)

        # Бірінші рет орындалатын команда
        #bot.send_message(user_id, "Сіз бірінші рет бастау батырмасын бастыңыз! Алдымен мәзірді көрсетемін.")
        #change_language(message)  # /language командасын орындау
        if user_id in allowed_users:
        	None
        else:
        	send_log_to_admin(message, "⏳ Рұқсат сұрады")
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")
        btn2 = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
        btn3 = types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, "🌍 Тілді таңдаңыз | Выберите язык | Choose a language:", reply_markup=markup)
    else:
        # Кейінгі рет басқанда стандартты /start орындалады
        #bot.send_message(user_id, "Қош келдіңіз! Бұл стандартты старт командасы.")
        try:
            user_id = message.chat.id
            if user_id in allowed_users:
                bot.send_message(user_id, translations["start_allow"][language], parse_mode='html')
            else:
                send_log_to_admin(message, "⏳ Рұқсат сұрады")
                bot.send_message(user_id, translations["start_deny"][language], parse_mode='html')
                logger.info(f"Жаңа қолданушы рұқсат сұрады: {user_id}")

        except Exception as e:
            logger.error(f"Start командасында қате: {str(e)}")
            bot.forward_message(ADMIN_IDS, message.chat.id, message.message_id)



def edit_after_selection(func):
    """Бұл декоратор тіл таңдалған соң ғана хабарламаны өзгертеді"""
    def wrapper(call):
        func(call)  # Бастапқы функцияны орындау
        try:
            user_id = call.message.chat.id
            language = get_user_language(str(user_id))

            if user_id in allowed_users:
                bot.edit_message_text(translations["start_allow"][language], call.message.chat.id, call.message.message_id, parse_mode='html')
            else:
                bot.edit_message_text(translations["start_deny"][language], call.message.chat.id, call.message.message_id, parse_mode='html')
                logger.info(f"Жаңа қолданушы рұқсат сұрады: {user_id}")
        except Exception as e:
            logger.error(f"Тілді өзгерткеннен кейін қате: {str(e)}")
    return wrapper

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
@edit_after_selection
def setset_language(call):
    try:
        user_id = str(call.message.chat.id)
        lang_map = {
            "lang_kz": "Қазақша",
            "lang_ru": "Русский",
            "lang_en": "English",
        }
        language = lang_map.get(call.data, "Қазақша")

        # Егер user_id users ішінде болмаса, оны қосу
        if user_id not in users:
            users[user_id] = {"language": language}
        else:
            users[user_id]["language"] = language  # Тілді өзгерту

        save_users(users)  # Өзгерістерді сақтау

        bot.edit_message_text(translations["language_l"][language], call.message.chat.id, call.message.message_id)
        logger.info(f"Қолданушы {user_id} тілін {language} етіп өзгертті")
    except Exception as e:
        logger.error(f"Тілді өзгерту кезінде қате: {str(e)}")
        bot.edit_message_text("❌ Қате орын алды. Әрекетті қайталап көріңіз.", call.message.chat.id, call.message.message_id)








# Қолданушының тілін алу
def get_user_language(user_id):
    user_id = str(user_id)
    return users.get(user_id, {}).get("language", "Қазақша")  # Егер тіл орнатылмаған болса, әдепкісі – Қазақша

@bot.message_handler(commands=['language'])
def change_language(message):
    try:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("🇰🇿 Қазақша", callback_data="lang_kz")
        btn2 = types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
        btn3 = types.InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, "🌍 Тілді таңдаңыз | Выберите язык | Choose a language:", reply_markup=markup)
    except Exception as e:
        logger.error(f"/language командасында қате: {str(e)}")
        bot.send_message(message.chat.id, "❌ Қате орын алды. Әрекетті қайталап көріңіз.")





@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    try:
        user_id = str(call.message.chat.id)
        lang_map = {
            "lang_kz": "Қазақша",
            "lang_ru": "Русский",
            "lang_en": "English",
        }
        language = lang_map.get(call.data, "Қазақша")

        # Егер user_id users ішінде болмаса, оны қосу
        if user_id not in users:
            users[user_id] = {"language": language}
        else:
            users[user_id]["language"] = language  # Тілді өзгерту

        save_users(users)  # Өзгерістерді сақтау

        bot.edit_message_text(translations["language_l"][language], call.message.chat.id, call.message.message_id)
        logger.info(f"Қолданушы {user_id} тілін {language} етіп өзгертті")
    except Exception as e:
        logger.error(f"Тілді өзгерту кезінде қате: {str(e)}")
        bot.edit_message_text("❌ Қате орын алды. Әрекетті қайталап көріңіз.", call.message.chat.id, call.message.message_id)




@bot.message_handler(commands=['help'])
def send_help(message):
    user_id = message.chat.id
    language = get_user_language(user_id)
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton(translations["developer"][language], url="https://t.me/Nuryk12344")
    btn2 = types.InlineKeyboardButton(translations["commands"][language], callback_data="commands")
    markup.add(btn1)
    markup.add(btn2)
    bot.send_message(message.chat.id, translations["help_text"][language], reply_markup=markup, parse_mode="HTML")
    bot.forward_message(ADMIN_IDS, message.chat.id, message.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    language = get_user_language(user_id)
    if call.data == "commands":
        if call.message.chat.id in ADMIN_IDS:
            # Егер админ болса, барлық командалар шығады
            COMMANDS_HELP_TEXT = """
<b>📜 Боттағы барлық командалар:</b>

🔹 <b>/start</b> – Ботты іске қосу
🔹 <b>/help</b> – Көмек және байланыс
🔹 <b>/allow [ID]</b> – Қолданушыға рұқсат беру (Админ)
🔹 <b>/deny [ID]</b> – Қолданушыны бұғаттау (Админ)
🔹 <b>/allowed_users</b> – Рұқсат етілген қолданушылар тізімі (Админ)
🔹 <b>/sendall [мәтін]</b> – Барлық қолданушыға хабарлама жібер (Админ)
🔹 <b>/send [ID] [ТЕКСТ]</b> – Белгілі бір қолданушыға жеке хабарлама жіберу (Админ)
🔹 <b>/users</b> – Барлық тіркелген қолданушылардың ID-сін көру (Админ).
🔹 <b>/user [ID]</b> – Қолданушы туралы толық ақпаратты көру (Админ).
🔹 <b>/users_list</b> – Барлық қолданушылардың толық ақпаратын көру (Админ).

🛠 <i>Әр команданың мақсаты:</i>
✅ <b>/start</b> – Ботты алғаш рет іске қосады.
✅ <b>/help</b> – Бот туралы ақпарат береді.
✅ <b>/allow</b> – Белгілі бір қолданушыға ботты пайдалануға рұқсат береді.
✅ <b>/deny</b> – Белгілі бір қолданушыны бұғаттайды.
✅ <b>/allowed_users</b> – Рұқсат етілген қолданушылардың тізімін көрсетеді.
✅ <b>/sendall</b> – Барлық қолданушыға бірдей хабарлама жібереді.
✅ <b>/user</b> – Қолданушының Telegram ID-сі бойынша жеке чат ашу батырмасын жасайды.
✅ <b>/send</b> – Белгілі бір қолданушыға тікелей бот арқылы хабарлама жіберуге мүмкіндік береді.
✅ <b>/users</b> – Барлық тіркелген қолданушылардың ID-сін тізімдеп көрсетеді.
✅ <b>/user [ID]</b> – Белгілі бір қолданушының толық мәліметін (аты, тегі, тілі, юзернеймі) шығарады.
✅ <b>/users_list</b> – Барлық қолданушылардың толық ақпаратын (аты, тегі, тілі, юзернеймі) көрсетеді.
            """
            bot.send_message(call.message.chat.id, COMMANDS_HELP_TEXT, parse_mode='html')
        else:
            # Егер жай қолданушы болса, қысқаша нұсқа шығады
            bot.send_message(call.message.chat.id, translations["command_user"][language], parse_mode='HTML')

@bot.message_handler(commands=['allow'])
def allow_user(message):
    user_id = message.chat.id
    language = get_user_language(user_id)
    try:
        if message.chat.id in ADMIN_IDS:  # Changed comparison
            try:
                command_parts = message.text.split()
                if len(command_parts) != 2:
                    bot.reply_to(message, "❌ Қате! Қолданушы ID-ін көрсетіңіз.\nМысалы: /allow 123456789")
                    return

                user_id = int(command_parts[1])
                allowed_users.add(user_id)
                save_allowed_users(allowed_users)
                bot.send_message(user_id, translations["allow_user"][language])
                bot.reply_to(message, f"✅ {user_id} ID-сы бар қолданушыға рұқсат берілді.")
                logger.info(f"Әкімші {message.chat.id} пайдаланушыға рұқсат берді {user_id}")
            except ValueError:
                bot.reply_to(message, "❌ Қате! ID тек сандардан тұруы керек.\nМысалы: /allow 123456789")
        else:
            bot.send_message(message.chat.id, translations["e"][language])
            logger.warning(f"Рұқсатсыз қолданушы әкімші командасын пайдаланды: {message.chat.id}")
    except Exception as e:
        error_msg = f"Allow командасында қате: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        bot.send_message(message.chat.id, "❌ Қате орын алды. Әрекетті қайталап көріңіз.")

@bot.message_handler(commands=['deny'])
def deny_user(message):
    user_id = message.chat.id
    language = get_user_language(user_id)
    try:
        if message.chat.id in ADMIN_IDS:  # Changed comparison
            try:
                command_parts = message.text.split()
                if len(command_parts) != 2:
                    bot.reply_to(message, "❌ Қате! Қолданушы ID-ін көрсетіңіз.\nМысалы: /deny 123456789")
                    return

                user_id = int(command_parts[1])
                allowed_users.discard(user_id)
                save_allowed_users(allowed_users)
                bot.send_message(user_id, translations["user_a"][language])
                bot.reply_to(message, f"❌ {user_id} ID-сы бар қолданушыға тыйым салынды.")
                logger.info(f"Әкімші {message.chat.id} пайдаланушыға тыйым салды {user_id}")
            except ValueError:
                bot.reply_to(message, "❌ Қате! ID тек сандардан тұруы керек.\nМысалы: /deny 123456789")
        else:
            bot.send_message(message.chat.id, translations["e"][language])
            logger.warning(f"Рұқсатсыз қолданушы әкімші командасын пайдаланды: {message.chat.id}")
    except Exception as e:
        error_msg = f"Deny командасында қате: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        bot.send_message(message.chat.id, "❌ Қате орын алды. Әрекетті қайталап көріңіз.")

@bot.message_handler(commands=['allowed_users'])
def show_allowed_users(message):
    try:
        if message.chat.id in ADMIN_IDS:  # Changed comparison
            if allowed_users:
                users_list = "\n".join([f"- <code>{user_id}</code>" for user_id in allowed_users])
                bot.send_message(message.chat.id, f"✅ Рұқсат берілген қолданушылар:\n{users_list}", parse_mode='html')
                logger.info(f"Әкімші {message.chat.id} қолданушылар тізімін қарады")
            else:
                bot.send_message(message.chat.id, "⚠️ Рұқсат етілген пайдаланушылар тізімі бос.")
        else:
            bot.send_message(message.chat.id, translations["e"][language])
            logger.warning(f"Рұқсатсыз қолданушы әкімші командасын пайдаланды: {message.chat.id}")
    except Exception as e:
        error_msg = f"Allowed users командасында қате: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        bot.send_message(message.chat.id, "❌ Қате орын алды. Әрекетті қайталап көріңіз.")

@bot.message_handler(commands=['sendall'])
def send_to_all(message):
    user_id = message.chat.id
    language = get_user_language(user_id)
    try:
        if message.chat.id not in ADMIN_IDS:  # Тек әкімшілер қолдана алады
            bot.send_message(message.chat.id, translations["e"][language])
            return

        text = message.text.replace('/sendall', '').strip()
        if not text:
            bot.send_message(message.chat.id, "❗ Хабарлама жіберу үшін мәтінді қосыңыз! Мысалы: \n<code>/sendall Барлығына сәлем!</code>", parse_mode="HTML")
            return

        failed_users = []  # Хабарлама жібере алмаған қолданушылар
        success_count = 0

        for user_id in allowed_users:
            try:
                bot.send_message(user_id, text, parse_mode="HTML")
                success_count += 1
            except Exception as e:
                logger.error(f"Қолданушыға хабарлама жіберу кезінде қате ({user_id}): {str(e)}")
                failed_users.append(user_id)

        # Әкімшіге есеп беру
        result_text = f"✅ {success_count} қолданушыға хабарлама жіберілді."
        if failed_users:
            failed_list = "\n".join([f"- <code>{uid}</code>" for uid in failed_users])
            result_text += f"\n⚠️ Хабарлама жіберілмеген қолданушылар:\n{failed_list}"

        bot.send_message(message.chat.id, result_text, parse_mode="HTML")

    except Exception as e:
        error_msg = f"/sendall командасында қате: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        bot.send_message(message.chat.id, "❌ Қате орын алды. Әрекетті қайталап көріңіз.")

# users_info.json файлынан мәліметтерді оқу
def load_users():
    try:
        with open(USERS_LANGUAGE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Профиль сілтемесі бар батырма жасау
def generate_profile_button(user_id):
    url = f"tg://openmessage?user_id={user_id}"  # Telegram профиліне сілтеме
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("🔗 Профильді қарау", url=url)
    markup.add(button)
    return markup



# /жберу [ID] [ТЕКСТ] командасын өңдеу
@bot.message_handler(commands=['send'])
def send_message_to_user(message):
    try:
        parts = message.text.split(maxsplit=2)  # /жберу ID мәтін
        if len(parts) < 3:
            bot.reply_to(message, "Қолдану үлгісі:\n/send [ID] [Хабарлама]")
            return

        user_id = int(parts[1])  # ID-ін алу
        text = parts[2]  # Хабарлама мәтіні

        bot.send_message(user_id, text)  # Белгіленген қолданушыға хабарлама жіберу
        bot.reply_to(message, f"<b>Хабарлама <code>{user_id}</code></b> қолданушысына жіберілді!", parse_mode='html')

    except ValueError:
        bot.reply_to(message, "Қате! ID дұрыс емес.")
    except Exception as e:
        bot.reply_to(message, f"Қате орын алды: {e}")




@bot.message_handler(commands=["users"])
def send_users(message):
    user = message.from_user

    if user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ Сізге бұл команданы қолдануға рұқсат жоқ!")
        return

    users = load_users()
    if not users:
        bot.reply_to(message, "🔍 Қолданушылар табылмады.")
        return

    response = "👥 *Тіркелген қолданушылар:*\n\n"
    for user_id in users.keys():
        response += f"🆔 `{user_id}`\n"

    bot.reply_to(message, response, parse_mode="Markdown")

@bot.message_handler(commands=["user"])
def get_user_info(message):
    user = message.from_user
    if user.id not in ADMIN_IDS:
        bot.reply_to(message, "⛔ Сізге бұл команданы қолдануға рұқсат жоқ!")
        return

    # Командадан ID алу ("/user 123456789")
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        bot.reply_to(message, "❌ Қолданушы ID-н дұрыс көрсетіңіз! Мысалы: `/user 123456789`", parse_mode="Markdown")
        return

    user_id = parts[1]
    users = load_users()

    if user_id not in users:
        bot.reply_to(message, "❌ Мұндай қолданушы табылмады!")
        return

    user_info = users[user_id]

    first_name = user_info.get("first_name", "?")
    last_name = user_info.get("last_name", "?")
    username = f"{user_info['username']}" if user_info.get("username") else "?"
    language = user_info.get("language", "?")

    response = (
        f"👤 *Қолданушы*\n\n"
        f"🆔 *ID:* `{user_id}`\n"
        f"👤 *Аты:* {first_name}\n"
        f"👥 *Тегі:* {last_name}\n"
        f"🌍 *Тілі:* {language}\n"
        f"🔗 *Username:* {username}\n"
    )

    bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=generate_profile_button(user_id))

@bot.message_handler(commands=["users_list"])
def send_users(message):
    user = message.from_user

    if user.id not in ADMIN_IDS:
        #bot.reply_to(message, "⛔ Сізге бұл команданы қолдануға рұқсат жоқ!")
        notify_admins(user, "🔎 /users командасын орындауға тырысты")
        return

    users = load_users()
    if not users:
        bot.reply_to(message, "🔍 Қолданушылар табылмады.")
        return

    response = "👥 *Тіркелген қолданушылар:*\n\n"
    for user_id, info in users.items():
        first_name = info.get("first_name", "?")
        last_name = info.get("last_name", "?")
        username = f"{info['username']}" if info.get("username") else "?"
        language = info.get("language", "?")

        response += (
            f"🆔 *ID:* `{user_id}`\n"
            f"👤 *Аты:* {first_name}\n"
            f"👥 *Тегі:* {last_name}\n"
            f"🌍 *Тілі:* {language}\n"
            f"🔗 *Username:* {username}\n\n"
        )

    bot.reply_to(message, response, parse_mode="Markdown")

# Кез келген хабарламаны өңдеу
@bot.message_handler(func=lambda message: True)
def track_user_activity(message):
    user = message.from_user
    if user.id not in ADMIN_IDS:
        notify_admins(user, f"📩 Хабарлама жіберді: `{message.text}`")





#@bot.message_handler(content_types=["document", "photo", "audio", "video"])
#def forward_to_admin(message):
#    """Кез келген файлды әкімшіге 'переслать' етіп жібереді"""
#    bot.forward_message(ADMIN_IDS, message.chat.id, message.message_id)

@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.chat.id
    language = get_user_language(user_id)
    bot.forward_message(ADMIN_IDS, message.chat.id, message.message_id)
    try:
        user_id = message.chat.id
        if user_id not in allowed_users:
            bot.send_message(user_id, translations["user_a"][language])
            return

        logger.info(f"Файл қабылданды: {message.document.file_name}")
        processing_msg = bot.send_message(user_id, translations["file"][language])

        # Get and save the file
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process based on file type
        mime_type = file_processor.detect_file_type(file_name)
        txt_file = f"input_{user_id}.txt"
        processed_file = f"processed_{user_id}.txt"

        file_ext = os.path.splitext(file_name)[1].lower()
        logger.info(f"Файл түрі: {mime_type}, кеңейтім: {file_ext}")

        try:
            if file_ext in ['.doc', '.docx'] or (mime_type and ('msword' in mime_type or 'wordprocessingml' in mime_type)):
                file_processor.convert_doc_to_txt(file_name, txt_file)
                logger.info("DOC/DOCX файлы сәтті өңделді")
            elif file_ext in ['.pdf'] or (mime_type and 'pdf' in mime_type):
                file_processor.convert_pdf_to_txt(file_name, txt_file)
                logger.info("PDF файлы сәтті өңделді")
            elif file_ext in ['.xls', '.xlsx'] or (mime_type and 'spreadsheetml' in mime_type):
                file_processor.convert_excel_to_txt(file_name, txt_file)
                logger.info("Excel файлы сәтті өңделді")
            elif mime_type and mime_type.startswith('image/'):
                file_processor.convert_image_to_txt(file_name, txt_file)
                logger.info("Сурет файлы сәтті өңделді")
            else:
                bot.edit_message_text(
                    translations["file_edit"][language],
                    user_id,
                    processing_msg.message_id
                )
                return

            # Process the text file
            file_processor.process_file(txt_file, processed_file)
            logger.info("Файл сәтті өңделді")

            # Send the processed file
            with open(processed_file, 'rb') as f:
                bot.send_document(user_id, f)
            bot.edit_message_text(translations["file_edit_y"][language], user_id, processing_msg.message_id)
            logger.info("Өңделген файл жіберілді")

        except Exception as e:
            error_msg = f"Файлды өңдеу кезінде қате: {str(e)}"
            logger.error(error_msg)
            bot.edit_message_text(
                translations["file_edit_e"][language],
                user_id,
                processing_msg.message_id
            )
        finally:
            # Cleanup
            for file in [file_name, txt_file, processed_file]:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                except Exception as e:
                    logger.error(f"Файлды жою кезінде қате {file}: {str(e)}")

    except Exception as e:
        error_msg = f"Файлды өңдеу кезінде қате: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        bot.send_message(user_id, translations["file_edit_e"][language])
        bot.forward_message(ADMIN_IDS, message.chat.id, message.message_id)

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'sticker', 'audio'])
def forward(message):
    try:
        # Skip forwarding if message is from admin or is an admin command
        if message.chat.id in ADMIN_IDS: # Changed comparison
            return

        if message.text and message.text.startswith('/'):
            # If it's a command from non-admin, only send log
            send_log_to_admin(message, f"Команда қолданылды: {message.text}")
            return

        # Forward regular messages to admins
        for admin_id in ADMIN_IDS:
            try:
                bot.forward_message(admin_id, message.chat.id, message.message_id)
            except Exception as e:
                logger.error(f"Әкімшіге хабарлама жіберу кезінде қате (ID: {admin_id}): {str(e)}")

        # Send log message for non-command messages
        send_log_to_admin(message, message.text if message.text else "Мазмұн (файл)")
    except Exception as e:
        logger.error(f"Хабарламаны жіберу кезінде қате: {str(e)}")


def main():
    logger.info("Бот іске қосылуда...")
    while True:
        try:
            logger.info("Бот іске қосылды")
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            error_msg = f"Бот тоқтады: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            time.sleep(5)  # Қайта қосылу алдында күту
            continue

if __name__ == "__main__":
    main()