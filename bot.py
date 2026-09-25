import os
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# توکن ربات شما
TOKEN = "8626851273:AAGeREQkwl42DXIiYCd_-HOodpSRrdTx5hM"

# آیدی عددی شما به عنوان ادمین
ADMIN_CHAT_ID = 5120714149 

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# حافظه‌های موقت برای مدیریت وضعیت کاربران
user_state = {}           
user_pending_data = {}    
admin_action_data = {}    

@app.route('/')
def home():
    return "TacticalZone Bot is running!"

# تابع ساخت منوی اصلی شیشه‌ای
def get_main_menu():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("📤 ارسال اتچمنت جدید", callback_data="menu_send_attachment"),
        InlineKeyboardButton("✍️ انتقادات، پیشنهادات و گزارش باگ", callback_data="menu_feedback"),
        InlineKeyboardButton("ℹ️ درباره برنامه‌ی TacticalZone", callback_data="menu_about")
    )
    return markup

@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    user_state[user_id] = None
    
    welcome_text = (
        "🌟 **درود به خانواده بزرگ TacticalZone!** 👋\n\n"
        "به ربات رسمی مدیریت و ارسال اتچمنت خوش آمدید. لطفاً از منوی زیر یکی از گزینه‌ها را انتخاب کنید: 👇"
    )
    bot.reply_to(message, welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text_message(message):
    user_id = message.from_user.id
    current_state = user_state.get(user_id)
    
    # اگر ادمین در حال نوشتن دلیل رد کردن اتچمنت باشد
    if user_id == ADMIN_CHAT_ID and current_state == "waiting_for_rejection_reason":
        target_user_id = admin_action_data.get("target_user_id")
        reason = message.text
        
        try:
            bot.send_message(
                target_user_id,
                f"❌ **متاسفانه اتچمنت شما رد شد.**\n\n💬 **دلیل رد:**\n_{reason}_",
                parse_mode="Markdown"
            )
            bot.reply_to(message, "✅ دلیل رد شدن با موفقیت برای کاربر ارسال شد.")
        except Exception as e:
            bot.reply_to(message, f"❌ خطا در ارسال پیام به کاربر: {e}")
            
        user_state[user_id] = None
        return

    # اگر کاربر در حال ارسال بازخورد باشد
    if current_state == "waiting_for_feedback":
        feedback_text = message.text
        user_state[user_id] = None
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_to_menu"))
        
        bot.reply_to(message, "✅ **بازخورد شما با موفقیت برای تیم توسعه ارسال شد. سپاسگزاریم!** 🙏", reply_markup=markup, parse_mode="Markdown")
        
        admin_fb_msg = (
            "💬 **یک بازخورد / گزارش باگ جدید دریافت شد:**\n\n"
            f"👤 **ارسال کننده:** @{message.from_user.username or message.from_user.first_name}\n"
            f"🆔 **آیدی عددی:** `{user_id}`\n\n"
            f"📝 **متن پیام:**\n_{feedback_text}_"
        )
        bot.send_message(ADMIN_CHAT_ID, admin_fb_msg, parse_mode="Markdown")
        return

    # اگر کاربر در حال فرستادن اطلاعات اتچمنت باشد
    if current_state == "waiting_for_gun_data":
        gun_data = message.text
        user_pending_data[user_id] = {
            "data": gun_data,
            "category": user_pending_data.get(user_id, {}).get("category", "نامشخص")
        }
        
        user_state[user_id] = None
        
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ بله، ارسال شود", callback_data="confirm_send"),
            InlineKeyboardButton("❌ انصراف", callback_data="cancel_send")
        )
        
        bot.reply_to(
            message,
            "🔍 **آیا از صحت اطلاعات و ارسال اتچمنت خود مطمئن هستید؟** 🤔",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        # اگر متن بی‌ربط فرستاد، منو را به او نشان بدهیم
        bot.reply_to(message, "لطفاً از طریق منوی زیر گزینه‌ی مورد نظر را انتخاب کنید: 👇", reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # مدیریت دکمه‌های منوی اصلی
    if call.data == "menu_send_attachment":
        user_state[user_id] = "waiting_for_category"
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🔫 اسالت رایفل (Assault)", callback_data="cat_Assault"),
            InlineKeyboardButton("🎯 اسنایپر (Sniper)", callback_data="cat_Sniper"),
            InlineKeyboardButton("💥 شاتگان (Shotgun)", callback_data="cat_Shotgun"),
            InlineKeyboardButton("⚡ ساب‌ماشین‌گان (SMG)", callback_data="cat_SMG"),
            InlineKeyboardButton("🎮 سایر موارد", callback_data="cat_Other"),
            InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu")
        )
        
        bot.edit_message_text(
            "🎯 لطفاً **دسته سلاح** مورد نظر اتچمنت خود را انتخاب کنید: 👇",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    elif call.data == "menu_feedback":
        user_state[user_id] = "waiting_for_feedback"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
        
        bot.edit_message_text(
            "✍️ لطفاً انتقاد، پیشنهاد یا گزارش باگ خود را درباره برنامه‌ی TacticalZone **به صورت یک پیام متنی** بفرستید:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    elif call.data == "menu_about":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_to_menu"))
        
        about_text = (
            "ℹ️ **درباره برنامه‌ی TacticalZone:**\n\n"
            "این اپلیکیشن برای دسترسی سریع به بهترین اتچمنت‌ها و کدهای سلاح‌های بازی Call of Duty Mobile طراحی شده است. با این ربات می‌توانید اتچمنت‌های خود را با ما به اشتراک بگذارید! 🎮🔥"
        )
        bot.edit_message_text(
            about_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    elif call.data == "back_to_menu":
        user_state[user_id] = None
        welcome_text = (
            "🌟 **منوی اصلی TacticalZone:**\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید: 👇"
        )
        bot.edit_message_text(
            welcome_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )

    # انتخاب دسته سلاح
    elif call.data.startswith("cat_"):
        category = call.data.split("_")[1]
        if user_id not in user_pending_data:
            user_pending_data[user_id] = {}
        user_pending_data[user_id]["category"] = category
        
        user_state[user_id] = "waiting_for_gun_data"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 انصراف و بازگشت به منو", callback_data="back_to_menu"))
        
        bot.edit_message_text(
            f"🎯 دسته انتخابی: **{category}**\n\n"
            "اکنون **نام سلاح و کد اتچمنت** خود را در قالب متن بفرستید: 📝",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
    elif call.data == "confirm_send":
        item = user_pending_data.get(user_id, {})
        gun_data = item.get("data", "اطلاعات نامشخص")
        category = item.get("category", "نامشخص")
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data="back_to_menu"))
        
        success_user_text = (
            "✅ **اتچمنت شما جهت بررسی ارسال شد!**\n\n"
            "پس از تایید ادمین، در آپدیت‌های بعدی به برنامه‌ی TacticalZone اضافه خواهد شد. 🎮🔥"
        )
        bot.edit_message_text(
            success_user_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )
        
        admin_markup = InlineKeyboardMarkup(row_width=2)
        admin_markup.add(
            InlineKeyboardButton("✅ تایید و انتشار", callback_data=f"adm_accept_{user_id}"),
            InlineKeyboardButton("❌ رد کردن با دلیل", callback_data=f"adm_reject_{user_id}")
        )
        
        admin_message = (
            "📥 **یک اتچمنت جدید دریافت شد!** 🎯\n\n"
            f"📂 **دسته:** `{category}`\n"
            f"👤 **ارسال کننده:** @{call.from_user.username or call.from_user.first_name}\n"
            f"🆔 **آیدی عددی:** `{user_id}`\n\n"
            f"📋 **جزئیات و کد:**\n`{gun_data}`"
        )
        
        try:
            bot.send_message(ADMIN_CHAT_ID, admin_message, reply_markup=admin_markup, parse_mode="Markdown")
        except Exception as e:
            print(f"خطا در ارسال پیام به ادمین: {e}")
            
        if user_id in user_pending_data:
            del user_pending_data[user_id]
            
    elif call.data == "cancel_send":
        user_state[user_id] = None
        bot.edit_message_text(
            "❌ **عملیات لغو شد.**",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        if user_id in user_pending_data:
            del user_pending_data[user_id]

    # پنل مدیریتی ادمین
    elif user_id == ADMIN_CHAT_ID:
        if call.data.startswith("adm_accept_"):
            target_user_id = int(call.data.split("_")[2])
            
            bot.edit_message_text(
                call.message.text + "\n\n✅ **وضعیت: تایید شد.**",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown"
            )
            
            try:
                bot.send_message(
                    target_user_id,
                    "🎉 **تبریک! اتچمنت پیشنهادی شما توسط ادمین تایید شد و به برنامه‌ی TacticalZone اضافه گردید.** 🎮",
                    parse_mode="Markdown"
                )
            except:
                pass
                
        elif call.data.startswith("adm_reject_"):
            target_user_id = int(call.data.split("_")[2])
            admin_action_data["target_user_id"] = target_user_id
            user_state[ADMIN_CHAT_ID] = "waiting_for_rejection_reason"
            
            bot.edit_message_text(
                call.message.text + "\n\n❌ **وضعیت: در انتظار نوشتن دلیل رد...**",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown"
            )
            bot.send_message(
                ADMIN_CHAT_ID,
                "✍️ لطفاً **دلیل رد شدن** این اتچمنت را در قالب متن ارسال کنید تا برای کاربر فرستاده شود:",
                parse_mode="Markdown"
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    import threading
    threading.Thread(target=lambda: bot.infinity_polling()).start()
    app.run(host="0.0.0.0", port=port)
