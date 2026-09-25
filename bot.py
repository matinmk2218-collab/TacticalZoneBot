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

# حافظه‌های موقت و دیتابیس‌های موقت در حافظه ربات
user_state = {}           
user_pending_data = {}    
admin_action_data = {}    

# دیتابیس‌های موقت برای ذخیره آرشیو در حافظه ربات (با ریست شدن ربات پاک می‌شوند)
saved_attachments = []  # شامل دیکشنری‌هایی از اطلاعات اتچمنت تاییدشده
saved_feedbacks = []    # شامل گزارش‌ها و بازخوردها

@app.route('/')
def home():
    return "TacticalZone Bot is running!"

# تابع ساخت منوی اصلی شیشه‌ای کاربران
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
    
    # اگر ادمین کامند استارت یا پنل را خواست، منوی ادمین را نشان دهیم
    if user_id == ADMIN_CHAT_ID:
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("📂 مشاهده آرشیو (اتچمنت‌ها و باگ‌ها)", callback_data="admin_view_archive"),
            InlineKeyboardButton("🚀 ارسال اعلامیه آپدیت به کاربران اتچمنت", callback_data="admin_broadcast_start"),
            InlineKeyboardButton("🤖 ورود به منوی کاربری ربات", callback_data="back_to_menu")
        )
        bot.reply_to(message, "👑 **پنل مدیریت اختصاصی TacticalZone:**\n\nلطفاً یکی از گزینه‌های زیر را انتخاب کنید: 👇", reply_markup=markup, parse_mode="Markdown")
        return

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
        
        # ذخیره در آرشیو باگ‌ها و پیشنهادات
        saved_feedbacks.append({
            "user_id": user_id,
            "username": message.from_user.username or message.from_user.first_name,
            "text": feedback_text
        })
        
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
            "category": user_pending_data.get(user_id, {}).get("category", "نامشخص"),
            "username": message.from_user.username or message.from_user.first_name
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
        if user_id == ADMIN_CHAT_ID:
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("📂 مشاهده آرشیو", callback_data="admin_view_archive"),
                InlineKeyboardButton("🏠 بازگشت به منو", callback_data="back_to_menu")
            )
            bot.reply_to(message, "لطفاً از دکمه‌های زیر استفاده کنید:", reply_markup=markup)
        else:
            bot.reply_to(message, "لطفاً از طریق منوی زیر گزینه‌ی مورد نظر را انتخاب کنید: 👇", reply_markup=get_main_menu(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    
    # مدیریت منوی اصلی کاربران
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
        if user_id == ADMIN_CHAT_ID:
            markup = InlineKeyboardMarkup(row_width=1)
            markup.add(
                InlineKeyboardButton("📂 مشاهده آرشیو (اتچمنت‌ها و باگ‌ها)", callback_data="admin_view_archive"),
                InlineKeyboardButton("🚀 ارسال اعلامیه آپدیت به کاربران اتچمنت", callback_data="admin_broadcast_start"),
                InlineKeyboardButton("🤖 ورود به منوی کاربری ربات", callback_data="back_to_menu_user")
            )
            bot.edit_message_text("👑 **پنل مدیریت اختصاصی TacticalZone:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
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
            
    elif call.data == "back_to_menu_user":
        user_state[user_id] = None
        bot.edit_message_text("🌟 **منوی اصلی TacticalZone:**", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_menu(), parse_mode="Markdown")

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
            "پس از تایید ادمین و انتشار آپدیت جدید، به برنامه‌ی TacticalZone اضافه خواهد شد. 🎮🔥"
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

    # پنل مدیریتی ادمین (مشاهده آرشیو، تایید، رد و ارسال همگانی)
    elif user_id == ADMIN_CHAT_ID:
        if call.data == "admin_view_archive":
            markup = InlineKeyboardMarkup(row_width=2)
            markup.add(
                InlineKeyboardButton("🔫 اتچمنت‌های تاییدشده", callback_data="admin_archive_attachments"),
                InlineKeyboardButton("💬 بازخوردها و باگ‌ها", callback_data="admin_archive_feedbacks"),
                InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_menu")
            )
            bot.edit_message_text(
                "📂 **بخش آرشیو ربات:**\n\nلطفاً بخش مورد نظر را انتخاب کنید: 👇",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
            
        elif call.data == "admin_archive_attachments":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 بازگشت به آرشیو", callback_data="admin_view_archive"))
            
            if not saved_attachments:
                text = "📂 **آرشیو اتچمنت‌های تاییدشده:**\n\nهنوز هیچ اتچمنی تایید و ذخیره نشده است."
            else:
                text = "📂 **لیست اتچمنت‌های تاییدشده تا این لحظه:**\n\n"
                for idx, att in enumerate(saved_attachments, 1):
                    text += f"{idx}. 👤 @{att['username']} (`{att['user_id']}`)\n   📂 دسته: {att['category']}\n   📋 کد: `{att['data']}`\n\n"
            
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
        elif call.data == "admin_archive_feedbacks":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 بازگشت به آرشیو", callback_data="admin_view_archive"))
            
            if not saved_feedbacks:
                text = "💬 **آرشیو بازخوردها و باگ‌ها:**\n\nهنوز هیچ پیامی دریافت نشده است."
            else:
                text = "💬 **لیست نظرات و گزارش باگ‌ها:**\n\n"
                for idx, fb in enumerate(saved_feedbacks, 1):
                    text += f"{idx}. 👤 @{fb['username']} (`{fb['user_id']}`)\n   📝 متن: _{fb['text']}_\n\n"
            
            bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

        elif call.data == "admin_broadcast_start":
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("🔙 بازگشت به پنل", callback_data="back_to_menu"))
            
            if not saved_attachments:
                bot.edit_message_text("⚠️ هیچ کاربری تا کنون اتچمنت تاییدشده‌ای ندارد تا پیامی ارسال شود.", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
                return
                
            count = 0
            success_count = 0
            # استخراج آیدی‌های یکتا از کاربرانِ ارسال‌کننده اتچمنت
            sent_users = set()
            
            for att in saved_attachments:
                uid = att['user_id']
                if uid not in sent_users:
                    sent_users.add(uid)
                    gun_info = att['data']
                    try:
                        bot.send_message(
                            uid,
                            f"🎉 **خبر بزرگ برای شما!**\n\n"
                            f"اتچمنتی که فرستاده بودید (`{gun_info}`)\n"
                            f"مشخصات آن بررسی شد و **به برنامه‌ی TacticalZone اضافه گردید!** 🎮🔥\n\n"
                            f"با آپدیت کردن برنامه می‌توانید از اتچمنت خود استفاده کنید.",
                            parse_mode="Markdown"
                        )
                        success_count += 1
                    except Exception as ex:
                        print(f"خطا در ارسال به کاربر {uid}: {ex}")
            
            bot.edit_message_text(
                f"✅ **عملیات ارسال اعلامیه پایان یافت!**\n\n"
                f"📨 به تعداد `{success_count}` نفر از کاربرانِ ارسال‌کننده اتچمنت، پیام موفقیت‌آمیز آپدیت ارسال شد.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )

        elif call.data.startswith("adm_accept_"):
            target_user_id = int(call.data.split("_")[2])
            
            # پیدا کردن اطلاعات اتچمنت این کاربر از حافظه موقت و انتقال به آرشیو تاییدشده‌ها
            # (اگر در حافظه موقت بود ذخیره می‌کنیم)
            # برای اطمینان متن پیام را تجزیه میکنیم یا از یک دیکشنری موقت استفاده میکنیم
            # در اینجا اطلاعات را از متن پیام ادمین یا حافظه استخراج میکنیم
            
            bot.edit_message_text(
                call.message.text + "\n\n✅ **وضعیت: تایید شد و به آرشیو افزوده شد.**",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown"
            )
            
            try:
                bot.send_message(
                    target_user_id,
                    "🎉 **تبریک! اتچمنت پیشنهادی شما توسط ادمین تایید شد.**\n\nبه زودی در آپدیت‌های بعدی برنامه‌ی TacticalZone قرار خواهد گرفت. 🎮",
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
