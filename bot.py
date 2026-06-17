import asyncio
import random
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
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

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎴 خرید پک",
                    callback_data="shop"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📦 باز کردن کارت",
                    callback_data="open"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎒 اینونتوری",
                    callback_data="inv"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎰 شانس",
                    callback_data="chans"
                )
            ]
        ]
    )

    await message.answer(
        f"""
🎴 JJK TCG ONLINE

👋 خوش آمدی

💰 امتیاز فعلی: {points}

برای شروع از دکمه‌ها یا دستورات استفاده کن.
""",
        reply_markup=keyboard
    )


# =========================
# HELP
# =========================
@dp.message(Command("help"))
async def help_cmd(message: Message):

    await message.answer(
        """
📖 راهنمای دستورات

/start
شروع ربات

/help
نمایش راهنما

/points
نمایش امتیاز

/shop
خرید یک پک (30 امتیاز)

/open
باز کردن یک کارت

/inv
نمایش کارت‌ها

/chans
دریافت جایزه تصادفی هر 1 ساعت

/sell نام_کارت قیمت
فروش کارت

/trade user_id نام_کارت قیمت
انتقال کارت به کاربر دیگر

/debug
بررسی امتیاز داخل دیتابیس

/testpoints
افزودن 100 امتیاز تستی
"""
    )


# =========================
# POINTS
# =========================
@dp.message(Command("points"))
async def points(message: Message):

    uid = message.from_user.id

    register_user(uid)

    p = get_points(uid)

    await message.answer(
        f"💰 امتیاز فعلی شما: {p}"
    )


# =========================
# DEBUG
# =========================
@dp.message(Command("debug"))
async def debug(message: Message):

    uid = message.from_user.id

    await message.answer(
        f"""
🛠 اطلاعات کاربر

ID: {uid}

Points: {get_points(uid)}
"""
    )


# =========================
# TEST POINTS
# =========================
@dp.message(Command("testpoints"))
async def testpoints(message: Message):

    uid = message.from_user.id

    add_points(uid, 100)

    await message.answer(
        f"""
✅ 100 امتیاز اضافه شد

💰 موجودی جدید:
{get_points(uid)}
"""
    )


# =========================
# DB PATH
# =========================
@dp.message(Command("dbpath"))
async def dbpath(message: Message):

    await message.answer(
        os.path.abspath("tcg.db")
    )
    # =========================
# SHOP
# =========================
@dp.message(Command("shop"))
async def shop(message: Message):

    uid = message.from_user.id

    register_user(uid)

    points = get_points(uid)

    if points < 30:
        await message.answer(
            f"""
❌ امتیاز کافی نیست

💰 موجودی شما: {points}
🎴 قیمت هر پک: 30
"""
        )
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await message.answer(
        f"""
📦 پک با موفقیت خریداری شد

🎴 تعداد کارت داخل پک: 8

💰 موجودی جدید:
{get_points(uid)}

برای باز کردن کارت‌ها:
/open
"""
    )


# =========================
# OPEN CARD
# =========================
@dp.message(Command("open"))
async def open_card(message: Message):

    uid = message.from_user.id

    card = get_next_unopened(uid)

    if not card:
        await message.answer(
            """
📦 هیچ کارت بازنشده‌ای نداری

ابتدا یک پک بخر:
/shop
"""
        )
        return

    card_id, _, card_name, image_file = card

    try:

        image_path = os.path.join(
            BASE_PATH,
            image_file
        )

        photo = FSInputFile(image_path)

        await message.answer_photo(
            photo,
            caption=f"🎴 {card_name}"
        )

    except Exception:

        await message.answer(
            f"""
🎴 کارت دریافت شد

{card_name}
"""
        )

    move_card_to_inventory(card_id)

    left = unopened_count(uid)

    await message.answer(
        f"""
✅ کارت به اینونتوری منتقل شد

📦 کارت بازنشده باقی‌مانده:
{left}
"""
    )


# =========================
# INVENTORY
# =========================
@dp.message(Command("inv"))
async def inv(message: Message):

    uid = message.from_user.id

    cards = get_inventory(uid)

    if not cards:

        await message.answer(
            """
🎒 اینونتوری خالی است

برای دریافت کارت:
/shop
"""
        )
        return

    text = (
        f"🎒 اینونتوری شما\n\n"
        f"📊 تعداد کارت‌ها: {len(cards)}\n\n"
    )

    for index, card in enumerate(cards, start=1):

        card_name = card[1]

        text += f"{index}. {card_name}\n"

    await message.answer(text)
    # =========================
# SELL CARD
# =========================
@dp.message(Command("sell"))
async def sell(message: Message):

    args = message.text.split()

    if len(args) < 3:
        await message.answer(
            """
❌ استفاده صحیح:

/sell نام_کارت قیمت

مثال:
/sell JJK Card 5 100
"""
        )
        return

    try:
        price = int(args[-1])
    except:
        await message.answer("❌ قیمت نامعتبر است")
        return

    card_name = " ".join(args[1:-1])

    result = sell_card(
        message.from_user.id,
        card_name,
        price
    )

    if not result:
        await message.answer(
            "❌ این کارت در اینونتوری شما وجود ندارد"
        )
        return

    await message.answer(
        f"""
💰 کارت فروخته شد

🎴 کارت:
{card_name}

💵 مبلغ:
{price}

💰 موجودی جدید:
{get_points(message.from_user.id)}
"""
    )


