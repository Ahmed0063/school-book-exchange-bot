import sqlite3
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8308890169:AAE-kW4flu-SNLHc85JICAfaGPsXNSEDR2s"
DB_NAME = "books.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            school_class TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            owner_name TEXT NOT NULL
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            from_user_id INTEGER NOT NULL,
            from_user_name TEXT NOT NULL
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS stats (
            user_id INTEGER PRIMARY KEY,
            success_count INTEGER DEFAULT 0
        )
    """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_user_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5)
        )
    """
    )

    conn.commit()
    conn.close()


def register_user(user_id: int, first_name: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT OR REPLACE INTO users (user_id, first_name)
        VALUES (?, ?)
    """,
        (user_id, first_name),
    )

    cur.execute(
        """
        INSERT OR IGNORE INTO stats (user_id, success_count)
        VALUES (?, 0)
    """,
        (user_id,),
    )

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.first_name)

    await update.message.reply_text(
        "📚 Привет! Я бот для школьного книгообмена.\n\n"
        "Через меня можно добавлять книги, смотреть каталог и отправлять заявки на обмен.\n\n"
        "Основные команды:\n"
        "/add Название книги ; Класс\n"
        "/list — список всех книг\n"
        "/filter Класс — фильтр по классу\n"
        "/mybooks — мои книги\n"
        "/request ID — запросить книгу\n"
        "/approve ID — подтвердить обмен\n"
        "/decline ID — отклонить обмен\n"
        "/rate user_id оценка — оценить пользователя\n"
        "/stats — моя статистика\n\n"
        "Пример:\n"
        "/add Гарри Поттер и философский камень ; 10"
    )


async def add_book(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.first_name)

    full_text = update.message.text.replace("/add", "", 1).strip()

    if ";" not in full_text:
        await update.message.reply_text(
            "❗ Используй формат:\n"
            "/add Название книги ; Класс\n\n"
            "Пример:\n"
            "/add Гарри Поттер ; 10"
        )
        return

    title_part, class_part = full_text.split(";", 1)
    title = title_part.strip()
    school_class = class_part.strip()

    if not title or not school_class:
        await update.message.reply_text(
            "❌ Название книги и класс не должны быть пустыми."
        )
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO books (title, school_class, owner_id, owner_name)
        VALUES (?, ?, ?, ?)
    """,
        (title, school_class, user.id, user.first_name),
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(f"✅ Книга «{title}» добавлена в каталог.")


async def list_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, school_class, owner_name
        FROM books
        ORDER BY id
    """
    )
    books = cur.fetchall()
    conn.close()

    if not books:
        await update.message.reply_text("📭 Пока в каталоге нет книг.")
        return

    text = "📚 Каталог книг:\n\n"
    for book_id, title, school_class, owner_name in books:
        text += f"ID {book_id}. {title} (класс {school_class}) — {owner_name}\n"

    await update.message.reply_text(text)


async def filter_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Используй так:\n/filter 10")
        return

    school_class = context.args[0]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, owner_name
        FROM books
        WHERE school_class = ?
        ORDER BY id
    """,
        (school_class,),
    )
    books = cur.fetchall()
    conn.close()

    if not books:
        await update.message.reply_text("📭 Для этого класса книг пока нет.")
        return

    text = f"📘 Книги для {school_class} класса:\n\n"
    for book_id, title, owner_name in books:
        text += f"ID {book_id}. {title} — {owner_name}\n"

    await update.message.reply_text(text)


async def my_books(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.first_name)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, school_class
        FROM books
        WHERE owner_id = ?
        ORDER BY id
    """,
        (user.id,),
    )
    books = cur.fetchall()
    conn.close()

    if not books:
        await update.message.reply_text("📕 У тебя пока нет добавленных книг.")
        return

    text = "📗 Твои книги:\n\n"
    for book_id, title, school_class in books:
        text += f"ID {book_id}. {title} (класс {school_class})\n"

    await update.message.reply_text(text)


async def request_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.first_name)

    if not context.args:
        await update.message.reply_text("❗ Используй так:\n/request ID")
        return

    try:
        book_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID книги должен быть числом.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, owner_id, owner_name
        FROM books
        WHERE id = ?
    """,
        (book_id,),
    )
    book = cur.fetchone()

    if not book:
        conn.close()
        await update.message.reply_text("❌ Книга не найдена.")
        return

    _, title, owner_id, owner_name = book

    if owner_id == user.id:
        conn.close()
        await update.message.reply_text(
            "❌ Нельзя отправить запрос на свою собственную книгу."
        )
        return

    cur.execute(
        """
        SELECT id FROM requests
        WHERE book_id = ? AND from_user_id = ?
    """,
        (book_id, user.id),
    )
    existing_request = cur.fetchone()

    if existing_request:
        conn.close()
        await update.message.reply_text("❗ Ты уже отправлял заявку на эту книгу.")
        return

    cur.execute(
        """
        INSERT INTO requests (book_id, from_user_id, from_user_name)
        VALUES (?, ?, ?)
    """,
        (book_id, user.id, user.first_name),
    )

    conn.commit()
    conn.close()

    try:
        await context.bot.send_message(
            chat_id=owner_id,
            text=(
                f"📩 Пользователь {user.first_name} хочет получить книгу:\n"
                f"«{title}»\n\n"
                f"Подтвердить: /approve {book_id}\n"
                f"Отклонить: /decline {book_id}"
            ),
        )
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ Заявка на книгу «{title}» отправлена пользователю {owner_name}."
    )


