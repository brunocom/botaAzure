#!/usr/bin/env python3
"""
================================================================================
BOT AVIS COMACCHIO - VERSIONE PER AZURE APP SERVICE
================================================================================
Prenotazione donazioni sangue - File unico, compatibile con Azure

Modifiche principali:
- Cartella dati spostata in /home/data (persistente su Azure)
- Rimosso uso della cartella locale "data/"
================================================================================
"""

import os
import json
import csv
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)

# =============================================================================
# CONFIGURAZIONE
# =============================================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # <-- Inserisci su Azure App Service

ADMIN_PASSWORD = "ARDUINOR3"
ORARIO_INIZIO = (7, 50)
ORARIO_FINE = (10, 40)
INTERVALLO_MINUTI = 5

# Cartella persistente su Azure
BASE_DIR = "/home/data"
os.makedirs(BASE_DIR, exist_ok=True)

FILE_PRENOTAZIONI = f"{BASE_DIR}/prenotazioni.json"
FILE_CONFIG = f"{BASE_DIR}/config.json"
FILE_CSV = f"{BASE_DIR}/prenotazioni.csv"
FILE_TXT = f"{BASE_DIR}/prenotazioni.txt"

# Stati conversazione
(STATO_HOME, STATO_PASSWORD, STATO_NOME, STATO_COGNOME, STATO_ORA,
 STATO_ADMIN_PASS, STATO_ADMIN_MENU, STATO_NUOVA_DATA, STATO_NUOVA_PASSWORD) = range(9)

# =============================================================================
# GENERAZIONE FILE
# =============================================================================

def crea_file_necessari():
    """Crea file iniziali se non esistono"""
    if not os.path.exists(FILE_CONFIG):
        config_default = {
            "password_donatore": "1234",
            "data_donazione": None
        }
        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config_default, f, indent=2)

    if not os.path.exists(FILE_PRENOTAZIONI):
        prenotazioni_default = {
            "prenotazioni": [],
            "data_donazione": None
        }
        with open(FILE_PRENOTAZIONI, "w", encoding="utf-8") as f:
            json.dump(prenotazioni_default, f, indent=2)

# =============================================================================
# DATABASE
# =============================================================================

