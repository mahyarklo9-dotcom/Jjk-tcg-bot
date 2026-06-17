import asyncio
import random
import os
import time

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from db import *
from cards import CARDS, BASE_PATH


TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# TEMP STATES
# =========================

sell_states = {}
trade_states = {}


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

خوش آمدی

💰 امتیاز فعلی: {points}

برای مشاهده دستورات:

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
📖 راهنمای کامل

/start
شروع بازی

/help
نمایش راهنما

/profile
نمایش اطلاعات حساب

/points
نمایش امتیاز

/shop
خرید یک پک (30 امتیاز)

/pack
نمایش تعداد کارت‌های بازنشده

/open
باز کردن یک کارت

/inv
نمایش اینونتوری

/card
نمایش یک کارت تصادفی

/chans
جایزه تصادفی هر یک ساعت

/sell
فروش کارت

/trade
انتقال کارت به بازیکن دیگر

/debug
نمایش اطلاعات حساب

/testpoints
افزودن 100 امتیاز تستی
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

🆔 {uid}

💰 امتیاز:
{get_points(uid)}

🎒 تعداد کارت:
{len(cards)}

📦 کارت بازنشده:
{unopened}
"""
    )


# =========================
# POINTS
# =========================

@dp.message(Command("points"))
async def points(message: Message):

    uid = message.from_user.id

    register_user(uid)

    await message.answer(
        f"💰 امتیاز فعلی شما: {get_points(uid)}"
    )


# =========================
# PACK
# =========================

@dp.message(Command("pack"))
async def pack(message: Message):

    uid = message.from_user.id

    await message.answer(
        f"""
📦 کارت‌های بازنشده

تعداد:
{unopened_count(uid)}

برای باز کردن:
/open
"""
    )


# =========================
# RANDOM CARD
# =========================

@dp.message(Command("card"))
async def card(message: Message):

    card_name, _ = random.choice(CARDS)

    await message.answer(
        f"""
🎴 کارت تصادفی

{card_name}
"""
    )


# =========================
# DEBUG
# =========================

@dp.message(Command("debug"))
async def debug(message: Message):

    uid = message.from_user.id

    await message.answer(
        f"""
🛠 اطلاعات حساب

ID:
{uid}

Points:
{get_points(uid)}
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

💰 موجودی شما:
{points}

🎴 قیمت هر پک:
30
"""
        )
        return

    remove_points(uid, 30)

    pack_cards = random.sample(
        CARDS,
        min(8, len(CARDS))
    )

    for name, img in pack_cards:

        add_unopened_card(
            uid,
            name,
            img
        )

    await message.answer(
        f"""
✅ خرید موفق

📦 یک پک دریافت کردی

🎴 تعداد کارت:
{len(pack_cards)}

💰 موجودی فعلی:
{get_points(uid)}

برای باز کردن کارت:

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

برای خرید:

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

    await message.answer(
        f"""
✅ کارت به اینونتوری منتقل شد

📦 کارت باقی‌مانده:

{unopened_count(uid)}
"""
    )


# =========================
# INVENTORY
# =========================

@dp.message(Command("inv"))
async def inventory(message: Message):

    uid = message.from_user.id

    cards = get_inventory(uid)

    if not cards:

        await message.answer(
            """
🎒 اینونتوری شما خالی است

برای خرید کارت:

/shop
"""
        )
        return

    text = (
        f"🎒 اینونتوری شما\n\n"
        f"📊 تعداد کارت‌ها: {len(cards)}\n\n"
    )

    for index, card in enumerate(cards, start=1):

        text += f"{index}. {card[1]}\n"

    await message.answer(text)


# =========================
# CHANS
# =========================

@dp.message(Command("chans"))
async def chans(message: Message):

    uid = message.from_user.id

    register_user(uid)

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

{minutes} دقیقه
{seconds} ثانیه
"""
        )

        return

    reward = random.randint(
        100,
        300
    )

    add_points(
        uid,
        reward
    )

    set_last_chans(
        uid,
        now
    )

    await message.answer(
        f"""
🎰 جایزه دریافت شد

💎 جایزه:
{reward}

💰 موجودی فعلی:
{get_points(uid)}

