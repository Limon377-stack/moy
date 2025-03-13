import logging
import os
import asyncio
import re
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ContentType
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sys
from aiogram import F
from cities import CITIES
from config import YANDEX_API_KEY
from config import TOKEN

logging.basicConfig(level=logging.INFO)

# Функция обработчика команды /start
async def on_start(message: Message):
    await message.answer("Привет! Бот работает.")

# Инициализация бота с токеном
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # Хранилище для состояний
dp = Dispatcher(storage=storage)  # Создание диспетчера без передачи bot в позиционном аргументе

geolocator = Nominatim(user_agent="geoapiExercises")

USER_DATA_FILE = "users.txt"

# States for profile creation
class ProfileForm(StatesGroup):
    age = State()
    name = State()
    city = State()
    update_name = State()
    update_age = State()
    update_city = State()
    update_description = State()
    update_media = State()

    # Клавиатура выбора 🔄 Обновить анкету, 🔍 Смотреть анкеты"
def get_custom_keyboard(buttons):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=button)] for button in buttons],
        resize_keyboard=True
    )

    # Клавиатура выбора при наличии анкеты
def get_profile_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оставить анкету")],
            [KeyboardButton(text="Создать заново")]
        ],
        resize_keyboard=True
    )

# Main menu keyboard
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📜 Создать анкету")]],
        resize_keyboard=True
    )

# City input keyboard
def get_city_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Отправить местоположение", request_location=True)],
            [KeyboardButton(text="🖊 Ввести город вручную")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Skip button keyboard
def get_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Функция загрузки пользователей из TXT
def load_users():
    users = {}
    if not os.path.exists(USER_DATA_FILE):
        return users

    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(": ")
            if len(parts) == 2:
                user_id, data = parts
                user_id = int(user_id)  # Преобразуем в int для удобства
                age, name, city = data.split(" | ")
                users[user_id] = {"age": age, "name": name, "city": city}
    
    return users

# Функция сохранения пользователей в TXT
def save_users(users):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        for user_id, data in users.items():
            f.write(f"{user_id}: {data['age']} | {data['name']} | {data['city']}\n")

# Функция сохранения данных пользователя (с обновлением)
def save_user_data(user_id, age=None, name=None, city=None):
    users = load_users()

    if user_id in users:
        user_data = users[user_id]
    else:
        user_data = {"age": "Не указано", "name": "Не указано", "city": "Не указано"}

    if age is not None:
        user_data["age"] = age
    if name is not None:
        user_data["name"] = name
    if city is not None:
        user_data["city"] = city

    users[user_id] = user_data
    save_users(users)

# Функция получения данных пользователя
def get_user_data(user_id):
    users = load_users()
    return users.get(user_id, None)

# Start command handler
@dp.message(Command("start"))
async def start(message: Message, state: FSMContext):
    user_data = get_user_data(message.from_user.id)
    print(f"Данные пользователя ({message.from_user.id}):", user_data)  # Отладка
    
    if user_data and all(key in user_data for key in ["age", "name", "city"]):
        age = user_data.get("age", "неизвестно")
        name = user_data.get("name", "неизвестно")
        city = user_data.get("city", "неизвестно")
        
        # Отправляем первое сообщение с приветствием
        await message.answer("👋 Привет! Твоя анкета уже существует:")

        # Формируем анкету и отправляем её как отдельное сообщение
        profile_text = f"📸 {name}, {age}, {city}"
        await message.answer(profile_text)

        # Отправляем сообщение с выбором действия
        await message.answer(
            "Что будем делать дальше?",
            reply_markup=get_custom_keyboard(["🔄 Обновить анкету", "🔍 Смотреть анкеты"])
        )
    else:
        await message.answer(
            "👋 Привет!",
            reply_markup=get_main_keyboard()
        )

# Обновление анкеты
@dp.message(lambda message: message.text == "🔄 Обновить анкету")
async def update_profile(message: Message, state: FSMContext):
    user_data = get_user_data(message.from_user.id)
    if user_data:
        await state.update_data(name=user_data.get("name", "Не указано"))
        await state.update_data(age=user_data.get("age", "Не указано"))
        await state.update_data(city=user_data.get("city", "Не указано"))
    
    await message.answer("Давай обновим твою анкету! ✍️")
    await ask_name(message, state)

# Создание новой анкеты
@dp.message(lambda message: message.text == "📜 Создать анкету")
async def create_new_profile(message: Message, state: FSMContext):
    await state.clear()
    await ask_name(message, state)

# Оставить старую анкету
@dp.message(lambda message: message.text == "Оставить анкету")
async def keep_profile(message: Message):
    await message.answer("✅ Отлично! Твоя анкета сохранена. Приятного общения!", reply_markup=ReplyKeyboardRemove())

# Запрос имени
async def ask_name(message: types.Message, state: FSMContext):
    user_data = get_user_data(message.from_user.id)
    
    if user_data and user_data.get("name") and user_data["name"] != "Не указано":
        name = user_data["name"]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=name)]],
            resize_keyboard=True
        )
        await message.answer("📝 Введи своё имя:", reply_markup=keyboard)
    else:
        await message.answer("📝 Введи своё имя:", reply_markup=ReplyKeyboardRemove())
    
    await state.set_state(ProfileForm.name)