class Database:
    def __init__(self):
        self.prenotazioni = []
        self.data_donazione = None
        self.password_donatore = "1234"
        self.carica()

    def carica(self):
        if os.path.exists(FILE_PRENOTAZIONI):
            with open(FILE_PRENOTAZIONI, "r", encoding="utf-8") as f:
                dati = json.load(f)
                self.prenotazioni = dati.get("prenotazioni", [])
                self.data_donazione = dati.get("data_donazione")

        if os.path.exists(FILE_CONFIG):
            with open(FILE_CONFIG, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.password_donatore = config.get("password_donatore", "1234")
                if not self.data_donazione:
                    self.data_donazione = config.get("data_donazione")

    def salva(self):
        with open(FILE_PRENOTAZIONI, "w", encoding="utf-8") as f:
            json.dump({
                "prenotazioni": self.prenotazioni,
                "data_donazione": self.data_donazione
            }, f, ensure_ascii=False, indent=2)

        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            json.dump({
                "password_donatore": self.password_donatore,
                "data_donazione": self.data_donazione
            }, f, ensure_ascii=False, indent=2)

        self.esporta_csv()
        self.esporta_txt()

    def esporta_csv(self):
        with open(FILE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Data", "Ora", "Cognome", "Nome"])
            for p in self.prenotazioni:
                writer.writerow([self.data_donazione, p["ora"], p["cognome"], p["nome"]])

    def esporta_txt(self):
        with open(FILE_TXT, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("      PRENOTAZIONI DONAZIONI AVIS COMACCHIO\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Data donazione: {self.data_donazione}\n")
            f.write(f"Totale prenotazioni: {len(self.prenotazioni)}\n\n")
            f.write(f"{'Ora':<10} {'Cognome':<20} {'Nome':<20}\n")
            f.write("-" * 60 + "\n")
            for p in self.prenotazioni:
                f.write(f"{p['ora']:<10} {p['cognome']:<20} {p['nome']:<20}\n")
            f.write("-" * 60 + "\n")
            
            f.write("-" * 60 + "\n")

    def genera_orari(self):
        orari = []
        ora, minuto = ORARIO_INIZIO
        while (ora, minuto) <= ORARIO_FINE:
            orario_str = f"{ora:02d}:{minuto:02d}"
            occupato = any(p["ora"] == orario_str for p in self.prenotazioni)
            orari.append({"ora": orario_str, "libero": not occupato})
            minuto += INTERVALLO_MINUTI
            if minuto >= 60:
                minuto -= 60
                ora += 1
        return orari

    def orari_liberi(self):
        return [o for o in self.genera_orari() if o["libero"]]

    def aggiungi_prenotazione(self, nome, cognome, orario):
        self.prenotazioni.append({"nome": nome, "cognome": cognome, "ora": orario})
        self.prenotazioni.sort(key=lambda x: x["ora"])
        self.salva()

    def verifica_password(self, pwd):
        return pwd == self.password_donatore

    def verifica_admin(self, pwd):
        return pwd == ADMIN_PASSWORD

    def reset(self, nuova_data, nuova_password=None):
        self.prenotazioni = []
        self.data_donazione = nuova_data
        if nuova_password:
            self.password_donatore = nuova_password
        self.salva()

    def cambia_password(self, nuova_password):
        self.password_donatore = nuova_password
        self.salva()

    def statistiche(self):
        totali = len(self.genera_orari())
        occupati = len(self.prenotazioni)
        return {"totali": totali, "occupati": occupati, "liberi": totali - occupati}

# =============================================================================
# LOGGING
# =============================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# =============================================================================
# TASTIERE
# =============================================================================

def tastiera_home():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🩸 PRENOTA DONAZIONE", callback_data="prenota")],
        [InlineKeyboardButton("🔐 Area Amministratore", callback_data="admin")]
    ])

def tastiera_orari():
    orari = db.orari_liberi()
    if not orari:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⚠️ Nessun orario disponibile", callback_data="none")],
            [InlineKeyboardButton("🔙 Torna indietro", callback_data="home")]
        ])
    tastiera = []
    riga = []
    for o in orari:
        riga.append(InlineKeyboardButton(o["ora"], callback_data=f"ora_{o['ora']}"))
        if len(riga) == 3:
            tastiera.append(riga)
            riga = []
    if riga:
        tastiera.append(riga)
    tastiera.append([InlineKeyboardButton("🔙 Torna indietro", callback_data="home")])
    return tastiera

def tastiera_admin():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Visualizza Prenotazioni", callback_data="view")],
        [InlineKeyboardButton("📥 Scarica CSV", callback_data="csv"),
         InlineKeyboardButton("📄 Scarica TXT", callback_data="txt")],
        [InlineKeyboardButton("🔄 Nuova Data/Reset", callback_data="reset")],
        [InlineKeyboardButton("🔑 Cambia Password", callback_data="cambiapass")],
        [InlineKeyboardButton("🔙 Logout", callback_data="home")]
    ])

def tastiera_conferma():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Conferma", callback_data="conferma"),
         InlineKeyboardButton("❌ Annulla", callback_data="home")]
    ])

# =============================================================================
# HANDLER
# =============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    testo = "🩸 *DONAZIONE AVIS COMACCHIO* 🩸\n\n"
    if db.data_donazione:
        stats = db.statistiche()
        testo += f"📅 *Data:* {db.data_donazione}\n"
        testo += f"⏰ Posti liberi: {stats['liberi']}/{stats['totali']}\n\n"
        testo += 'Clicca "PRENOTA DONAZIONE" per prenotare.'
    else:
        testo += "📅 *Data:* Da definire\n\nData non ancora impostata."

    if update.callback_query:
        await update.callback_query.edit_message_text(
            testo, reply_markup=tastiera_home(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            testo, reply_markup=tastiera_home(), parse_mode="Markdown"
        )
    return STATO_HOME

async def prenota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not db.data_donazione:
        await query.edit_message_text(
            "⚠️ Data non impostata.", reply_markup=tastiera_home()
        )
        return STATO_HOME

    if not db.orari_liberi():
        await query.edit_message_text(
            "⚠️ Orari esauriti!", reply_markup=tastiera_home()
        )
        return STATO_HOME

    await query.edit_message_text(
        "🩸 *PRENOTAZIONE* 🩸\n\n"
        f"📅 Data: {db.data_donazione}\n\n"
        "Inserisci la *password di 4 cifre*:",
        parse_mode="Markdown"
    )
    return STATO_PASSWORD

async def ricevi_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pwd = update.message.text.strip()

    if not pwd.isdigit() or len(pwd) != 4:
        await update.message.reply_text("❌ Deve essere di 4 cifre. Riprova:")
        return STATO_PASSWORD

    if not db.verifica_password(pwd):
        await update.message.reply_text("❌ Password errata. Riprova:")
        return STATO_PASSWORD

    await update.message.reply_text("✅ Corretta!\n\nInserisci il tuo *NOME*:", parse_mode="Markdown")
    return STATO_NOME

async def ricevi_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text(
        f"Nome: *{context.user_data['nome']}*\n\nOra il *COGNOME*:",
        parse_mode="Markdown"
    )
    return STATO_COGNOME

async def ricevi_cognome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cognome"] = update.message.text.strip()
    await update.message.reply_text(
        f"✓ {context.user_data['nome']} {context.user_data['cognome']}\n\n"
        "Seleziona l'*orario*:",
        reply_markup=tastiera_orari(), parse_mode="Markdown"
    )
    return STATO_ORA
    
    
    InlineKeyboardButton("🔙 Annulla", callback_data="admin_back")]
        ]),
        parse_mode="Markdown"
    )
    return STATO_NUOVA_PASSWORD

