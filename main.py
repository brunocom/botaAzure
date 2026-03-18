#!/usr/bin/env python3
"""
================================================================================
BOT AVIS COMACCHIO - VERSIONE UNICO FILE
================================================================================
Prenotazione donazioni sangue - Genera automaticamente tutti i file necessari

ISTRUZIONI:
1. Modifica la riga BOT_TOKEN qui sotto con il tuo token da @BotFather
2. Carica questo file su PythonAnywhere
3. Esegui: python3 avis_bot_completo.py
================================================================================
"""

# =============================================================================
# CONFIGURAZIONE - MODIFICA SOLO QUESTA RIGA
# =============================================================================
BOT_TOKEN = "8771912446:AAHdbv3aRgCmpUyUpnZjX_uxiGZOBo4MvOY"  # <-- MODIFICA QUESTO!

# =============================================================================
# CONFIGURAZIONE AVANZATA (opzionale)
# =============================================================================
ADMIN_PASSWORD = "ARDUINOR3"
ORARIO_INIZIO = (7, 50)      # ore, minuti
ORARIO_FINE = (10, 40)       # ore, minuti
INTERVALLO_MINUTI = 5

# Nomi file
FILE_PRENOTAZIONI = "data/prenotazioni.json"
FILE_CONFIG = "data/config.json"
FILE_CSV = "data/prenotazioni.csv"
FILE_TXT = "data/prenotazioni.txt"

# Stati conversazione
(STATO_HOME, STATO_PASSWORD, STATO_NOME, STATO_COGNOME, STATO_ORA,
 STATO_ADMIN_PASS, STATO_ADMIN_MENU, STATO_NUOVA_DATA, STATO_NUOVA_PASSWORD) = range(9)

# =============================================================================
# GENERAZIONE FILE (eseguito automaticamente al primo avvio)
# =============================================================================

def crea_file_necessari():
    """Crea tutti i file necessari se non esistono"""
    import os
    
    # Crea directory data
    os.makedirs("data", exist_ok=True)
    
    # Crea config.json se non esiste
    if not os.path.exists(FILE_CONFIG):
        import json
        config_default = {
            "password_donatore": "1234",
            "data_donazione": None
        }
        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config_default, f, indent=2)
        print("✅ Creato config.json")
    
    # Crea prenotazioni.json se non esiste
    if not os.path.exists(FILE_PRENOTAZIONI):
        import json
        prenotazioni_default = {
            "prenotazioni": [],
            "data_donazione": None
        }
        with open(FILE_PRENOTAZIONI, "w", encoding="utf-8") as f:
            json.dump(prenotazioni_default, f, indent=2)
        print("✅ Creato prenotazioni.json")
    
    print("✅ Directory e file inizializzati")

# =============================================================================
# DATABASE
# =============================================================================