استفاده بعدی:
1 ساعت دیگر
"""
    )
    # =========================
# SELL CARD
# =========================

@dp.message(Command("sell"))
async def sell_start(message: Message):

    uid = message.from_user.id

    cards = get_inventory(uid)

    if not cards:

        await message.answer(
            "🎒 اینونتوری شما خالی است"
        )
        return

    sell_states[uid] = {
        "step": "card"
    }

    await message.answer(
        "🎴 نام کارت را وارد کن:"
    )


# =========================
# TRADE CARD
# =========================

@dp.message(Command("trade"))
async def trade_start(message: Message):

    uid = message.from_user.id

    trade_states[uid] = {
        "step": "buyer"
    }

    await message.answer(
        "👤 شناسه خریدار را وارد کن:"
    )


# =========================
# SELL FLOW
# =========================

@dp.message()
async def sell_flow(message: Message):

    uid = message.from_user.id

    # ------------------
    # SELL
    # ------------------

    if uid in sell_states:

        state = sell_states[uid]

        if state["step"] == "card":

            card_name = message.text.strip()

            card = get_card_by_name(
                uid,
                card_name
            )

            if not card:

                await message.answer(
                    "❌ چنین کارتی در اینونتوری شما نیست"
                )
                return

            state["card_name"] = card_name
            state["step"] = "price"

            await message.answer(
                "💰 قیمت فروش را وارد کن:"
            )

            return

        if state["step"] == "price":

            try:

                price = int(
                    message.text.strip()
                )

            except:

                await message.answer(
                    "❌ فقط عدد وارد کن"
                )
                return

            card_name = state["card_name"]

            result = sell_card(
                uid,
                card_name,
                price
            )

            del sell_states[uid]

            if not result:

                await message.answer(
                    "❌ فروش انجام نشد"
                )
                return

            await message.answer(
                f"""
✅ کارت فروخته شد

🎴 کارت:
{card_name}

💰 مبلغ:
{price}

💎 موجودی جدید:
{get_points(uid)}
"""
            )

            return

    # ------------------
    # TRADE
    # ------------------

    if uid in trade_states:

        state = trade_states[uid]

        if state["step"] == "buyer":

            try:

                buyer = int(
                    message.text.strip()
                )

            except:

                await message.answer(
                    "❌ شناسه نامعتبر است"
                )
                return

            state["buyer"] = buyer
            state["step"] = "card"

            await message.answer(
                "🎴 نام کارت را وارد کن:"
            )

            return

        if state["step"] == "card":

            card_name = message.text.strip()

            card = get_card_by_name(
                uid,
                card_name
            )

            if not card:

                await message.answer(
                    "❌ کارت پیدا نشد"
                )
                return

            state["card_name"] = card_name
            state["step"] = "price"

            await message.answer(
                "💰 قیمت معامله را وارد کن:"
            )

            return

        if state["step"] == "price":

            try:

                price = int(
                    message.text.strip()
                )

            except:

                await message.answer(
                    "❌ قیمت نامعتبر است"
                )
                return

            buyer = state["buyer"]
            card_name = state["card_name"]

            buyer_points = get_points(
                buyer
            )

            if buyer_points < price:

                del trade_states[uid]

                await message.answer(
                    f"""
❌ خریدار امتیاز کافی ندارد

💰 موجودی خریدار:
{buyer_points}

💵 قیمت:
{price}
"""
                )

                return

            card = get_card_by_name(
                uid,
                card_name
            )

            if not card:

                del trade_states[uid]

                await message.answer(
                    "❌ کارت پیدا نشد"
                )

                return

            card_id = card[0]

            remove_points(
                buyer,
                price
            )

            add_points(
                uid,
                price
            )

            transfer_card(
                card_id,
                uid,
                buyer
            )

            del trade_states[uid]

            await message.answer(
                f"""
✅ معامله انجام شد

🎴 کارت:
{card_name}

👤 خریدار:
{buyer}

💰 مبلغ:
{price}
"""
            )

            return
            # =========================
# FALLBACK
# =========================

@dp.message()
async def unknown_command(message: Message):

    await message.answer(
        """
❓ دستور ناشناخته

برای مشاهده دستورات:

/help
"""
    )


# =========================
# RUN
# =========================

async def main():

    init_db()

    print("Bot Started...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
