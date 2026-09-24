import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# توکن ربات شما
TOKEN = "8626851273:AAGeREQkwl42DXIiYCd_-HOodpSRrdTx5hM"

# آیدی عددی شما به عنوان ادمین
ADMIN_CHAT_ID = 5120714149 

bot = telebot.TeleBot(TOKEN)

# ذخیره موقت اطلاعات کاربران در حافظه موقت ربات
user_pending_data = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    text_parts = message.text.split(maxsplit=1)
    
    if len(text_parts) > 1:
        # اگر کاربر مستقیماً از داخل برنامه اندرویدی روی لینک استارت زده باشد
        gun_data = text_parts[1]
        user_pending_data[message.from_user.id] = gun_data
        
        # پرسیدن سوال برای تایید نهایی
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ بله، ارسال شود", callback_data="confirm_send"),
            InlineKeyboardButton("❌ انصراف", callback_data="cancel_send")
        )
        
        bot.reply_to(
            message,
            "🔍 **آیا از ارسال اتچمنت خود مطمئن هستید؟** 🤔",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        # متن خوش آمدگویی اولیه
        welcome_text = (
            "🌟 **درود، خوش آمدید!** 👋\n\n"
            "جهت ارسال اتچمنت، اسم گان و کد اتچمنت را ارسال کنید. 📝✨"
        )
        bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text_message(message):
    # اگر کاربر متن عادی (مثل اسم گان و کد) بفرستد
    gun_data = message.text
    user_pending_data[message.from_user.id] = gun_data
    
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ بله، ارسال شود", callback_data="confirm_send"),
        InlineKeyboardButton("❌ انصراف", callback_data="cancel_send")
    )
    
    bot.reply_to(
        message,
        "🔍 **آیا از ارسال اتچمنت خود مطمئن هستید؟** 🤔",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    if call.data == "confirm_send":
        gun_data = user_pending_data.get(user_id, "اطلاعات نامشخص")
        
        # پیام تایید نهایی به کاربر
        success_user_text = (
            "✅ **اتچمنت شما جهت بررسی ارسال شد!**\n\n"
            "پس از تایید، در آپدیت‌های بعدی به برنامه‌ی TacticalZone اضافه خواهد شد. 🎮🔥"
        )
        bot.edit_message_text(
            success_user_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        
        # ارسال پیام دقیق و کامل به چت شخصی شما (ادمین)
        admin_message = (
            "📥 **یک اتچمنت جدید و تایید شده دریافت شد!** 🎯\n\n"
            f"👤 **ارسال کننده:** @{call.from_user.username or call.from_user.first_name}\n"
            f"🆔 **آیدی عددی:** `{user_id}`\n\n"
            f"📋 **جزئیات و کد اتچمنت:**\n`{gun_data}`"
        )
        
        try:
            bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="Markdown")
        except Exception as e:
            print(f"خطا در ارسال پیام به ادمین: {e}")
            
        # پاک کردن داده موقت
        if user_id in user_pending_data:
            del user_pending_data[user_id]
            
    elif call.data == "cancel_send":
        # اگر کاربر انصراف داد
        cancel_text = (
            "❌ **عملیات ارسال لغو شد.**\n\n"
            "🌟 **درود، خوش آمدید!** 👋\n"
            "جهت ارسال اتچمنت، اسم گان و کد اتچمنت را ارسال کنید. 📝✨"
        )
        bot.edit_message_text(
            cancel_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown"
        )
        if user_id in user_pending_data:
            del user_pending_data[user_id]

print("Robot is running smoothly...")
bot.infinity_polling()