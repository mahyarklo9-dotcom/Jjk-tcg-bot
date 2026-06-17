import asyncio
import random

from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from db import (
    register_user,
    get_points,
    remove_points,
    add_unopened_card,
    get_next_unopened,
    move_card_to_inventory,
    get_inventory,
    unopened_count
)

from cards import CARDS
import os

TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start_cmd(message: Message):

    user_id = message.from_user.id

    points = register_user(user_id)

    if points is None:

        current_points = get_points(user_id)

        await message.answer(
            f"👋 خوش برگشتی\n\n"
            f"💰 امتیاز فعلی: {current_points}"
        )

    else:

        await message.answer(
            f"🎉 به ربات TCG جوجوتسو خوش آمدی\n\n"
            f"🎁 امتیاز اولیه: {points}"
        )


# =========================
# POINTS
# =========================

@dp.message(Command("points"))
async def points_cmd(message: Message):

    points = get_points(message.from_user.id)

    await message.answer(
        f"💰 امتیاز شما: {points}"
    )


# =========================
# SHOP
# =========================

@dp.message(Command("TCG_shop"))
async def tcg_shop(message: Message):

    user_id = message.from_user.id

    points = get_points(user_id)

    if points < 30:

        await message.answer(
            "❌ امتیاز کافی نداری.\n"
            "برای خرید پک به 30 امتیاز نیاز داری."
        )
        return

    remove_points(user_id, 30)

    pack = random.sample(CARDS, 8)

    for card_name, image_file in pack:

        add_unopened_card(
            user_id,
            card_name,
            image_file
        )

    await message.answer(
        "📦 پک خریداری شد.\n\n"
        "برای باز کردن کارت ها:\n"
        "/TCG_Open"
    )


# =========================
# OPEN
# =========================

@dp.message(Command("TCG_Open"))
async def tcg_open(message: Message):

    user_id = message.from_user.id

    card = get_next_unopened(user_id)

    if not card:

        await message.answer(
            "📦 هیچ کارت باز نشده ای نداری."
        )
        return

    card_id = card[0]
    card_name = card[2]
    image_file = card[3]

    try:

        photo = FSInputFile(image_file)

        await message.answer_photo(
            photo,
            caption=f"🎴 {card_name}"
        )

    except Exception:

        await message.answer(
            f"🎴 {card_name}\n\n"
            f"⚠️ عکس کارت پیدا نشد."
        )

    move_card_to_inventory(card_id)

    remain = unopened_count(user_id)

    await message.answer(
        f"📦 کارت های باقی مانده در پک: {remain}"
    )


# =========================
# INVENTORY
# =========================

@dp.message(Command("TCG_inv"))
async def tcg_inv(message: Message):

    cards = get_inventory(
        message.from_user.id
    )

    if not cards:

        await message.answer(
            "🎴 اینونتوری شما خالی است."
        )
        return

    text = "🎴 Collection\n\n"

    for i, card in enumerate(cards, start=1):

        text += f"{i}. {card[0]}\n"

    await message.answer(text)


# =========================
# HELP
# =========================

@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "/start - شروع بازی\n"
        "/points - مشاهده امتیاز\n"
        "/TCG_shop - خرید پک\n"
        "/TCG_Open - باز کردن کارت\n"
        "/TCG_inv - مشاهده کالکشن"
    )


# =========================
# MAIN
# =========================

async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())