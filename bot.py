import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from datetime import datetime

BOT_TOKEN = "7115175533:AAHcFYSUzqagDMuxOttx4jLUNCDdlVyvtZo"
ADMIN_PASSWORD = "jamais007"
SUPPORT_USERNAME = "blackdjdj"

bot = telebot.TeleBot(BOT_TOKEN)

def load_wallets():
    if not os.path.exists("wallet.json"):
        return {}
    with open("wallet.json", "r") as f:
        return json.load(f)

def save_wallets(wallets):
    with open("wallet.json", "w") as f:
        json.dump(wallets, f)

def load_admin_wallet():
    if not os.path.exists("admin_wallet.json"):
        return {"admin": 0}
    with open("admin_wallet.json", "r") as f:
        return json.load(f)

def save_admin_wallet(wallet):
    with open("admin_wallet.json", "w") as f:
        json.dump(wallet, f)

def load_services():
    with open("services.json", "r") as f:
        return json.load(f)

wallets = load_wallets()
admin_wallet = load_admin_wallet()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    wallets.setdefault(user_id, 0)
    save_wallets(wallets)

    with open("logo.jpg", "rb") as photo:
        bot.send_photo(message.chat.id, photo, caption="📌 Bienvenue sur le canal de BLACKDJLOG\n\nPour toute demande, passez en privé avec le support : @" + SUPPORT_USERNAME)

    markup = InlineKeyboardMarkup(row_width=2)
    categories = list(set(s["category"] for s in load_services() if s["enabled"]))
    for cat in categories:
        markup.add(InlineKeyboardButton(cat, callback_data="CAT_" + cat))
    markup.add(InlineKeyboardButton("💼 Mon solde", callback_data="SOLDE"))
    markup.add(InlineKeyboardButton("📞 Support", url=f"https://t.me/{SUPPORT_USERNAME}"))

    bot.send_message(message.chat.id, "⬇️ Choisissez une catégorie :", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("CAT_"))
def show_category(call):
    category = call.data.replace("CAT_", "")
    services = [s for s in load_services() if s["category"] == category and s["enabled"]]
    markup = InlineKeyboardMarkup()
    for s in services:
        label = f'{s["name"]} - {s["price"]}€'
        markup.add(InlineKeyboardButton(label, callback_data=f"BUY_{s['id']}"))
    markup.add(InlineKeyboardButton("🔙 Retour", callback_data="BACK"))
    bot.edit_message_text(f"📦 {category} :", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "SOLDE")
def solde_display(call):
    user_id = str(call.from_user.id)
    solde = wallets.get(user_id, 0)
    bot.answer_callback_query(call.id, text=f"💰 Solde : {solde}€")

@bot.callback_query_handler(func=lambda call: call.data.startswith("BUY_"))
def buy_service(call):
    service_id = call.data.replace("BUY_", "")
    user_id = str(call.from_user.id)
    services = load_services()
    service = next((s for s in services if s["id"] == service_id), None)
    if not service:
        bot.answer_callback_query(call.id, "Service introuvable.")
        return

    if service.get("restricted_time") is not None and datetime.now().hour != service["restricted_time"]:
        bot.answer_callback_query(call.id, "⏰ Ce service est dispo uniquement à 00h.")
        return

    if wallets.get(user_id, 0) < service["price"]:
        bot.answer_callback_query(call.id, "❌ Solde insuffisant.")
        return

    wallets[user_id] -= service["price"]
    admin_wallet["admin"] += service["price"]
    save_wallets(wallets)
    save_admin_wallet(admin_wallet)
    bot.answer_callback_query(call.id, f"✅ {service['name']} acheté !")

@bot.callback_query_handler(func=lambda call: call.data == "BACK")
def back_menu(call):
    start(call.message)

@bot.message_handler(commands=["admin"])
def admin_login(message):
    bot.send_message(message.chat.id, "🔐 Entrez le mot de passe admin :")
    bot.register_next_step_handler(message, check_admin_password)

def check_admin_password(message):
    if message.text.strip() == ADMIN_PASSWORD:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Créditer un utilisateur", callback_data="ADMIN_CREDIT"))
        markup.add(InlineKeyboardButton("🔁 Créditer mon solde", callback_data="ADMIN_SELF"))
        markup.add(InlineKeyboardButton("💼 Voir les soldes", callback_data="ADMIN_BAL"))
        bot.send_message(message.chat.id, "🔓 Panel Admin :", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ Mot de passe incorrect.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("ADMIN_"))
def admin_panel(call):
    if call.data == "ADMIN_CREDIT":
        bot.send_message(call.message.chat.id, "ID de l'utilisateur à créditer :")
        bot.register_next_step_handler(call.message, get_credit_user)
    elif call.data == "ADMIN_SELF":
        bot.send_message(call.message.chat.id, "💳 Montant à ajouter à ton solde admin :")
        bot.register_next_step_handler(call.message, get_credit_admin)
    elif call.data == "ADMIN_BAL":
        admin_solde = admin_wallet.get("admin", 0)
        bot.send_message(call.message.chat.id, f"💼 Solde Admin : {admin_solde}€")

def get_credit_user(message):
    try:
        uid = message.text.strip()
        if not uid.isdigit():
            return bot.send_message(message.chat.id, "❌ ID invalide.")
        bot.send_message(message.chat.id, "💰 Montant à créditer :")
        bot.register_next_step_handler(message, lambda m: credit_user_final(m, uid))
    except:
        bot.send_message(message.chat.id, "Erreur.")

def credit_user_final(message, uid):
    try:
        amount = float(message.text)
        wallets[uid] = wallets.get(uid, 0) + amount
        save_wallets(wallets)
        bot.send_message(message.chat.id, f"✅ {amount}€ crédité à l'utilisateur {uid}.")
    except:
        bot.send_message(message.chat.id, "Erreur.")

def get_credit_admin(message):
    try:
        amount = float(message.text)
        admin_wallet["admin"] += amount
        save_admin_wallet(admin_wallet)
        bot.send_message(message.chat.id, f"✅ {amount}€ ajouté à ton solde admin.")
    except:
        bot.send_message(message.chat.id, "Erreur.")

bot.infinity_polling()
