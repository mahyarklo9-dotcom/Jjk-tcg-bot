import asyncio
import random
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
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

    uid = message.from_user.id

    points = register_user(uid)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 Shop", callback_data="shop")],
        [InlineKeyboardButton(text="📦 Inventory", callback_data="inv")],
        [InlineKeyboardButton(text="🎰 Chance", callback_data="chans")]
    ])

    await message.answer(
        f"🎴 JJK TCG ONLINE\n\n💰 Points: {points}",
        reply_markup=keyboard
    )
@dp.message(Command("debug"))
async def debug(message: Message):

    uid = message.from_user.id

    points = get_points(uid)

    await message.answer(
        f"User ID: {uid}\n"
        f"Points in DB: {points}"
    )

# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "📖 Commands:\n\n"
        "/start\n"
        "/points\n"
        "/shop (30 coins)\n"
        "/open\n"
        "/inv\n"
        "/sell name price\n"
        "/trade user card price\n"
        "/chans (1 hour cooldown)"
    )


# =========================
# POINTS (SAFE)
# =========================
@dp.message(Command("points"))
async def points(message: Message):

    p = get_points(message.from_user.id)
    await message.answer(f"💰 {p}")


# =========================
# SHOP (FIXED 100% BUG FREE)
# =========================
@dp.message(Command("shop"))
@dp.callback_query(F.data == "shop")
async def shop(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    points = get_points(uid)

    if points is None:
        points = 0

    points = int(points)

    if points < 30:
        await bot.send_message(uid, f"❌ Not enough coins\n💰 You have: {points}")
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await bot.send_message(uid, "📦 Pack opened successfully!")


# =========================
# OPEN CARDS
# =========================
@dp.message(Command("open"))
@dp.callback_query(F.data == "open")
async def open_card(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    card = get_next_unopened(uid)

    if not card:
        await bot.send_message(uid, "📦 No cards")
        return

    cid, _, name, img = card

    try:
        photo = FSInputFile(os.path.join(BASE_PATH, img))
        await bot.send_photo(uid, photo, caption=name)
    except:
        await bot.send_message(uid, name)

    move_card_to_inventory(cid)

    await bot.send_message(uid, f"📦 Left: {unopened_count(uid)}")


# =========================
# INVENTORY
# =========================
@dp.message(Command("inv"))
@dp.callback_query(F.data == "inv")
async def inv(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    cards = get_inventory(uid)

    if not cards:
        await bot.send_message(uid, "📦 Empty")
        return

    text = "🎴 Your Cards:\n\n"

    for i, c in enumerate(cards, 1):
        text += f"{i}. {c[0]}\n"

    await bot.send_message(uid, text)


# =========================
# SELL
# =========================
@dp.message(Command("sell"))
async def sell(message: Message):

    args = message.text.split()

    if len(args) < 3:
        await message.answer("❌ /sell name price")
        return

    name = " ".join(args[1:-1])
    price = int(args[-1])

    sell_card(message.from_user.id, name, price)

    await message.answer("💰 Sold")


# =========================
# TRADE
# =========================
@dp.message(Command("trade"))
async def trade(message: Message):

    args = message.text.split()

    if len(args) < 4:
        await message.answer("❌ /trade user card price")
        return

    target = int(args[1])
    card_name = " ".join(args[2:-1])
    price = int(args[-1])

    seller = message.from_user.id

    card = get_card_by_name(seller, card_name)

    if not card:
        await message.answer("❌ No card")
        return

    card_id = card[0]

    add_points(target, -price)
    add_points(seller, price)

    transfer_card(card_id, seller, target)

    await message.answer("✅ Trade done")


# =========================
# CHANS (FIXED COOLDOWN)
# =========================
@dp.message(Command("chans"))
async def chans(message: Message):

    uid = message.from_user.id
    now = int(time.time())

    last = get_last_chans(uid)

    if now - last < 3600:
        await message.answer("⏳ Wait 1 hour")
        return

    reward = random.randint(100, 300)

    add_points(uid, reward)
    set_last_chans(uid, now)

    await message.answer(f"🎰 +{reward}")


# =========================
# CALLBACKS
# =========================
@dp.callback_query()
async def cb(call):

    if call.data == "shop":
        await shop(call.message)

    elif call.data == "open":
        await open_card(call.message)

    elif call.data == "inv":
        await inv(call.message)


# =========================
# RUN
# =========================
async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