class Database:
    """Gestione dati prenotazioni"""
    
    def __init__(self):
        import json
        import os
        self.json = json
        self.os = os
        
        self.prenotazioni = []
        self.data_donazione = None
        self.password_donatore = "1234"
        self.carica()
    
    def carica(self):
        """Carica dati dai file"""
        if self.os.path.exists(FILE_PRENOTAZIONI):
            with open(FILE_PRENOTAZIONI, "r", encoding="utf-8") as f:
                dati = self.json.load(f)
                self.prenotazioni = dati.get("prenotazioni", [])
                self.data_donazione = dati.get("data_donazione")
        
        if self.os.path.exists(FILE_CONFIG):
            with open(FILE_CONFIG, "r", encoding="utf-8") as f:
                config = self.json.load(f)
                self.password_donatore = config.get("password_donatore", "1234")
                if not self.data_donazione:
                    self.data_donazione = config.get("data_donazione")
    
    def salva(self):
        """Salva dati su file"""
        # Salva JSON prenotazioni
        with open(FILE_PRENOTAZIONI, "w", encoding="utf-8") as f:
            self.json.dump({
                "prenotazioni": self.prenotazioni,
                "data_donazione": self.data_donazione
            }, f, ensure_ascii=False, indent=2)
        
        # Salva JSON config
        with open(FILE_CONFIG, "w", encoding="utf-8") as f:
            self.json.dump({
                "password_donatore": self.password_donatore,
                "data_donazione": self.data_donazione
            }, f, ensure_ascii=False, indent=2)
        
        self.esporta_csv()
        self.esporta_txt()
    
    def esporta_csv(self):
        """Esporta in CSV"""
        import csv
        with open(FILE_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Data", "Ora", "Cognome", "Nome"])
            for p in self.prenotazioni:
                writer.writerow([self.data_donazione, p["ora"], p["cognome"], p["nome"]])
    
    def esporta_txt(self):
        """Esporta in TXT"""
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
    
    def genera_orari(self):
        """Genera tutti gli orari"""
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
        """Restituisce orari disponibili"""
        return [o for o in self.genera_orari() if o["libero"]]
    
    def aggiungi_prenotazione(self, nome, cognome, orario):
        """Aggiunge prenotazione"""
        self.prenotazioni.append({"nome": nome, "cognome": cognome, "ora": orario})
        self.prenotazioni.sort(key=lambda x: x["ora"])
        self.salva()
    
    def verifica_password(self, pwd):
        return pwd == self.password_donatore
    
    def verifica_admin(self, pwd):
        return pwd == ADMIN_PASSWORD
    
    def reset(self, nuova_data, nuova_password=None):
        """Reset completo"""
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
# BOT TELEGRAM
# =============================================================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Istanza database
db = Database()

# TASTIERE
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
    return InlineKeyboardMarkup(tastiera)

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

# HANDLER
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Homepage"""
    testo = "🩸 *DONAZIONE AVIS COMACCHIO* 🩸\n\n"
    
    if db.data_donazione:
        testo += f"📅 *Data:* {db.data_donazione}\n"
        stats = db.statistiche()
        testo += f"⏰ Posti liberi: {stats['liberi']}/{stats['totali']}\n\n"
        testo += 'Clicca "PRENOTA DONAZIONE" per prenotare.'
    else:
        testo += "📅 *Data:* Da definire\n\n"
        testo += "Data non ancora impostata dall'amministratore."
    
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
    """Inizia prenotazione"""
    query = update.callback_query
    await query.answer()
    
    if not db.data_donazione:
        await query.edit_message_text(
            "⚠️ Data non impostata. Riprova più tardi.",
            reply_markup=tastiera_home()
        )
        return STATO_HOME
    
    if not db.orari_liberi():
        await query.edit_message_text(
            "⚠️ Orari esauriti! Grazie per l'interesse.",
            reply_markup=tastiera_home()
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
    """Verifica password"""
    pwd = update.message.text.strip()
    
    if not pwd.isdigit() or len(pwd) != 4:
        await update.message.reply_text(
            "❌ Deve essere di 4 cifre. Riprova:", parse_mode="Markdown"
        )
        return STATO_PASSWORD
    
    if not db.verifica_password(pwd):
        await update.message.reply_text(
            "❌ Password errata. Riprova:", parse_mode="Markdown"
        )
        return STATO_PASSWORD
    
    await update.message.reply_text(
        "✅ Corretta!\n\nInserisci il tuo *NOME*:", parse_mode="Markdown"
    )
    return STATO_NOME

async def ricevi_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Riceve nome"""
    context.user_data["nome"] = update.message.text.strip()
    await update.message.reply_text(
        f"Nome: *{context.user_data['nome']}*\n\nOra il *COGNOME*:",
        parse_mode="Markdown"
    )
    return STATO_COGNOME

async def ricevi_cognome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Riceve cognome, mostra orari"""
    context.user_data["cognome"] = update.message.text.strip()
    await update.message.reply_text(
        f"✓ {context.user_data['nome']} {context.user_data['cognome']}\n\n"
        "Seleziona l'*orario*:",
        reply_markup=tastiera_orari(), parse_mode="Markdown"
    )
    return STATO_ORA

async def ricevi_orario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce scelta orario"""
    query = update.callback_query
    await query.answer()
    
    orario = query.data.replace("ora_", "")
    context.user_data["orario"] = orario
    
    # Verifica disponibilità
    if any(p["ora"] == orario for p in db.prenotazioni):
        await query.edit_message_text(
            "⚠️ Orario appena prenotato! Scegli altro:",
            reply_markup=tastiera_orari()
        )
        return STATO_ORA
    
    await query.edit_message_text(
        "🩸 *CONFERMA* 🩸\n\n"
        f"📅 {db.data_donazione}\n"
        f"⏰ {orario}\n"
        f"👤 {context.user_data['cognome']} {context.user_data['nome']}\n\n"
        "Confermi?",
        reply_markup=tastiera_conferma(), parse_mode="Markdown"
    )
    return STATO_ORA

async def conferma(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Salva prenotazione"""
    query = update.callback_query
    await query.answer()
    
    nome = context.user_data["nome"]
    cognome = context.user_data["cognome"]
    orario = context.user_data["orario"]
    
    db.aggiungi_prenotazione(nome, cognome, orario)
    
    await query.edit_message_text(
        "✅ *PRENOTAZIONE AVVENUTA* ✅\n\n"
        f"🩸 Grazie {nome} {cognome}!\n"
        f"📅 {db.data_donazione} alle {orario}\n\n"
        "Ti aspettiamo! Porta un documento.",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ADMIN
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Accesso admin"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔐 *AREA ADMIN* 🔐\n\nInserisci password:",
        parse_mode="Markdown"
    )
    return STATO_ADMIN_PASS

async def verifica_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica password admin"""
    if not db.verifica_admin(update.message.text.strip()):
        await update.message.reply_text(
            "❌ Errata.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Home", callback_data="home")]
            ])
        )
        return STATO_ADMIN_PASS
    
    await menu_admin(update, context)
    return STATO_ADMIN_MENU

