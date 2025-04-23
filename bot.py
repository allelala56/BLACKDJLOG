import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
import os
from datetime import datetime

BOT_TOKEN = "7115175533:AAHcFYSUzqagDMuxOttx4jLUNCDdlVyvtZo"
ADMIN_PASSWORD = "jamais007"
WALLET_FILE = "wallet.json"

bot = telebot.TeleBot(BOT_TOKEN)

# Chargement des soldes utilisateurs
if os.path.exists(WALLET_FILE):
    with open(WALLET_FILE, "r") as f:
        user_wallets = json.load(f)
else:
    user_wallets = {}

def save_wallets():
    with open(WALLET_FILE, "w") as f:
        json.dump(user_wallets, f)

# Clavier principal utilisateur
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("🛍 Services"))
main_menu.add(KeyboardButton("💼 Mon Portefeuille"))

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.from_user.id)
    if user_id not in user_wallets:
        user_wallets[user_id] = 0
        save_wallets()
    bot.send_message(message.chat.id, "Bienvenue sur BLACKDJLOG. Choisis une option :", reply_markup=main_menu)

@bot.message_handler(func=lambda m: m.text == "🛍 Services")
def services(message):
    now = datetime.now()
    cc_access = "✅ Disponible" if now.hour == 0 else "⛔ Disponible à minuit"
    msg = (
        "<b>Services :</b>
"
        "1. Spam lien : 25€
"
        "2. Tek Prixtel : 50€
"
        "3. Logs : 10€
"
        "4. MEXT : 50€
"
        "5. ML : 5€/k
"
        "6. NL ciblée : 5€/k
"
        f"7. Boîte de CC : 280€ → {cc_access}"
    )
    bot.send_message(message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text == "💼 Mon Portefeuille")
def show_wallet(message):
    user_id = str(message.from_user.id)
    solde = user_wallets.get(user_id, 0)
    bot.send_message(message.chat.id, f"💰 Ton solde actuel : {solde}€")

@bot.message_handler(commands=['admin'])
def admin_login(message):
    bot.send_message(message.chat.id, "Entrez le mot de passe admin :")
    bot.register_next_step_handler(message, check_password)

def check_password(message):
    if message.text == ADMIN_PASSWORD:
        admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
        admin_menu.add(KeyboardButton("📥 Créditer un utilisateur"))
        bot.send_message(message.chat.id, "✅ Accès admin autorisé.", reply_markup=admin_menu)
        bot.register_next_step_handler(message, handle_admin_menu)
    else:
        bot.send_message(message.chat.id, "❌ Mot de passe incorrect.")

def handle_admin_menu(message):
    if message.text == "📥 Créditer un utilisateur":
        bot.send_message(message.chat.id, "Envoie l'ID Telegram de l'utilisateur à créditer :")
        bot.register_next_step_handler(message, get_user_id)
    else:
        bot.send_message(message.chat.id, "Commande admin inconnue.")

def get_user_id(message):
    admin_id = message.chat.id
    target_id = message.text
    if target_id.isdigit():
        bot.send_message(admin_id, f"Montant à créditer pour l'utilisateur {target_id} :")
        bot.register_next_step_handler_by_chat_id(admin_id, lambda m: credit_user(m, target_id))
    else:
        bot.send_message(admin_id, "❌ ID invalide.")

def credit_user(message, user_id):
    try:
        amount = float(message.text)
        user_wallets[user_id] = user_wallets.get(user_id, 0) + amount
        save_wallets()
        bot.send_message(message.chat.id, f"✅ {amount}€ crédités à l'utilisateur {user_id}.")
    except:
        bot.send_message(message.chat.id, "❌ Montant invalide.")

bot.infinity_polling()
