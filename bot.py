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
    InlineKeyboardButton,
    InputMediaPhoto
)
from aiogram.filters import Command

from db import *
from cards import CARDS, BASE_PATH


TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# STATES
# =========================

sell_states = {}
trade_states = {}
inv_states = {}
inv_index = {}   # ✅ اضافه شد (برای تشخیص کارت فعلی)


# =========================
# INVENTORY (GALLERY)
# =========================

@dp.message(Command("inv"))
async def inventory(message: Message):

    uid = message.from_user.id
    cards = get_inventory(uid)

    if not cards:
        await message.answer("🎒 خالی است")
        return

    inv_states[uid] = cards
    inv_index[uid] = 0   # ✅ کارت فعلی

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
# NAVIGATION
# =========================

@dp.callback_query(F.data.startswith("inv_"))
async def inv_nav(callback: CallbackQuery):

    uid = callback.from_user.id

    if uid not in inv_states:
        await callback.answer("منقضی شد")
        return

    cards = inv_states[uid]

    _, action, index = callback.data.split("_")
    index = int(index)

    if action == "next":
        index += 1
    else:
        index -= 1

    if index < 0:
        index = len(cards) - 1
    if index >= len(cards):
        index = 0

    inv_index[uid] = index   # ✅ ذخیره کارت فعلی

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

    await callback.message.edit_media(
    media=InputMediaPhoto(
        media=image_path,
        caption=f"🎴 {card[1]}\n\n📊 {index+1} / {len(cards)}"
    ),
    reply_markup=keyboard
    )

    await callback.answer()


# =========================
# 🗑 SELL (FIXED VERSION)
# =========================

@dp.callback_query(F.data == "inv_sell")
async def inv_sell(callback: CallbackQuery):

    uid = callback.from_user.id

    cards = inv_states.get(uid)
    if not cards:
        await callback.answer("منقضی شد")
        return

    index = inv_index.get(uid, 0)   # ✅ کارت فعلی گالری
    card = cards[index]

    sell_states[uid] = {
        "step": "price",
        "card_name": card[1]
    }

    await callback.message.answer(
        f"🗑 فروش کارت:\n🎴 {card[1]}\n\n💰 قیمت را وارد کن:"
    )

    await callback.answer()


# =========================
# 🎁 TRADE (FIXED VERSION)
# =========================

@dp.callback_query(F.data == "inv_trade")
async def inv_trade(callback: CallbackQuery):

    uid = callback.from_user.id

    cards = inv_states.get(uid)
    if not cards:
        await callback.answer("منقضی شد")
        return

    index = inv_index.get(uid, 0)   # ✅ کارت فعلی
    card = cards[index]

    trade_states[uid] = {
        "step": "buyer",
        "card_name": card[1]
    }

    await callback.message.answer(
        f"🎁 انتقال کارت:\n🎴 {card[1]}\n\n👤 ID خریدار را وارد کن:"
    )

    await callback.answer()
