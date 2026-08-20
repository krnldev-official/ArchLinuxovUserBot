from hydrogram.raw import functions, types
def setup(registry):
    # Регистрируем команду myusern (строго без точки)
    registry.register_command("myusern", mod_myusern, module_name="MyUsernames")

async def mod_myusern(client, message, api):
    """Выводит список публичных юзернеймов (каналов/групп), которые зарезервированы тобой."""
    
    try:
        # Используем Raw API Pyrogram для вызова метода GetAdminedPublicChannels
        # Это прямой аналог функции из Telethon
        result = await client.invoke(functions.channels.GetAdminedPublicChannels())
        
        output_str = "• "
        has_usernames = False
        
        for chat in result.chats:
            # Проверяем, что чат является каналом/супергруппой и имеет установленный username
            if isinstance(chat, types.Channel) and getattr(chat, 'username', None):
                output_str += f"<code>{chat.title}</code> | <b>@{chat.username}</b>\n• "
                has_usernames = True
        
        # Формируем итоговое сообщение
        if has_usernames:
            final_text = f"<b>💼 List usernames reserved by me</b>\n\n{output_str[:-3]}"
        else:
            final_text = "<b>🤷‍♂️ У тебя нет зарезервированных публичных юзернеймов.</b>"
            
        # Отправляем результат строго через кастомное API юзербота
        await api.edit_or_reply(message, final_text)
        
    except Exception as e:
        # Элегантный перехват ошибок на случай ограничений со стороны Telegram
        await api.edit_or_reply(message, f"<b>❌ Ошибка при получении юзернеймов:</b>\n<code>{str(e)}</code>")

