import asyncio
import random
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    FSInputFile,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command

from db import *
from cards import CARDS, BASE_PATH


TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("TOKEN is not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# STATES
# =========================

sell_states = {}
trade_states = {}
inv_states = {}
inv_index = {}


# =========================
# START
# =========================

@dp.message(Command("start"))
async def start(message: Message):
    uid = message.from_user.id
    points = register_user(uid)

    await message.answer(
        f"🎴 خوش آمدی\n💰 امتیاز: {points}\n/help"
    )


# =========================
# HELP
# =========================

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("""
📌 دستورات:

/profile
/inv
/shop
/open
/sell
/trade
/luck
/help_trade
""")


# =========================
# PROFILE
# =========================

@dp.message(Command("profile"))
async def profile(message: Message):

    uid = message.from_user.id
    register_user(uid)

    await message.answer(
        f"""
👤 پروفایل

🆔 {uid}
💰 امتیاز: {get_points(uid)}
🎒 کارت‌ها: {len(get_inventory(uid))}
📦 بازنشده: {unopened_count(uid)}
"""
    )


# =========================
# SHOP
# =========================

@dp.message(Command("shop"))
async def shop(message: Message):

    uid = message.from_user.id
    register_user(uid)

    if get_points(uid) < 30:
        await message.answer("❌ امتیاز کافی نیست (30 لازم است)")
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, min(8, len(CARDS)))

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await message.answer("✅ پک خریداری شد\n/open")


# =========================
# OPEN
# =========================

@dp.message(Command("open"))
async def open_card(message: Message):

    uid = message.from_user.id

    card = get_next_unopened(uid)

    if not card:
        await message.answer("📦 کارتی برای باز کردن نداری")
        return

    card_id, _, name, img = card

    path = os.path.join(BASE_PATH, img)

    try:
        await message.answer_photo(FSInputFile(path), caption=f"🎴 {name}")
    except:
        await message.answer(f"🎴 {name}")

    move_card_to_inventory(card_id)


# =========================
# INVENTORY (GALLERY)
# =========================

@dp.message(Command("inv"))
async def inv(message: Message):

    uid = message.from_user.id
    cards = get_inventory(uid)

    if not cards:
        await message.answer("🎒 خالی است")
        return

    inv_states[uid] = cards
    inv_index[uid] = 0

    card = cards[0]
    path = os.path.join(BASE_PATH, card[2])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="prev_0"),
                InlineKeyboardButton(text="➡️", callback_data="next_0")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="trade")
            ]
        ]
    )

    await message.answer_photo(
        FSInputFile(path),
        caption=f"🎴 {card[1]}\n1 / {len(cards)}",
        reply_markup=kb
    )


# =========================
# NAVIGATION NEXT
# =========================

@dp.callback_query(F.data.startswith("next_"))
async def next_card(cb: CallbackQuery):

    uid = cb.from_user.id
    cards = inv_states.get(uid)

    if not cards:
        await cb.answer()
        return

    index = inv_index[uid] + 1
    if index >= len(cards):
        index = 0

    inv_index[uid] = index
    card = cards[index]

    path = os.path.join(BASE_PATH, card[2])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"prev_{index}"),
                InlineKeyboardButton(text="➡️", callback_data=f"next_{index}")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="trade")
            ]
        ]
    )

    await cb.message.delete()
    await cb.message.answer_photo(
        FSInputFile(path),
        caption=f"🎴 {card[1]}\n{index+1} / {len(cards)}",
        reply_markup=kb
    )

    await cb.answer()


# =========================
# NAVIGATION PREV
# =========================

@dp.callback_query(F.data.startswith("prev_"))
async def prev_card(cb: CallbackQuery):

    uid = cb.from_user.id
    cards = inv_states.get(uid)

    if not cards:
        await cb.answer()
        return

    index = inv_index[uid] - 1
    if index < 0:
        index = len(cards) - 1

    inv_index[uid] = index
    card = cards[index]

    path = os.path.join(BASE_PATH, card[2])

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"prev_{index}"),
                InlineKeyboardButton(text="➡️", callback_data=f"next_{index}")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="trade")
            ]
        ]
    )

    await cb.message.delete()
    await cb.message.answer_photo(
        FSInputFile(path),
        caption=f"🎴 {card[1]}\n{index+1} / {len(cards)}",
        reply_markup=kb
    )

    await cb.answer()


# =========================
# SELL
# =========================

@dp.callback_query(F.data == "sell")
async def sell(cb: CallbackQuery):

    uid = cb.from_user.id
    cards = inv_states.get(uid)

    if not cards:
        return

    index = inv_index.get(uid, 0)
    card = cards[index]

    sell_states[uid] = {"step": "price", "card_name": card[1]}

    await cb.message.answer("💰 قیمت فروش؟")
    await cb.answer()


# =========================
# TRADE
# =========================

@dp.callback_query(F.data == "trade")
async def trade(cb: CallbackQuery):

    uid = cb.from_user.id
    cards = inv_states.get(uid)

    if not cards:
        return

    index = inv_index.get(uid, 0)
    card = cards[index]

    trade_states[uid] = {"step": "buyer", "card_name": card[1]}

    await cb.message.answer("👤 ID خریدار؟")
    await cb.answer()


# =========================
# LUCK (NEW)
# =========================

@dp.message(Command("luck"))
async def luck(message: Message):

    uid = message.from_user.id
    register_user(uid)

    now = int(time.time())
    last = get_last_luck(uid)

    if now - last < 3600:
        remain = 3600 - (now - last)
        await message.answer(f"⏳ صبر کن {remain//60} دقیقه")
        return

    reward = random.randint(100, 200)

    add_points(uid, reward)
    set_last_luck(uid, now)

    await message.answer(
        f"""
🍀 شانس!

🎁 +{reward}
💰 {get_points(uid)}
"""
    )


# =========================
# MESSAGE FLOW
# =========================

@dp.message()
async def handler(message: Message):

    uid = message.from_user.id
    text = message.text or ""

    if text.startswith("/"):
        return

    # SELL
    if uid in sell_states:

        if sell_states[uid]["step"] == "price":
            try:
                price = int(text)
            except:
                await message.answer("❌ عدد")
                return

            sell_card(uid, sell_states[uid]["card_name"], price)
            del sell_states[uid]

            await message.answer("✅ فروخته شد")
            return

    # TRADE
    if uid in trade_states:

        st = trade_states[uid]

        if st["step"] == "buyer":
            st["buyer"] = int(text)
            st["step"] = "card"
            await message.answer("🎴 نام کارت")
            return

        if st["step"] == "card":
            st["card_name"] = text
            st["step"] = "price"
            await message.answer("💰 قیمت")
            return

        if st["step"] == "price":

            price = int(text)
            buyer = st["buyer"]

            if get_points(buyer) < price:
                del trade_states[uid]
                await message.answer("❌ پول کم")
                return

            card = get_card_by_name(uid, st["card_name"])

            if not card:
                del trade_states[uid]
                await message.answer("❌ کارت نیست")
                return

            remove_points(buyer, price)
            add_points(uid, price)
            transfer_card(card[0], uid, buyer)

            del trade_states[uid]

            await message.answer("✅ معامله انجام شد")
            return


# =========================
# RUN
# =========================

async def main():
    init_db()
    print("BOT RUNNING")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
