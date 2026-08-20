def setup(registry):
    registry.register_command("id", mod_id, module_name="Info")
    registry.register_command("chatinfo", mod_chatinfo, module_name="Info")

async def mod_id(client, message, api):
    chat = message.chat
    reply = message.reply_to_message

    text = f"Чат айди: {chat.id} \n"
    if reply:
        user_id = reply.from_user.id if reply.from_user else "Скрыт/Бот"
        text += f"Юз айди : {user_id}\n"
        text += f"Айди сообщения: {reply.id}"
    else:
        text += f"Твой айди: {message.from_user.id}"
    await api.edit_or_reply(message, text)

async def mod_chatinfo(client, message, api):
    """Получить инфлрмациб про чат и айди"""
    await api.edit_or_reply(message, "🔄 **Сбор информации...**")

    try:
        chat = await client.get_chat(message.chat.id)
        chat_type_map = {
            "PRIVATE": "Личный чат",
            "BOT": "Диалог с ботом",
            "GROUP": "Группа",
            "SUPERGROUP": "Супергруппа",
            "CHANNEL": "Канал"
        }
        type_str = chat_type_map.get(str(chat.type).split(".")[-1].upper(), str(chat.type))

        info = (
            f"Информация о чате\n"
            f"--------------------------------\n"
            f"Название:{chat.title or chat.first_name or 'Без названия'}\n"
            f"ID: {chat.id}\n"
            f"Тип: {type_str}\n"
        )

        if hasattr(chat, "members_count") and chat.members_count:
            info += f"Участников: {chat.members_count}\n"

        if chat.username:
            info += f"Юзернейм: @{chat.username}\n"

        if getattr(chat, "dc_id", None):
            info += f"Дата-центр: {chat.dc_id}\n"

        if chat.description:
            desc = chat.description[:100] + "..." if len(chat.description) > 100 else chat.description
            info += f"Описание: {desc}\n"

        await api.edit_or_reply(message, info)

    except Exception as e:
        await api.edit_or_reply(message, f"Ошибка при получении данных: {e}")
