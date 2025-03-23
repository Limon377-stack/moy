from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from states import Form
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

# Запрос возраста
async def ask_age(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)
    age = user_data.get("age")

    # Если есть возраст, добавляем кнопку с этим возрастом
    if age:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(age))]], resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardRemove()

    await message.answer("Теперь введи свой возраст (0-99):", reply_markup=keyboard)
    await state.set_state(Form.age)

# Обработка возраста
@router.message(Form.age)
async def process_age(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)

    if message.text == f"{user_data.get('age', '')}":
        await ask_city(message, state)
        return

    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи только цифры!")
        return

    age = int(message.text)

    if 0 <= age <= 99:
        user_data['age'] = age
        save_profile(user_id=message.from_user.id, data=user_data)
        await ask_city(message, state)
    else:
        await message.answer("Возраст должен быть от 0 до 99. Попробуй ещё раз!")

# Запрос города
async def ask_city(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)
    city = user_data.get("city")

    # Кнопка только с городом (если он уже сохранён)
    if city:
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=f"{city}")]],
            resize_keyboard=True
        )
    else:
        keyboard = ReplyKeyboardRemove()

    await message.answer("Введи название своего города:", reply_markup=keyboard)
    await state.set_state(Form.city)

# Обработка города
@router.message(Form.city)
async def process_city(message: types.Message, state: FSMContext):
    user_data = await load_profile(message.from_user.id)

    # Если юзер выбрал "Пропустить", город не сохраняем
    if message.text.lower() == "пропустить":
        user_data["city"] = "Не указано"
        save_profile(user_id=message.from_user.id, data=user_data)
        await ask_description(message, state)
        return

    # Сохраняем город, если он введён
    user_data["city"] = message.text
    save_profile(user_id=message.from_user.id, data=user_data)

    await ask_description(message, state)

# Следующий шаг — запрос описания
async def ask_description(message: types.Message, state: FSMContext):
    await message.answer("Расскажи немного о себе:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.description)
