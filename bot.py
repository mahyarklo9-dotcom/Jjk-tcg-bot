import asyncio
import random
import os
import time

from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from db import *

from cards import CARDS, BASE_PATH


TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):

    user_id = message.from_user.id
    points = register_user(user_id)

    if points is None:
        points = get_points(user_id)

    await message.answer(
        f"🎴 TCG JJK Bot\n\n"
        f"💰 امتیاز: {points}\n"
        f"📖 /help"
    )


# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "📖 دستورات:\n\n"
        "/points\n"
        "/TCG_shop\n"
        "/TCG_Open\n"
        "/TCG_inv\n"
        "/sell\n"
        "/trade\n"
        "/chans"
    )


# =========================
# POINTS
# =========================
@dp.message(Command("points"))
async def points(message: Message):

    await message.answer(f"💰 {get_points(message.from_user.id)}")


# =========================
# SHOP
# =========================
@dp.message(Command("TCG_shop"))
async def shop(message: Message):

    uid = message.from_user.id
    if get_points(uid) < 30:
        await message.answer("❌ امتیاز کافی نیست")
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await message.answer("📦 پک خریدی!")


# =========================
# OPEN
# =========================
@dp.message(Command("TCG_Open"))
async def open_card(message: Message):

    card = get_next_unopened(message.from_user.id)

    if not card:
        await message.answer("📦 چیزی نداری")
        return

    cid, _, name, img = card

    try:
        photo = FSInputFile(os.path.join(BASE_PATH, img))
        await message.answer_photo(photo, caption=name)
    except:
        await message.answer(name)

    move_card_to_inventory(cid)

    await message.answer(f"📦 باقی: {unopened_count(message.from_user.id)}")


# =========================
# INVENTORY
# =========================
@dp.message(Command("TCG_inv"))
async def inv(message: Message):

    cards = get_inventory(message.from_user.id)

    if not cards:
        await message.answer("خالیه")
        return

    text = "🎴:\n"
    for i, c in enumerate(cards, 1):
        text += f"{i}. {c[0]}\n"

    await message.answer(text)


# =========================
# SELL
# =========================
@dp.message(Command("sell"))
async def sell(message: Message):

    args = message.text.split()
    if len(args) < 3:
        await message.answer("/sell name price")
        return

    name = " ".join(args[1:-1])
    price = int(args[-1])

    sell_card(message.from_user.id, name, price)

    await message.answer("💰 فروخته شد")


# =========================
# TRADE
# =========================
@dp.message(Command("trade"))
async def trade(message: Message):

    args = message.text.split()

    if len(args) < 4:
        await message.answer("/trade user_id card price")
        return

    target = int(args[1])
    card_name = " ".join(args[2:-1])
    price = int(args[-1])

    seller = message.from_user.id

    card = get_card_by_name(seller, card_name)

    if not card:
        await message.answer("❌ کارت نداری")
        return

    card_id = card[0]

    add_points(target, -price)
    add_points(seller, price)

    transfer_card(card_id, seller, target)

    await message.answer("✅ معامله شد")


# =========================
# CHANS
# =========================
@dp.message(Command("chans"))
async def chans(message: Message):

    uid = message.from_user.id
    now = int(time.time())

    last = get_last_chans(uid)

    if now - last < 3600:
        await message.answer("⏳ هر 1 ساعت یکبار")
        return

    reward = random.randint(100, 300)

    add_points(uid, reward)
    set_last_chans(uid, now)

    await message.answer(f"🎉 +{reward}")


# =========================
# MAIN
# =========================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
