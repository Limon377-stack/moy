from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
import json
from .age_and_city import ask_age

router = Router()

# Функция для загрузки данных из файла
async def load_profile(user_id):
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        return data.get(str(user_id), {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Функция для сохранения данных
def save_profile(user_id, data):
    try:
        with open("user_profiles.json", "r", encoding="utf-8") as file:
            profiles = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        profiles = {}

    profiles[str(user_id)] = data

    with open("user_profiles.json", "w", encoding="utf-8") as file:
        json.dump(profiles, file, ensure_ascii=False, indent=4)

# Приветствие с кнопкой "Создать анкету"
@router.message(F.text == "/start")
async def welcome_message(message: types.Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Создать анкету")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Привет! Давай создадим твою анкету.", reply_markup=keyboard)

# Старт анкеты — запрос имени
@router.message(F.text == "Создать анкету")
async def start_profile(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)
    name = user_data.get("name")

    # Если имя уже сохранено — предлагаем его кнопкой
    if name:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"{name}")]],
            resize_keyboard=True
        )
        await message.answer("Давайте начнём с имени! Введи своё имя:", reply_markup=keyboard)
    else:
        await message.answer("Давайте начнём с имени! Введи своё имя:", reply_markup=ReplyKeyboardRemove())
    
    await state.set_state(Form.name)

# Обработка имени
@router.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)

    # Сохраняем имя
    user_data["name"] = message.text
    save_profile(user_id=message.from_user.id, data=user_data)

    # Переход к возрасту
    await ask_age(message, state)
