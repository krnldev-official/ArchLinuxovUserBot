from datetime import datetime, timedelta, timezone

def setup(registry):
    # Регистрация команды .test в модуле SystemInfo
    registry.register_command("test", mod_test, module_name="SystemInfo")

async def mod_test(client, message, api):
    """Выводит текущее московское время и активное ядро системы."""
    # Вычисляем точное московское время (UTC+3)
    tz_moscow = timezone(timedelta(hours=3))
    moscow_time = datetime.now(tz_moscow).strftime("%d.%m.%Y %H:%M:%S")
    
    # Получаем режим ядра через кастомное API
    kernel_mode = api.kernel.mode
    
    # Формируем итоговый текст
    text = (
        f"📊 **Системный статус:**\n\n"
        f"🕒 **Время в Москве:** `{moscow_time}`\n"
        f"🐧 **Текущее ядро:** `{kernel_mode}`"
    )
    
    # Отправляем ответ строго через встроенный метод во избежание флуда
    await api.edit_or_reply(message, text)

