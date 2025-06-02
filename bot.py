import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from config import TOKEN_BOT


logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN_BOT)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class Registration(StatesGroup):
    name = State()
    age = State()
    grade = State()

def create_database():
    connection = sqlite3.connect('school_data.db')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        grade TEXT NOT NULL
    )
    ''')
    connection.commit()
    connection.close()

def save_to_database(name, age, grade):
    connection = sqlite3.connect('school_data.db')
    cursor = connection.cursor()
    cursor.execute('''
    INSERT INTO students (name, age, grade) VALUES (?, ?, ?)
    ''', (name, age, grade))
    connection.commit()
    connection.close()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Давай зарегистрируем тебя в системе. Как тебя зовут?")
    await state.set_state(Registration.name)

@dp.message(Registration.name)
async def process_name(message: Message, state: FSMContext):
    logging.info(f"Получено имя: {message.text}")
    await state.update_data(name=message.text)
    await message.answer("Отлично! Теперь напиши свой возраст, указав цифры:")
    await state.set_state(Registration.age)

@dp.message(Registration.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи возраст числом.")
        return
    logging.info(f"Получен возраст: {message.text}")
    await state.update_data(age=int(message.text))
    await message.answer("Теперь напиши свой класс (например: 10A):")
    await state.set_state(Registration.grade)  # Переходим к следующему состоянию

@dp.message(Registration.grade)
async def process_grade(message: Message, state: FSMContext):
    logging.info(f"Получен класс: {message.text}")
    await state.update_data(grade=message.text)
    data = await state.get_data()

    name = data['name']
    age = data['age']
    grade = data['grade']

    save_to_database(name, age, grade)

    await message.answer(f"Спасибо! Ты был успешно зарегистрирован.\n"
                         f"Имя: {name}\nВозраст: {age}\nКласс: {grade}")
    logging.info(f"Данные сохранены в базу: Имя={name}, Возраст={age}, Класс={grade}")

    await state.clear()


async def main():
    create_database()
    logging.info("База данных создана, бот запускается...")
    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())