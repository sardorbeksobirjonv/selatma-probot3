from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters
)
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio

TOKEN = "8380067781:AAEU9rD2Ei3debul7_nkDoiAV3C79zUN4Zo"  # O'z tokeningizni yozing

# States
LANGUAGE, CONTACT, REGION, REMINDER_TYPE, SET_CHANNEL, SET_GROUP, TIME, REMINDER_TEXT, REMINDER_REPEAT, MAIN_MENU, DELETE_ID, EDIT_CHOOSE, EDIT_ACTION, EDIT_INPUT, CONFIRM_EDIT = range(15)

users = {}

ZONE_MAP = {
    "russia": "Europe/Moscow",
    "rossiya": "Europe/Moscow",
    "moscow": "Europe/Moscow",
    "moskva": "Europe/Moscow",
    "tashkent": "Asia/Tashkent",
    "tokyo": "Asia/Tokyo",
    "new york": "America/New_York"
}

REPEAT_OPTIONS = {
    "Hech qachon": 0,
    "Har kun": 1,
    "Har hafta": 7,
    "Har oy": 30
}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["🇺🇿 O'zbek"], ["🇷🇺 Русский"]]
    await update.message.reply_text(
        "Tilni tanlang / Выберите язык",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return LANGUAGE

async def language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users[update.effective_user.id] = {"reminders": []}
    kb = [[KeyboardButton("📱 Raqam yuborish", request_contact=True)]]
    await update.message.reply_text(
        "Telefon raqamingizni yuboring",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return CONTACT

# ================= CONTACT =================
async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    if contact is None:
        await update.message.reply_text("Iltimos, telefon raqamingizni yuboring.")
        return CONTACT
    users[update.effective_user.id]["phone"] = contact.phone_number
    await update.message.reply_text(
        "🌍 Mintaqani yozing (masalan: Rossiya,)",
        reply_markup=ReplyKeyboardRemove()
    )
    return REGION

# ================= REGION =================
async def region(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip().lower()
    if user_input not in ZONE_MAP:
        await update.message.reply_text("❌ Mintaqa topilmadi. Iltimos, to‘g‘ri mintaqa yozing.")
        return REGION

    tz_name = ZONE_MAP[user_input]
    users[update.effective_user.id]["tz"] = ZoneInfo(tz_name)
    # So‘ng eslatma turini soraymiz
    kb = [["Shaxsi"], ["Kanal"], ["Guruh"]]
    await update.message.reply_text(
        "🔔 Eslatma turini tanlang:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return REMINDER_TYPE

# ================= REMINDER TYPE =================
async def reminder_type_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    choice = update.message.text.strip().lower()
    users[user_id]["current_reminder"] = {"type": choice}

    if choice == "kanal":
        await update.message.reply_text("📢 Kanal ID sini kiriting (faqat raqam):", reply_markup=ReplyKeyboardRemove())
        return SET_CHANNEL
    elif choice == "guruh":
        await update.message.reply_text("👥 Guruh ID sini kiriting (faqat raqam):", reply_markup=ReplyKeyboardRemove())
        return SET_GROUP
    else:
        await update.message.reply_text("⏰ Eslatma vaqtini kiriting (HH:MM)")
        return TIME

async def set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        channel_id = int(update.message.text.strip())
        users[user_id]["current_reminder"]["channel_id"] = channel_id
    except:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting.")
        return SET_CHANNEL
    await update.message.reply_text("⏰ Eslatma vaqtini kiriting (HH:MM)")
    return TIME

async def set_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        group_id = int(update.message.text.strip())
        users[user_id]["current_reminder"]["group_id"] = group_id
    except:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting.")
        return SET_GROUP
    await update.message.reply_text("⏰ Eslatma vaqtini kiriting (HH:MM)")
    return TIME

# ================= TIME =================
async def time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        hour, minute = map(int, update.message.text.strip().split(":"))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError()
    except:
        await update.message.reply_text("❌ Vaqt noto‘g‘ri formatda! HH:MM ko‘rinishida yozing.")
        return TIME

    users[user_id]["current_reminder"]["hour"] = hour
    users[user_id]["current_reminder"]["minute"] = minute
    await update.message.reply_text("✏️ Eslatma matnini yozing")
    return REMINDER_TEXT

# ================= REMINDER TEXT =================
async def reminder_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    users[user_id]["current_reminder"]["text"] = text

    kb = [["Hech qachon", "Har kun"], ["Har hafta", "Har oy"]]
    await update.message.reply_text(
        "🔁 Eslatma qayta takrorlansinmi?",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return REMINDER_REPEAT

# ================= REMINDER REPEAT =================
async def reminder_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    repeat = update.message.text.strip()
    if repeat not in REPEAT_OPTIONS:
        await update.message.reply_text("❌ Iltimos, menyudan tanlang.")
        return REMINDER_REPEAT

    reminder = users[user_id]["current_reminder"]
    reminder["repeat_days"] = REPEAT_OPTIONS[repeat]
    reminder["id"] = len(users[user_id]["reminders"]) + 1
    users[user_id]["reminders"].append(reminder)
    users[user_id].pop("current_reminder", None)

    await update.message.reply_text("✅ Eslatma saqlandi!", reply_markup=ReplyKeyboardRemove())

    # Async eslatma ishga tushadi
    asyncio.create_task(schedule_reminder(user_id, reminder, context))
    return await main_menu(update, context)

# ================= MAIN MENU =================
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["➕ Yangi eslatma qo‘shish"],
        ["📋 Eslatmalar ro‘yxati"],
        ["❌ Eslatmani o‘chirish"],
        ["✏️ Eslatmani tahrirlash"],
        ["🚪 Chiqish"]
    ]
    await update.message.reply_text(
        "Asosiy menyu:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)
    )
    return MAIN_MENU

async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "➕ Yangi eslatma qo‘shish":
        await update.message.reply_text("🌍 Mintaqani yozing", reply_markup=ReplyKeyboardRemove())
        return REGION
    elif text == "📋 Eslatmalar ro‘yxati":
        reminders = users[user_id].get("reminders", [])
        if not reminders:
            await update.message.reply_text("📭 Eslatma yo‘q")
        else:
            msg = ""
            for r in reminders:
                repeat_text = next(k for k,v in REPEAT_OPTIONS.items() if v == r["repeat_days"])
                r_type = r.get("type", "Shaxsi").capitalize()
                msg += f"ID:{r['id']} - {r['text']} ({r['hour']:02d}:{r['minute']:02d}, {repeat_text}, {r_type})\n"
            await update.message.reply_text(msg)
        return MAIN_MENU
    elif text == "❌ Eslatmani o‘chirish":
        return await delete_reminder(update, context)
    elif text == "✏️ Eslatmani tahrirlash":
        return await edit_choose(update, context)
    elif text == "🚪 Chiqish":
        await update.message.reply_text("Botdan foydalanganingiz uchun rahmat!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Noto‘g‘ri tanlov.")
        return MAIN_MENU

# ================= DELETE =================
async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reminders = users[user_id].get("reminders", [])
    if not reminders:
        await update.message.reply_text("📭 Sizda o‘chiriladigan eslatma yo‘q.")
        return MAIN_MENU

    msg = "❌ O‘chirmoqchi bo‘lgan eslatma ID sini kiriting:\n"
    for r in reminders:
        repeat_text = next(k for k,v in REPEAT_OPTIONS.items() if v == r["repeat_days"])
        r_type = r.get("type", "Shaxsi").capitalize()
        msg += f"ID:{r['id']} - {r['text']} ({r['hour']:02d}:{r['minute']:02d}, {repeat_text}, {r_type})\n"
    await update.message.reply_text(msg)
    return DELETE_ID

async def delete_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        del_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting.")
        return DELETE_ID

    reminders = users[user_id].get("reminders", [])
    for r in reminders:
        if r["id"] == del_id:
            reminders.remove(r)
            await update.message.reply_text(f"✅ ID:{del_id} eslatma o‘chirildi.")
            return await main_menu(update, context)

    await update.message.reply_text("❌ Bunday ID topilmadi. Qayta urinib ko‘ring.")
    return DELETE_ID

# ================= EDIT =================
async def edit_choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reminders = users[user_id].get("reminders", [])
    if not reminders:
        await update.message.reply_text("📭 Tahrirlash uchun eslatma yo‘q.")
        return MAIN_MENU

    msg = "✏️ Tahrirlash uchun eslatma ID sini kiriting:\n"
    for r in reminders:
        repeat_text = next(k for k,v in REPEAT_OPTIONS.items() if v == r["repeat_days"])
        r_type = r.get("type", "Shaxsi").capitalize()
        msg += f"ID:{r['id']} - {r['text']} ({r['hour']:02d}:{r['minute']:02d}, {repeat_text}, {r_type})\n"
    await update.message.reply_text(msg)
    return EDIT_CHOOSE

async def edit_choose_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        edit_id = int(update.message.text.strip())
    except:
        await update.message.reply_text("❌ Iltimos, faqat raqam kiriting.")
        return EDIT_CHOOSE

    reminders = users[user_id].get("reminders", [])
    for r in reminders:
        if r["id"] == edit_id:
            users[user_id]["edit_reminder"] = r
            kb = [["Matnni o‘zgartirish"], ["Soatni o‘zgartirish"], ["Bekor qilish"]]
            await update.message.reply_text("✏️ Nimalarni tahrirlashni xohlaysiz?", 
                                            reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
            return EDIT_ACTION
    await update.message.reply_text("❌ Bunday ID topilmadi.")
    return EDIT_CHOOSE

async def edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "Matnni o‘zgartirish":
        await update.message.reply_text("✏️ Yangi matnni kiriting:", reply_markup=ReplyKeyboardRemove())
        return EDIT_INPUT
    elif text == "Soatni o‘zgartirish":
        await update.message.reply_text("⏰ Yangi soatni kiriting (HH:MM):", reply_markup=ReplyKeyboardRemove())
        return EDIT_INPUT
    else:
        await update.message.reply_text("❌ Bekor qilindi", reply_markup=ReplyKeyboardRemove())
        return await main_menu(update, context)

async def edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminder = users[update.effective_user.id]["edit_reminder"]
    text = update.message.text.strip()
    if ":" in text:
        try:
            hour, minute = map(int, text.split(":"))
            reminder["hour"] = hour
            reminder["minute"] = minute
        except:
            await update.message.reply_text("❌ Vaqt format noto‘g‘ri. HH:MM ko‘rinishida yozing.")
            return EDIT_INPUT
    else:
        reminder["text"] = text

    kb = [["Ha"], ["Yo‘q"]]
    await update.message.reply_text("💾 Saqlansinmi?", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return CONFIRM_EDIT

async def confirm_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text.strip().lower()
    if choice == "ha":
        reminder = users[update.effective_user.id]["edit_reminder"]
        asyncio.create_task(schedule_reminder(update.effective_user.id, reminder, context))
        await update.message.reply_text("✅ Eslatma tahrirlandi va saqlandi.", reply_markup=ReplyKeyboardRemove())
    else:
        await update.message.reply_text("❌ Tahrir saqlanmadi.", reply_markup=ReplyKeyboardRemove())

    users[update.effective_user.id].pop("edit_reminder", None)
    return await main_menu(update, context)

# ================= SCHEDULE REMINDER =================
async def schedule_reminder(user_id: int, reminder: dict, context: ContextTypes.DEFAULT_TYPE):
    tz = users[user_id]["tz"]
    hour = reminder["hour"]
    minute = reminder["minute"]
    text = reminder["text"]
    repeat_days = reminder["repeat_days"]
    r_type = reminder.get("type", "shaxsi")
    channel_id = reminder.get("channel_id")
    group_id = reminder.get("group_id")

    while True:
        now = datetime.now(tz)
        remind_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if remind_time <= now:
            remind_time += timedelta(days=1)

        wait_seconds = (remind_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        if r_type == "shaxsi":
            await context.bot.send_message(user_id, f"⏰ Eslatma: {text}")
        elif r_type == "kanal" and channel_id:
            await context.bot.send_message(channel_id, f"⏰ Kanal eslatma: {text}")
        elif r_type == "guruh" and group_id:
            await context.bot.send_message(group_id, f"⏰ Guruh eslatma: {text}")

        if repeat_days == 0:
            break
        else:
            remind_time += timedelta(days=repeat_days)

# ================= CANCEL =================
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Jarayon bekor qilindi", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.Regex("O'zbek|Русский"), language)],
            CONTACT: [MessageHandler(filters.CONTACT, contact)],
            REGION: [MessageHandler(filters.TEXT & ~filters.COMMAND, region)],
            REMINDER_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_type_choice)],
            SET_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_channel)],
            SET_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_group)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, time_input)],
            REMINDER_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_text)],
            REMINDER_REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, reminder_repeat)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)],
            DELETE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_id)],
            EDIT_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_choose_id)],
            EDIT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_action)],
            EDIT_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_input)],
            CONFIRM_EDIT: [MessageHandler(filters.Regex("Ha|Yo‘q"), confirm_edit)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