async def approve_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner = update.effective_user
    register_user(owner.id, owner.first_name)

    if not context.args:
        await update.message.reply_text("❗ Используй так:\n/approve ID")
        return

    try:
        book_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID книги должен быть числом.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, title, owner_id
        FROM books
        WHERE id = ?
    """,
        (book_id,),
    )
    book = cur.fetchone()

    if not book:
        conn.close()
        await update.message.reply_text("❌ Книга не найдена.")
        return

    _, title, owner_id = book

    if owner_id != owner.id:
        conn.close()
        await update.message.reply_text(
            "❌ Ты можешь подтверждать обмен только для своих книг."
        )
        return

    cur.execute(
        """
        SELECT id, from_user_id, from_user_name
        FROM requests
        WHERE book_id = ?
        ORDER BY id ASC
        LIMIT 1
    """,
        (book_id,),
    )
    request_row = cur.fetchone()

    if not request_row:
        conn.close()
        await update.message.reply_text("❌ Для этой книги нет активных заявок.")
        return

    request_id, new_owner_id, new_owner_name = request_row

    cur.execute(
        """
        UPDATE books
        SET owner_id = ?, owner_name = ?
        WHERE id = ?
    """,
        (new_owner_id, new_owner_name, book_id),
    )

    cur.execute(
        """
        UPDATE stats
        SET success_count = success_count + 1
        WHERE user_id = ?
    """,
        (new_owner_id,),
    )

    cur.execute(
        """
        DELETE FROM requests
        WHERE book_id = ?
    """,
        (book_id,),
    )

    conn.commit()
    conn.close()

    try:
        await context.bot.send_message(
            chat_id=new_owner_id,
            text=f"🎉 Твоя заявка одобрена. Теперь книга «{title}» закреплена за тобой.",
        )
    except Exception:
        pass

    await update.message.reply_text(f"✅ Обмен по книге «{title}» подтверждён.")


async def decline_exchange(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner = update.effective_user
    register_user(owner.id, owner.first_name)

    if not context.args:
        await update.message.reply_text("❗ Используй так:\n/decline ID")
        return

    try:
        book_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ ID книги должен быть числом.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT title, owner_id
        FROM books
        WHERE id = ?
    """,
        (book_id,),
    )
    book = cur.fetchone()

    if not book:
        conn.close()
        await update.message.reply_text("❌ Книга не найдена.")
        return

    title, owner_id = book

    if owner_id != owner.id:
        conn.close()
        await update.message.reply_text(
            "❌ Ты можешь отклонять заявки только для своих книг."
        )
        return

    cur.execute(
        """
        SELECT id, from_user_id
        FROM requests
        WHERE book_id = ?
        ORDER BY id ASC
        LIMIT 1
    """,
        (book_id,),
    )
    request_row = cur.fetchone()

    if not request_row:
        conn.close()
        await update.message.reply_text("❌ Для этой книги нет активных заявок.")
        return

    request_id, requester_id = request_row

    cur.execute(
        """
        DELETE FROM requests
        WHERE id = ?
    """,
        (request_id,),
    )

    conn.commit()
    conn.close()

    try:
        await context.bot.send_message(
            chat_id=requester_id,
            text=f"❌ Твоя заявка на книгу «{title}» была отклонена.",
        )
    except Exception:
        pass

    await update.message.reply_text("✅ Заявка отклонена.")


async def rate_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❗ Используй так:\n/rate user_id 5")
        return

    try:
        target_user_id = int(context.args[0])
        score = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ user_id и оценка должны быть числами.")
        return

    if score < 1 or score > 5:
        await update.message.reply_text("❌ Оценка должна быть от 1 до 5.")
        return

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO ratings (target_user_id, score)
        VALUES (?, ?)
    """,
        (target_user_id, score),
    )

    conn.commit()
    conn.close()

    await update.message.reply_text("✅ Оценка сохранена.")


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    register_user(user.id, user.first_name)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT success_count
        FROM stats
        WHERE user_id = ?
    """,
        (user.id,),
    )
    stats_row = cur.fetchone()

    cur.execute(
        """
        SELECT AVG(score), COUNT(*)
        FROM ratings
        WHERE target_user_id = ?
    """,
        (user.id,),
    )
    rating_row = cur.fetchone()

    conn.close()

    success_count = stats_row[0] if stats_row else 0
    avg_rating = rating_row[0]
    rating_count = rating_row[1] if rating_row else 0

    avg_text = f"{avg_rating:.2f}" if avg_rating is not None else "пока нет"

    await update.message.reply_text(
        "📊 Твоя статистика:\n\n"
        f"Успешных обменов: {success_count}\n"
        f"Средняя оценка: {avg_text}\n"
        f"Количество оценок: {rating_count}"
    )


async def set_commands(app):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("add", "Добавить книгу: /add Название ; Класс"),
        BotCommand("list", "Показать все книги"),
        BotCommand("filter", "Фильтр по классу: /filter 10"),
        BotCommand("mybooks", "Показать мои книги"),
        BotCommand("request", "Запросить книгу: /request ID"),
        BotCommand("approve", "Подтвердить обмен: /approve ID"),
        BotCommand("decline", "Отклонить обмен: /decline ID"),
        BotCommand("rate", "Оценить пользователя: /rate user_id 5"),
        BotCommand("stats", "Показать статистику"),
    ]
    await app.bot.set_my_commands(commands)


def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_book))
    app.add_handler(CommandHandler("list", list_books))
    app.add_handler(CommandHandler("filter", filter_class))
    app.add_handler(CommandHandler("mybooks", my_books))
    app.add_handler(CommandHandler("request", request_exchange))
    app.add_handler(CommandHandler("approve", approve_exchange))
    app.add_handler(CommandHandler("decline", decline_exchange))
    app.add_handler(CommandHandler("rate", rate_user))
    app.add_handler(CommandHandler("stats", stats))

    app.post_init = set_commands

    print("🤖 Бот запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