async def completa_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Completa reset"""
    nuova_pwd = update.message.text.strip()
    nuova_data = context.user_data["nuova_data"]

    if nuova_pwd.lower() != "no":
        if not nuova_pwd.isdigit() or len(nuova_pwd) != 4:
            await update.message.reply_text("❌ Deve essere di 4 cifre. Riprova:")
            return STATO_NUOVA_PASSWORD
        db.reset(nuova_data, nuova_pwd)
    else:
        db.reset(nuova_data)

    await update.message.reply_text(
        f"✅ Reset completato!\n📅 {nuova_data}\n🔑 Password donatore: {db.password_donatore}",
        reply_markup=tastiera_admin()
    )
    return STATO_ADMIN_MENU

async def cambia_pass_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 Inserisci nuova password (4 cifre):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Annulla", callback_data="admin_back")]
        ]),
        parse_mode="Markdown"
    )
    return STATO_NUOVA_PASSWORD

async def cambia_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nuova = update.message.text.strip()
    if not nuova.isdigit() or len(nuova) != 4:
        await update.message.reply_text("❌ Deve essere di 4 cifre. Riprova:")
        return STATO_NUOVA_PASSWORD

    db.cambia_password(nuova)
    await update.message.reply_text(
        f"✅ Nuova password impostata: `{nuova}`",
        reply_markup=tastiera_admin(),
        parse_mode="Markdown"
    )
    return STATO_ADMIN_MENU

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "home":
        return await start(update, context)
    elif data == "prenota":
        return await prenota(update, context)
    elif data == "admin":
        return await admin(update, context)
    elif data == "admin_back":
        return await menu_admin(update, context)
    elif data == "view":
        return await view(update, context)
    elif data == "csv":
        return await download(update, context, "csv")
    elif data == "txt":
        return await download(update, context, "txt")
    elif data == "reset":
        return await reset_start(update, context)
    elif data == "cambiapass":
        return await cambia_pass_start(update, context)
    elif data == "conferma":
        return await conferma(update, context)
    elif data.startswith("ora_"):
        return await ricevi_orario(update, context)

    return STATO_HOME

# =============================================================================
# MAIN
# =============================================================================

def main():
    if not BOT_TOKEN:
        print("❌ ERRORE: Variabile d'ambiente BOT_TOKEN non trovata!")
        return

    print("🚀 Avvio Bot Avis Comacchio su Azure...")
    crea_file_necessari()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            STATO_HOME: [CallbackQueryHandler(callback_router)],
            STATO_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_password)],
            STATO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_nome)],
            STATO_COGNOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_cognome)],
            STATO_ORA: [CallbackQueryHandler(callback_router)],
            STATO_ADMIN_PASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, verifica_admin),
                CallbackQueryHandler(callback_router)
            ],
            STATO_ADMIN_MENU: [CallbackQueryHandler(callback_router)],
            STATO_NUOVA_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_data),
                CallbackQueryHandler(callback_router)
            ],
            STATO_NUOVA_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, completa_reset),
                CallbackQueryHandler(callback_router)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)

    print("✅ Bot avviato correttamente!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
            