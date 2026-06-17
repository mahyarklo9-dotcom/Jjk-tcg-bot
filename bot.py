import asyncio
import random
import os

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

from cards import CARDS, BASE_PATH


# =========================
# TOKEN (Railway)
# =========================
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
        points = get_points(user_id)
        await message.answer(
            "👋 خوش برگشتی به TCG جوجوتسو\n\n"
            f"💰 امتیاز فعلی: {points}\n\n"
            "📖 برای راهنما /help"
        )
    else:
        await message.answer(
            "🎉 خوش آمدی!\n\n"
            f"🎁 امتیاز اولیه: {points}\n\n"
            "📖 برای شروع /help"
        )


# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "📖 راهنمای ربات TCG\n\n"
        "/start - شروع بازی\n"
        "/points - نمایش امتیاز\n"
        "/TCG_shop - خرید پک (30 امتیاز)\n"
        "/TCG_Open - باز کردن کارت‌ها\n"
        "/TCG_inv - مشاهده کارت‌ها\n"
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
async def shop_cmd(message: Message):

    user_id = message.from_user.id
    points = get_points(user_id)

    if points < 30:
        await message.answer("❌ امتیاز کافی نیست (حداقل 30)")
        return

    remove_points(user_id, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(user_id, name, img)

    await message.answer(
        "📦 پک خریداری شد!\n\n"
        "🎴 برای باز کردن: /TCG_Open"
    )


# =========================
# OPEN CARD
# =========================
@dp.message(Command("TCG_Open"))
async def open_cmd(message: Message):

    user_id = message.from_user.id

    card = get_next_unopened(user_id)

    if not card:
        await message.answer("📦 کارت باز نشده نداری")
        return

    card_id, _, name, img = card

    try:
        photo = FSInputFile(os.path.join(BASE_PATH, img))

        await message.answer_photo(
            photo,
            caption=f"🎴 {name}"
        )
    except:
        await message.answer(f"🎴 {name}")

    move_card_to_inventory(card_id)

    await message.answer(
        f"📦 باقی مانده: {unopened_count(user_id)}"
    )


# =========================
# INVENTORY
# =========================
@dp.message(Command("TCG_inv"))
async def inv_cmd(message: Message):

    cards = get_inventory(message.from_user.id)

    if not cards:
        await message.answer("📦 اینونتوری خالیه")
        return

    text = "🎴 کارت‌های شما:\n\n"

    for i, c in enumerate(cards, 1):
        text += f"{i}. {c[0]}\n"

    await message.answer(text)


# =========================
# MAIN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