async def menu_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu admin"""
    stats = db.statistiche()
    testo = (
        "🔐 *ADMIN* 🔐\n\n"
        f"📅 {db.data_donazione or 'Non impostata'}\n"
        f"🔑 Password: {db.password_donatore}\n"
        f"📊 {stats['occupati']}/{stats['totali']} prenotati\n\n"
        "Scegli azione:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            testo, reply_markup=tastiera_admin(), parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            testo, reply_markup=tastiera_admin(), parse_mode="Markdown"
        )

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Visualizza prenotazioni"""
    query = update.callback_query
    await query.answer()
    
    if not db.prenotazioni:
        await query.edit_message_text(
            "📋 Nessuna prenotazione.",
            reply_markup=tastiera_admin()
        )
        return STATO_ADMIN_MENU
    
    testo = f"📋 *{db.data_donazione}*\n\n"
    for i, p in enumerate(db.prenotazioni, 1):
        testo += f"{i}. `{p['ora']}` - {p['cognome']} {p['nome']}\n"
    
    await query.edit_message_text(testo, reply_markup=tastiera_admin(), parse_mode="Markdown")
    return STATO_ADMIN_MENU

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE, tipo):
    """Scarica file"""
    query = update.callback_query
    await query.answer()
    
    import os
    percorso = FILE_CSV if tipo == "csv" else FILE_TXT
    nome = f"prenotazioni_{db.data_donazione}.{tipo}"
    
    if not os.path.exists(percorso):
        await query.edit_message_text(
            "⚠️ Nessun file.", reply_markup=tastiera_admin()
        )
        return STATO_ADMIN_MENU
    
    with open(percorso, "rb") as f:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=f, filename=nome,
            caption=f"📎 {db.data_donazione}"
        )
    
    await menu_admin(update, context)
    return STATO_ADMIN_MENU

async def reset_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inizia reset"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔄 *RESET* 🔄\n\nNuova data (GG-MM-AAAA):\n\n"
        "⚠️ Elimina tutte le prenotazioni!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Annulla", callback_data="admin_back")]
        ]),
        parse_mode="Markdown"
    )
    return STATO_NUOVA_DATA

async def ricevi_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Riceve nuova data"""
    context.user_data["nuova_data"] = update.message.text.strip()
    await update.message.reply_text(
        f"Data: *{context.user_data['nuova_data']}*\n\n"
        "Nuova password 4 cifre (o 'no' per tenere attuale):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Annulla", callback_data="admin_back")]
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
            await update.message.reply_text("❌ 4 cifre! Riprova:")
            return STATO_NUOVA_PASSWORD
        db.reset(nuova_data, nuova_pwd)
    else:
        db.reset(nuova_data)
    
    await update.message.reply_text(
        f"✅ Reset!\n📅 {nuova_data}\n🔑 {db.password_donatore}",
        reply_markup=tastiera_admin()
    )
    return STATO_ADMIN_MENU

async def cambia_pass_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inizia cambio password"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔑 Nuova password 4 cifre:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Annulla", callback_data="admin_back")]
        ]),
        parse_mode="Markdown"
    )
    return STATO_NUOVA_PASSWORD

async def cambia_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cambia password"""
    nuova = update.message.text.strip()
    if not nuova.isdigit() or len(nuova) != 4:
        await update.message.reply_text("❌ 4 cifre! Riprova:")
        return STATO_NUOVA_PASSWORD
    
    db.cambia_password(nuova)
    await update.message.reply_text(
        f"✅ Nuova: `{nuova}`",
        reply_markup=tastiera_admin(), parse_mode="Markdown"
    )
    return STATO_ADMIN_MENU

# CALLBACK ROUTER
async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gestisce tutti i callback"""
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

# MAIN

def main():
    """Avvia il bot"""
    import os
    
    # Verifica token
    if BOT_TOKEN == "INSERISCI_IL_TUO_TOKEN_QUI":
        print("=" * 60)
        print("❌ ERRORE: Devi inserire il BOT_TOKEN nel file!")
        print("=" * 60)
        print("\n1. Vai su Telegram -> @BotFather")
        print("2. Crea un nuovo bot con /newbot")
        print("3. Copia il token e incollalo nella riga:")
        print('   BOT_TOKEN = "il_tuo_token_qui"')
        print("=" * 60)
        return
    
    # Crea file necessari
    print("🚀 Avvio Bot Avis Comacchio...")
    crea_file_necessari()
    
    # Crea applicazione
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler
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
    
    print("✅ Bot avviato! Premi Ctrl+C per fermare")
    print(f"📅 Data attuale: {db.data_donazione or 'Non impostata'}")
    print(f"🔑 Admin password: {ADMIN_PASSWORD}")
    print(f"🔑 Donatore password: {db.password_donatore}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()