# =========================
# TRADE CARD
# =========================
@dp.message(Command("trade"))
async def trade(message: Message):

    args = message.text.split()

    if len(args) < 4:
        await message.answer(
            """
❌ استفاده صحیح

/trade user_id card_name price

مثال:
/trade 123456789 JJK Card 1 200
"""
        )
        return

    try:
        target_user = int(args[1])
        price = int(args[-1])
    except:
        await message.answer(
            "❌ شناسه یا قیمت نامعتبر است"
        )
        return

    card_name = " ".join(args[2:-1])

    seller = message.from_user.id

    card = get_card_by_name(
        seller,
        card_name
    )

    if not card:
        await message.answer(
            "❌ کارت پیدا نشد"
        )
        return

    buyer_points = get_points(target_user)

    if buyer_points < price:
        await message.answer(
            f"""
❌ خریدار امتیاز کافی ندارد

💰 موجودی خریدار:
{buyer_points}

💵 قیمت کارت:
{price}
"""
        )
        return

    card_id = card[0]

    remove_points(
        target_user,
        price
    )

    add_points(
        seller,
        price
    )

    transfer_card(
        card_id,
        seller,
        target_user
    )

    await message.answer(
        f"""
✅ معامله انجام شد

🎴 کارت:
{card_name}

💵 مبلغ:
{price}

👤 خریدار:
{target_user}
"""
    )


# =========================
# CHANS
# =========================
@dp.message(Command("chans"))
async def chans(message: Message):

    uid = message.from_user.id

    now = int(time.time())

    last = get_last_chans(uid)

    remain = 3600 - (now - last)

    if remain > 0:

        minutes = remain // 60
        seconds = remain % 60

        await message.answer(
            f"""
⏳ هنوز باید صبر کنی

🕒 زمان باقی‌مانده:
{minutes} دقیقه و {seconds} ثانیه
"""
        )
        return

    reward = random.randint(100, 300)

    add_points(uid, reward)

    set_last_chans(uid, now)

    await message.answer(
        f"""
🎰 جایزه دریافت شد

💎 جایزه:
{reward} امتیاز

💰 موجودی جدید:
{get_points(uid)}

🕒 استفاده بعدی:
1 ساعت دیگر
"""
    )
    # =========================
# CALLBACK SHOP
# =========================
@dp.callback_query(F.data == "shop")
async def cb_shop(callback: CallbackQuery):

    uid = callback.from_user.id

    register_user(uid)

    points = get_points(uid)

    if points < 30:
        await callback.message.answer(
            f"""
❌ امتیاز کافی نیست

💰 موجودی شما:
{points}

🎴 قیمت پک:
30
"""
        )

        await callback.answer()
        return

    remove_points(uid, 30)

    pack = random.sample(CARDS, 8)

    for name, img in pack:
        add_unopened_card(uid, name, img)

    await callback.message.answer(
        f"""
📦 پک خریداری شد

🎴 تعداد کارت:
8

💰 موجودی جدید:
{get_points(uid)}

برای باز کردن:
/open
"""
    )

    await callback.answer()


# =========================
# CALLBACK OPEN
# =========================
@dp.callback_query(F.data == "open")
async def cb_open(callback: CallbackQuery):

    uid = callback.from_user.id

    card = get_next_unopened(uid)

    if not card:

        await callback.message.answer(
            "📦 هیچ کارت بازنشده‌ای نداری"
        )

        await callback.answer()
        return

    card_id, _, card_name, image_file = card

    try:

        image_path = os.path.join(
            BASE_PATH,
            image_file
        )

        photo = FSInputFile(image_path)

        await callback.message.answer_photo(
            photo,
            caption=f"🎴 {card_name}"
        )

    except Exception:

        await callback.message.answer(
            f"🎴 {card_name}"
        )

    move_card_to_inventory(card_id)

    await callback.message.answer(
        f"""
📦 باقی‌مانده:
{unopened_count(uid)}
"""
    )

    await callback.answer()


# =========================
# CALLBACK INVENTORY
# =========================
@dp.callback_query(F.data == "inv")
async def cb_inv(callback: CallbackQuery):

    uid = callback.from_user.id

    cards = get_inventory(uid)

    if not cards:

        await callback.message.answer(
            "🎒 اینونتوری شما خالی است"
        )

        await callback.answer()
        return

    text = (
        f"🎒 اینونتوری شما\n\n"
        f"📊 تعداد کارت‌ها: {len(cards)}\n\n"
    )

    for i, card in enumerate(cards, start=1):

        text += f"{i}. {card[1]}\n"

    await callback.message.answer(text)

    await callback.answer()


# =========================
# CALLBACK CHANS
# =========================
@dp.callback_query(F.data == "chans")
async def cb_chans(callback: CallbackQuery):

    uid = callback.from_user.id

    now = int(time.time())

    last = get_last_chans(uid)

    remain = 3600 - (now - last)

    if remain > 0:

        minutes = remain // 60
        seconds = remain % 60

        await callback.message.answer(
            f"""
⏳ هنوز باید صبر کنی

🕒 {minutes} دقیقه
🕒 {seconds} ثانیه
"""
        )

        await callback.answer()
        return

    reward = random.randint(100, 300)

    add_points(uid, reward)

    set_last_chans(uid, now)

    await callback.message.answer(
        f"""
🎰 جایزه دریافت شد

💎 {reward} امتیاز

💰 موجودی فعلی:
{get_points(uid)}
"""
    )

    await callback.answer()


# =========================
# RUN
# =========================
async def main():

    init_db()

    print("Bot Started...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
