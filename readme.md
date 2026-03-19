# Bot Avis Comacchio - Azure Version

Questo repository contiene il bot Telegram per la gestione delle prenotazioni AVIS Comacchio, ottimizzato per Azure App Service.

## Deploy su Azure

### 1. Impostazioni App Service
- Runtime: Python 3.10
- Startup Command:
  python main.py

### 2. Variabili d’ambiente
Aggiungi in Configuration → Application Settings:

- BOT_TOKEN = <token del bot>

### 3. File salvati
I file JSON, CSV e TXT vengono salvati nella cartella persistente:
- /home/data

### 4. Librerie richieste
Sono elencate in requirements.txt