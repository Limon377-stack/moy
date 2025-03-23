from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
from handlers import photo
import json

router = Router()

# Функция для загрузки данных из файла
async def load_profile(user_id):
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return data.get(str(user_id), {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# Сохранение данных в файл
def save_profile(user_id, data):
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            profiles = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        profiles = {}

    profiles[str(user_id)] = data

    with open("user_profiles.json", "w", encoding="utf-8") as file:
        json.dump(profiles, file, ensure_ascii=False, indent=4)


# Функция для запроса описания с кнопкой "Пропустить"
async def ask_description(message: types.Message, state: FSMContext):
    """Запрашиваем у пользователя описание или предлагаем пропустить."""

    # Создаем клавиатуру с кнопкой "Пропустить"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Пропустить")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True  # Важный момент — клавиатура временная
    )

    # Запрос описания с кнопкой
    await message.answer("Расскажи немного о себе:", reply_markup=keyboard)

    # Сохраняем состояние для описания
    await state.set_state(Form.description)


# Обрабатываем описание с проверкой на минимум два слова или пропуск
@router.message(Form.description)
async def process_description(message: types.Message, state: FSMContext):
    """Обрабатываем введённое описание, проверяем его валидность или пропускаем."""
    description = message.text.strip()
    user_id = message.from_user.id
    user_data = await load_profile(user_id)

    # Если пользователь нажал "Пропустить" — сразу переходим к фото
    if description.lower() == "пропустить":
        from handlers.photo import ask_photo
        await ask_photo(message, state)
        return

    # Проверка на минимум два слова
    if len(description.split()) < 2:
        await message.answer("Описание должно содержать минимум два слова. Попробуй ещё раз!")
        return

    # Сохраняем описание в файл
    user_data['description'] = description
    save_profile(user_id, user_data)

    # Переходим к следующему шагу — запрос фото
    from handlers.photo import ask_photo
    await ask_photo(message, state)
