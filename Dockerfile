# Базовый образ Python
FROM python:3.11-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . .

# (Polling‑бот не слушает порты, но пусть контейнер знает, что там 8443)
EXPOSE 8443

# Команда запуска бота
CMD ["python", "bot.py"]