# Обработка ввода имени (или нажатия на кнопку)
@dp.message(ProfileForm.name)
async def validate_name(message: types.Message, state: FSMContext):
    if not message.text.strip():
        await message.delete()
        await message.answer("❌ Имя не может быть пустым! Попробуй снова.")
        return

    await state.update_data(name=message.text)
    user_data = await state.get_data()
    
    save_user_data(
        message.from_user.id, 
        age=user_data.get("age", "Не указано"), 
        name=message.text, 
        city=user_data.get("city", "Не указано")
    )

    await ask_age(message, state)

# Запрос возраста
async def ask_age(message: types.Message, state: FSMContext):
    user_data = get_user_data(message.from_user.id)
    
    if user_data and user_data.get("age") and user_data["age"] != "Не указано":  
        age = user_data["age"]
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(age))]], 
            resize_keyboard=True
        )
        await message.answer("🎂 Сколько тебе лет?", reply_markup=keyboard)
    else:
        await message.answer("🎂 Сколько тебе лет?", reply_markup=ReplyKeyboardRemove())
    
    await state.set_state(ProfileForm.age)

# Обработка возраста
@dp.message(ProfileForm.age)
async def validate_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.delete()
        await message.answer("❌ Возраст должен быть числом больше 0! Попробуй снова.")
        return

    await state.update_data(age=message.text)
    user_data = await state.get_data()
    
    save_user_data(
        message.from_user.id, 
        age=message.text, 
        name=user_data.get("name", "Не указано"), 
        city=user_data.get("city", "Не указано")
    )

    await ask_city(message, state)

# Запрос города
async def ask_city(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    previous_city = user_data.get('city')

    # Если город уже был введен, показываем кнопку с этим городом над кнопкой "Мои координаты"
    if previous_city:
        keyboard_buttons = [
            [KeyboardButton(text=f"🏙️ {previous_city}")],
            [KeyboardButton(text="📍 Мои координаты", request_location=True)]
        ]
    else:
        keyboard_buttons = [[KeyboardButton(text="📍 Мои координаты", request_location=True)]]

    await message.answer("🏙️ Где ты живёшь?", reply_markup=ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True))
    await state.set_state(ProfileForm.city)

# Получение координат по названию места
async def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return None

        most_relevant = found_places[0]
        lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
        return lon, lat
    except (requests.exceptions.RequestException, KeyError, TypeError):
        return None

