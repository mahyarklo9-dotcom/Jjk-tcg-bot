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
# SAFE POINTS (FIX BUG)
# =========================
def safe_points(user_id):
    p = get_points(user_id)
    if p is None:
        return 0
    return int(p)


# =========================
# START
# =========================
@dp.message(Command("start"))
async def start(message: Message):

    uid = message.from_user.id
    points = register_user(uid)

    if points is None:
        points = safe_points(uid)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎴 خرید پک", callback_data="shop")],
        [InlineKeyboardButton(text="📦 کارت‌ها", callback_data="inv")],
        [InlineKeyboardButton(text="🎰 شانس", callback_data="chans")]
    ])

    await message.answer(
        f"🎴 JJK TCG\n\n💰 امتیاز: {points}",
        reply_markup=keyboard
    )


# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        "📖 دستورات:\n"
        "/start\n/points\n/shop\n/open\n/inv\n/sell\n/trade\n/chans"
    )


# =========================
# POINTS
# =========================
@dp.message(Command("points"))
async def points(message: Message):

    await message.answer(f"💰 {safe_points(message.from_user.id)}")


# =========================
# SHOP (FIXED CONDITION)
# =========================
@dp.message(Command("shop"))
@dp.callback_query(F.data == "shop")
async def shop(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    points = safe_points(uid)

    # ✅ FIX: درست بررسی امتیاز
    if points < 30:
        await bot.send_message(uid, f"❌ امتیاز کافی نیست\n💰 داری: {points}")
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await bot.send_message(uid, "📦 پک خریداری شد!")


# =========================
# OPEN CARD
# =========================
@dp.message(Command("open"))
@dp.callback_query(F.data == "open")
async def open_card(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    card = get_next_unopened(uid)

    if not card:
        await bot.send_message(uid, "📦 کارت نداری")
        return

    cid, _, name, img = card

    try:
        photo = FSInputFile(os.path.join(BASE_PATH, img))
        await bot.send_photo(uid, photo, caption=f"🎴 {name}")
    except:
        await bot.send_message(uid, f"🎴 {name}")

    move_card_to_inventory(cid)

    await bot.send_message(uid, f"📦 باقی: {unopened_count(uid)}")


# =========================
# INVENTORY
# =========================
@dp.message(Command("inv"))
@dp.callback_query(F.data == "inv")
async def inv(event):

    uid = event.from_user.id if isinstance(event, Message) else event.message.chat.id

    cards = get_inventory(uid)

    if not cards:
        await bot.send_message(uid, "📦 خالیه")
        return

    text = "🎴 کارت‌ها:\n\n"

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

    await message.answer(f"💰 فروخته شد")


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
        await message.answer("⏳ هنوز باید صبر کنی")
        return

    reward = random.randint(100, 300)

    add_points(uid, reward)
    set_last_chans(uid, now)

    await message.answer(f"🎰 +{reward} امتیاز")


# =========================
# CALLBACK FIX
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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
