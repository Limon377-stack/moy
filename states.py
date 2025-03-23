from aiogram.fsm.state import State, StatesGroup
import json

# Файл для хранения данных
DB_FILE = "user_profiles.json"

# Функция для сохранения данных с проверкой уникальности по user_id
def save_profile(user_id, data):
    try:
        with open(DB_FILE, "r", encoding="utf-8") as file:
            profiles = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        profiles = {}

    # Сохраняем или обновляем профиль по user_id
    profiles[str(user_id)] = data

    # Сохраняем в файл
    with open(DB_FILE, "w", encoding="utf-8") as file:
        json.dump(profiles, file, ensure_ascii=False, indent=4)

    # Формируем строку с данными анкеты в формате: id - имя, возраст, город, описание, фото
    profile_line = (
        f"{user_id} - "
        f"{data.get('name', 'неизвестно')}, "
        f"{data.get('age', '??')} лет, "
        f"{data.get('city', 'неизвестно')} - "
        f"{data.get('description', 'нет описания')}, "
        f"Фото: {data.get('photo', 'нет фото')}"
    )
    print(profile_line)  # Для отладки

# Определяем состояния для машины состояний
class Form(StatesGroup):
    name = State()
    age = State()
    city = State()
    description = State()
    photo = State()

# Пример использования
async def process_city(message, state):
    """Пример заполнения данных и сохранения профиля."""
    user_data = {
        "name": "Иван",
        "age": 25,
        "city": "Москва",
        "description": "Люблю путешествовать",
        "photo": "photo_id"
    }
    user_id = message.from_user.id
    save_profile(user_id, user_data)
