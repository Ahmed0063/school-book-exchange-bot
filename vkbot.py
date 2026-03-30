import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

TOKEN = "ТВОЙ_ТОКЕН_ГРУППЫ"
GROUP_ID = 237041501  # твой ID группы

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

print("Бот запущен!")

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        message = event.object["message"]["text"].lower()
        user_id = event.object["message"]["from_id"]

        # ===== СТАРТ =====
        if message == "привет":
            vk.messages.send(
                user_id=user_id,
                random_id=0,
                message="Привет! Я работаю 😎"
            )

        # ===== ДОБАВИТЬ КНИГУ =====
        elif text.lower().startswith("добавить"):
            title = text[9:].strip()

            if not title:
                send_message(user_id, "❗ Напиши: добавить НАЗВАНИЕ")
                continue

            books.append({"title": title, "owner": user_id})

            send_message(user_id, f"✅ Книга «{title}» добавлена")

        # ===== СПИСОК КНИГ =====
        elif text.lower() == "список":
            if not books:
                send_message(user_id, "📭 Книг пока нет")
                continue

            msg = "📚 Список книг:\n\n"
            for i, book in enumerate(books, 1):
                msg += f"{i}. {book['title']}\n"

            send_message(user_id, msg)

        # ===== ЗАПРОС КНИГИ =====
        elif text.lower().startswith("запрос"):
            try:
                index = int(text.split()[1]) - 1

                if index < 0 or index >= len(books):
                    send_message(user_id, "❌ Такой книги нет")
                    continue

                book = books[index]

                if book["owner"] == user_id:
                    send_message(user_id, "❌ Это твоя книга")
                    continue

                requests.append(
                    {"from": user_id, "to": book["owner"], "book": book["title"]}
                )

                # уведомление владельцу
                send_message(
                    book["owner"],
                    f"📩 У тебя запрос на книгу:\n"
                    f"«{book['title']}»\n\n"
                    f"Напиши человеку: vk.com/id{user_id}",
                )

                send_message(user_id, "✅ Заявка отправлена")

            except:
                send_message(user_id, "❗ Используй: запрос НОМЕР")

        # ===== МОИ КНИГИ =====
        elif text.lower() == "мои":
            user_books = [b for b in books if b["owner"] == user_id]

            if not user_books:
                send_message(user_id, "📭 У тебя нет книг")
                continue

            msg = "📚 Твои книги:\n\n"
            for i, book in enumerate(user_books, 1):
                msg += f"{i}. {book['title']}\n"

            send_message(user_id, msg)

        # ===== УДАЛИТЬ КНИГУ =====
        elif text.lower().startswith("удалить"):
            try:
                index = int(text.split()[1]) - 1

                user_books = [b for b in books if b["owner"] == user_id]

                if index < 0 or index >= len(user_books):
                    send_message(user_id, "❌ Неверный номер")
                    continue

                book_to_remove = user_books[index]
                books.remove(book_to_remove)

                send_message(user_id, "🗑 Книга удалена")

            except:
                send_message(user_id, "❗ Используй: удалить НОМЕР")

        else:
            send_message(user_id, "❓ Напиши 'старт'")
