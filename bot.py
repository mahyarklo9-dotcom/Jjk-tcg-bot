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


# =========================
# TOKEN
# =========================

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
        f"""
🎴 JJK TCG ONLINE

👤 خوش آمدی

💰 امتیاز: {points}

/help
"""
    )


# =========================
# HELP
# =========================

@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        """
📌 دستورات اصلی:

/profile - پروفایل
/inv - گالری کارت‌ها
/shop - خرید پک
/open - باز کردن کارت
/sell - فروش کارت
/trade - انتقال کارت
/help_trade - راهنمای معامله
"""
    )


# =========================
# PROFILE
# =========================

@dp.message(Command("profile"))
async def profile(message: Message):

    uid = message.from_user.id
    register_user(uid)

    cards = get_inventory(uid)
    unopened = unopened_count(uid)

    await message.answer(
        f"""
👤 پروفایل

🆔 ID: {uid}

💰 امتیاز: {get_points(uid)}

🎒 کارت‌ها: {len(cards)}

📦 کارت‌های بازنشده: {unopened}
"""
    )


# =========================
# HELP TRADE
# =========================

@dp.message(Command("help_trade"))
async def help_trade(message: Message):

    await message.answer(
        """
🤝 نحوه معامله:

1️⃣ /trade
2️⃣ ID خریدار
3️⃣ نام کارت
4️⃣ قیمت
"""
    )


# =========================
# INVENTORY (GALLERY)
# =========================

@dp.message(Command("inv"))
async def inventory(message: Message):

    uid = message.from_user.id
    cards = get_inventory(uid)

    if not cards:
        await message.answer("🎒 اینونتوری خالی است")
        return

    inv_states[uid] = cards
    inv_index[uid] = 0

    card = cards[0]
    image_path = os.path.join(BASE_PATH, card[2])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data="inv_prev_0"),
                InlineKeyboardButton(text="➡️", callback_data="inv_next_0")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="inv_sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="inv_trade")
            ]
        ]
    )

    await message.answer_photo(
        FSInputFile(image_path),
        caption=f"🎴 {card[1]}\n\n📊 1 / {len(cards)}",
        reply_markup=keyboard
    )


# =========================
# NEXT
# =========================

@dp.callback_query(F.data.startswith("inv_next_"))
async def inv_next(callback: CallbackQuery):

    uid = callback.from_user.id

    if uid not in inv_states:
        await callback.answer("منقضی شد")
        return

    cards = inv_states[uid]
    index = int(callback.data.split("_")[-1]) + 1

    if index >= len(cards):
        index = 0

    inv_index[uid] = index
    card = cards[index]

    image_path = os.path.join(BASE_PATH, card[2])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"inv_prev_{index}"),
                InlineKeyboardButton(text="➡️", callback_data=f"inv_next_{index}")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="inv_sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="inv_trade")
            ]
        ]
    )

    await callback.message.delete()

    await callback.message.answer_photo(
        FSInputFile(image_path),
        caption=f"🎴 {card[1]}\n\n📊 {index+1} / {len(cards)}",
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# PREV
# =========================

@dp.callback_query(F.data.startswith("inv_prev_"))
async def inv_prev(callback: CallbackQuery):

    uid = callback.from_user.id

    if uid not in inv_states:
        await callback.answer("منقضی شد")
        return

    cards = inv_states[uid]
    index = int(callback.data.split("_")[-1]) - 1

    if index < 0:
        index = len(cards) - 1

    inv_index[uid] = index
    card = cards[index]

    image_path = os.path.join(BASE_PATH, card[2])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️", callback_data=f"inv_prev_{index}"),
                InlineKeyboardButton(text="➡️", callback_data=f"inv_next_{index}")
            ],
            [
                InlineKeyboardButton(text="🗑 فروش", callback_data="inv_sell"),
                InlineKeyboardButton(text="🎁 انتقال", callback_data="inv_trade")
            ]
        ]
    )

    await callback.message.delete()

    await callback.message.answer_photo(
        FSInputFile(image_path),
        caption=f"🎴 {card[1]}\n\n📊 {index+1} / {len(cards)}",
        reply_markup=keyboard
    )

    await callback.answer()


# =========================
# SELL
# =========================

@dp.callback_query(F.data == "inv_sell")
async def inv_sell(callback: CallbackQuery):

    uid = callback.from_user.id

    cards = inv_states.get(uid)
    if not cards:
        await callback.answer("منقضی شد")
        return

    index = inv_index.get(uid, 0)
    card = cards[index]

    sell_states[uid] = {
        "step": "price",
        "card_name": card[1]
    }

    await callback.message.answer(
        f"🗑 فروش کارت:\n🎴 {card[1]}\n💰 قیمت را وارد کن:"
    )

    await callback.answer()


# =========================
# TRADE
# =========================

@dp.callback_query(F.data == "inv_trade")
async def inv_trade(callback: CallbackQuery):

    uid = callback.from_user.id

    cards = inv_states.get(uid)
    if not cards:
        await callback.answer("منقضی شد")
        return

    index = inv_index.get(uid, 0)
    card = cards[index]

    trade_states[uid] = {
        "step": "buyer",
        "card_name": card[1]
    }

    await callback.message.answer(
        f"🎁 انتقال کارت:\n🎴 {card[1]}\n👤 ID خریدار را وارد کن:"
    )

    await callback.answer()


# =========================
# MESSAGE FLOW (SAFE)
# =========================

@dp.message()
async def handle_all(message: Message):

    uid = message.from_user.id
    text = message.text or ""

    if text.startswith("/"):
        return

    # SELL
    if uid in sell_states:

        state = sell_states[uid]

        if state["step"] == "price":

            try:
                price = int(text)
            except:
                await message.answer("❌ فقط عدد")
                return

            sell_card(uid, state["card_name"], price)
            del sell_states[uid]

            await message.answer("✅ فروخته شد")
            return

    # TRADE
    if uid in trade_states:

        state = trade_states[uid]

        if state["step"] == "buyer":

            try:
                state["buyer"] = int(text)
            except:
                await message.answer("❌ ID اشتباه")
                return

            state["step"] = "card"
            await message.answer("🎴 نام کارت را وارد کن:")
            return

        if state["step"] == "card":

            state["card_name"] = text
            state["step"] = "price"

            await message.answer("💰 قیمت؟")
            return

        if state["step"] == "price":

            try:
                price = int(text)
            except:
                await message.answer("❌ قیمت اشتباه")
                return

            buyer = state["buyer"]

            if get_points(buyer) < price:
                del trade_states[uid]
                await message.answer("❌ پول کافی نیست")
                return

            card = get_card_by_name(uid, state["card_name"])

            if not card:
                del trade_states[uid]
                await message.answer("❌ کارت پیدا نشد")
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
    print("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
