import asyncio
import re

from database import (
    init_db,
    add_order,
    update_status,
    update_taken_by,
    get_order
)

from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from config import TOKEN, ADMIN_CHAT_ID


# =====================
# BOT INIT
# =====================
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()


# =====================
# STATUSES
# =====================
STATUS_NEW = "new"
STATUS_WORK = "work"
STATUS_DONE = "done"


# =====================
# HELPERS
# =====================
def format_order_id(order_id: int) -> str:
    return f"#{order_id:04d}"


# =====================
# KEYBOARDS
# =====================
def kb_new(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟡 В роботу", callback_data=f"work:{order_id}")]
    ])


def kb_work(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Виконано", callback_data=f"done:{order_id}")]
    ])


def kb_done():
    return None


# =====================
# CRM RENDER
# =====================
def render_order(order_id, data):
    status_map = {
        "new": "🆕 Нова заявка",
        "work": f"🟡 В роботі ({data.get('taken_by', '—')})",
        "done": "✅ Виконано"
    }

    status = status_map.get(data.get("status", "new"))

    return (
        f"📥 БРОНЬ {format_order_id(order_id)}\n\n"
        f"👤 Ім’я: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📅 Дата: {data['event_date']}\n\n"
        f"{status}"
    )


# =====================
# FSM
# =====================
class Form(StatesGroup):
    name = State()
    phone = State()
    date = State()


# =====================
# START
# =====================
@router.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await message.answer("👋 Вітаю, як до вас можна звертатись?")
    await state.set_state(Form.name)


# =====================
# NAME
# =====================
@router.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📞 Вкажіть ваш номер телефону у форматі (+380XXXXXXXXX):")
    await state.set_state(Form.phone)


# =====================
# PHONE
# =====================
@router.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()

    if not re.match(r"^\+380\d{9}$", phone):
        await message.answer("❌ Невірний формат. Приклад: +380671234567")
        return

    await state.update_data(phone=phone)
    await message.answer("📅 Яка дата вашої події?")
    await state.set_state(Form.date)


# =====================
# FINAL
# =====================
@router.message(Form.date)
async def get_date(message: types.Message, state: FSMContext):
    data = await state.get_data()

    data["event_date"] = message.text

    order_id = await add_order(
        data["name"],
        data["phone"],
        data["event_date"]
    )

    data["status"] = STATUS_NEW
    data["taken_by"] = None

    sent_msg = await message.bot.send_message(
        ADMIN_CHAT_ID,
        render_order(order_id, data),
        reply_markup=kb_new(order_id)
    )

    data["msg_id"] = sent_msg.message_id

    await state.clear()

    await message.answer(
        "✅ Дякуємо! Ми зв’яжемося з вами протягом 24 годин для уточнення деталей.",
        reply_markup=ReplyKeyboardRemove()
    )


# =====================
# WORK CALLBACK
# =====================
@router.callback_query(F.data.startswith("work:"))
async def work(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    admin_name = callback.from_user.full_name

    await update_status(order_id, STATUS_WORK)
    await update_taken_by(order_id, admin_name)

    order = await get_order(order_id)

    data = {
        "name": order[1],
        "phone": order[2],
        "event_date": order[3],
        "status": STATUS_WORK,
        "taken_by": order[5]
    }

    await callback.message.edit_text(
        render_order(order_id, data),
        reply_markup=kb_work(order_id)
    )

    await callback.answer("В роботі 🟡")


# =====================
# DONE CALLBACK
# =====================
@router.callback_query(F.data.startswith("done:"))
async def done(callback: types.CallbackQuery):
    order_id = int(callback.data.split(":")[1])

    # обновляем статус
    await update_status(order_id, STATUS_DONE)

    order = await get_order(order_id)

    data = {
        "name": order[1],
        "phone": order[2],
        "event_date": order[3],
        "status": STATUS_DONE,
        "taken_by": order[5]   # 
    }

    text = (
        f"📥 БРОНЬ #{order_id:04d}\n\n"
        f"👤 Ім’я: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"📅 Дата: {data['event_date']}\n\n"
        f"✅ Виконано\n"
        f"👨‍💼 Виконав: {data.get('taken_by', '—')}"
    )

    await callback.message.edit_text(text, reply_markup=None)
    await callback.answer("Виконано ✅")


# =====================
# MAIN
# =====================
async def main():
    await init_db()

    dp.include_router(router)

    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())