# Получение названия местности по координатам
async def fetch_location_name(apikey, lat, lon):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    try:
        response = requests.get(base_url, params={
            "geocode": f"{lon},{lat}",
            "apikey": apikey,
            "format": "json",
        })
        response.raise_for_status()
        found_places = response.json()['response']['GeoObjectCollection']['featureMember']

        if not found_places:
            return "Неизвестное место"

        most_relevant = found_places[0]
        return most_relevant['GeoObject']['name']
    except (requests.exceptions.RequestException, KeyError, TypeError):
        return "Неизвестное место"

# Обработка локации с Яндекс Локатором
async def get_city_from_yandex_locator():
    api_key = 'YOUR_YANDEX_API_KEY'
    url = "https://locator.api.maps.yandex.ru/v1/locate?apikey=" + api_key
    data = {"ip": [{"address": "auto"}]}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get('position', {}).get('country', 'Неизвестная страна') + ", " + result.get('position', {}).get('city', 'Неизвестный город')
    except (requests.exceptions.RequestException, KeyError, TypeError, requests.exceptions.JSONDecodeError):
        return "Неизвестный город"

@dp.message(lambda message: message.content_type == ContentType.LOCATION)
async def handle_location(message: Message, state: FSMContext):
    api_key = 'YOUR_YANDEX_API_KEY'
    lat, lon = message.location.latitude, message.location.longitude
    location_name = await fetch_location_name(api_key, lat, lon)
    
    # Получаем предыдущие данные пользователя
    user_data = await state.get_data()
    previous_city = user_data.get('city')
    
    # Если пользователь ранее вводил город, показываем кнопку с этим городом
    if previous_city and previous_city == location_name:
        keyboard_buttons = [[KeyboardButton(text=f"🏙️ Показать данные для {location_name}")]]
        await message.answer(f"🏙️ Твоя местность: {location_name}", reply_markup=ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True))
    else:
        await message.answer(f"🏙️ Твоя местность: {location_name}")
    
    # Обновляем данные пользователя
    await state.update_data(city=location_name)
    await state.set_state(ProfileForm.city)

# Обработка ввода города вручную
@dp.message(lambda message: message.text and message.text != "📍 Мои координаты")
async def handle_manual_city_input(message: Message, state: FSMContext):
    user_city = message.text.strip()
    await state.update_data(city=user_city)
    await state.set_state(ProfileForm.city)

# Пример базы известных мест
known_locations = ["Москва", "Санкт-Петербург", "Новосибирск"]

# Description query handler
async def ask_description(message: types.Message, state: FSMContext):
    await message.answer("✍️ Напиши немного о себе или отправь 'Пропустить'.", reply_markup=get_skip_keyboard())
    await state.set_state(ProfileForm.description)

# Photos query handler
async def ask_photos(message: types.Message, state: FSMContext):
    desc = message.text if message.text.lower() != "пропустить" else ""
    await state.update_data(description=desc)
    await message.answer("📷 Отправь фото или напиши 'Пропустить'.", reply_markup=get_skip_keyboard())
    await state.set_state(ProfileForm.photos)

# Collect photos handler
async def collect_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get('photos', [])

    if message.photo:
        photos.append(message.photo[-1].file_id)
        await state.update_data(photos=photos)
    elif message.text.lower() == "пропустить":
        await finish_profile(message, state)
        return
    
    await message.answer("Фото добавлено! Если хочешь добавить еще одно, отправь его, иначе нажми 'Пропустить'.", reply_markup=get_skip_keyboard())
    await state.set_state(ProfileForm.photos)

# Final profile handler
async def finish_profile(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Формируем текст профиля
    profile_text = f"{data.get('name', 'Не указано')}, {data.get('age', 'Не указано')}, {data.get('city', 'Не указано')}"
    
    if data.get("description"):
        profile_text += f" - {data['description']}"
    
    # Если есть фото, добавляем их
    if data.get("photos"):
        media = [InputMediaPhoto(photo, caption=profile_text if i == 0 else None) for i, photo in enumerate(data["photos"])]
        await message.answer_media_group(media)
    else:
        await message.answer(profile_text)
    
    # Очистка состояния
    await state.clear()

# Main function that starts the bot
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
