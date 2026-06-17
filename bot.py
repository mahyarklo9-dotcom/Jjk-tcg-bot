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
    index = int(callback.data.split("_")[-1])

    index += 1
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
    index = int(callback.data.split("_")[-1])

    index -= 1
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
        f"🗑 فروش:\n🎴 {card[1]}\n💰 قیمت را وارد کن:"
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
        f"🎁 انتقال:\n🎴 {card[1]}\n👤 ID را وارد کن:"
    )

    await callback.answer()


# =========================
# FLOW (SELL + TRADE)
# =========================

@dp.message()
async def flow(message: Message):

    uid = message.from_user.id

    # SELL
    if uid in sell_states:

        state = sell_states[uid]

        if state["step"] == "price":

            try:
                price = int(message.text)
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
                state["buyer"] = int(message.text)
            except:
                await message.answer("❌ ID اشتباه")
                return

            state["step"] = "price"
            await message.answer("💰 قیمت؟")
            return

        if state["step"] == "price":

            try:
                price = int(message.text)
            except:
                await message.answer("❌ قیمت نامعتبر")
                return

            buyer = state["buyer"]

            if get_points(buyer) < price:
                del trade_states[uid]
                await message.answer("❌ پول کافی نیست")
                return

            card = get_card_by_name(uid, state["card_name"])

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
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
