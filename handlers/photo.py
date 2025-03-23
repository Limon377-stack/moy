from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from states import Form
from .age_and_city import ask_age
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

# Запрос фото
async def ask_photo(message: types.Message, state: FSMContext):
    await message.answer("Теперь отправь свою фотографию:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.photo)

# Обработка фото и показ анкеты
@router.message(Form.photo, F.content_type == "photo")
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1].file_id
    await state.update_data(photo=photo)
    data = await state.get_data()

    # Загружаем данные из файла
    user_data = await load_profile(message.from_user.id)
    name = data.get('name', user_data.get('name', 'Имя не указано'))
    age = data.get('age', user_data.get('age', 'Возраст не указан'))
    city = data.get('city', user_data.get('city', 'Город не указан'))
    description = data.get('description', user_data.get('description', ''))

    # Формирование текста анкеты
    profile_text = f"{name}, {age}, {city}"
    if description:
        profile_text += f" - {description}"

    # Сообщение перед показом анкеты с кнопкой "Готово"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Готово!")]], resize_keyboard=True
    )

    await message.answer("Вот так будет выглядеть твоя анкета. Готово?", reply_markup=keyboard)

    # Отправляем фото с анкетой
    await message.bot.send_photo(chat_id=message.chat.id, photo=photo, caption=profile_text)

    # Очищаем состояние
    await state.clear()

# Обработчик кнопки "Готово!"
@router.message(F.text == "Готово!")
async def finish_profile(message: types.Message):
    await message.answer("Анкета успешно создана!", reply_markup=ReplyKeyboardRemove())
