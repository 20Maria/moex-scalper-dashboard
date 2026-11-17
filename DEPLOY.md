# Deployment-Anleitung: MOEX Scalper Dashboard auf Render

## Voraussetzungen

- **GitHub Account** ✅ (hast du)
- **Render Account** → [render.com](https://render.com) (kostenlos registrieren mit GitHub)
- **MOEX API Key** (dein Algopack JWT-Token)

---

## Schritt 1: GitHub Repository erstellen

```bash
# Im Projekt-Verzeichnis:
cd "C:\Users\MKA02289\masha\my projects\learning stuff\moex-scalper-dashboard"

git init
git add .
git commit -m "Initial commit: MOEX Scalper Dashboard"

# Auf GitHub ein neues Repo erstellen (z.B. "moex-scalper-dashboard")
# Dann:
git remote add origin https://github.com/DEIN_USERNAME/moex-scalper-dashboard.git
git branch -M main
git push -u origin main
```

---

## Schritt 2: Auf Render deployen

### Option A: Blueprint (One-Click)

1. Gehe auf [render.com](https://render.com) und logge dich ein
2. Klicke **"New +"** → **"Blueprint Service"**
3. Verbinde dein GitHub Repository
4. Render erkennt die `render.yaml` automatisch
5. Du wirst nach den ENV-Variablen gefragt:
   - **MOEX_API_KEY**: Dein MOEX Algopack JWT-Token
   - **ACCESS_TOKEN**: Ein Passwort deiner Wahl (z.B. `meingeheimespasswort123`)
6. Klicke **"Apply"** → Deploy startet

### Option B: Manuell

1. Gehe auf [render.com](https://render.com) → **"New +"** → **"Web Service"**
2. Verbinde dein GitHub Repository
3. Konfiguration:
   - **Name**: `moex-scalper-dashboard`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python server.py`
   - **Instance Type**: `Free`
4. Unter **"Environment Variables"** hinzufügen:
   | Key | Value |
   |---|---|
   | `MOEX_API_KEY` | `eyJhbGci...` (dein MOEX JWT) |
   | `ACCESS_TOKEN` | `deinpasswort` |
5. **"Create Web Service"** klicken

---

## Schritt 3: Dashboard teilen

Nach dem Deploy (ca. 2-3 Min) bekommst du eine URL wie:

```
https://moex-scalper-dashboard.onrender.com
```

**Link zum Teilen:**

```
https://moex-scalper-dashboard.onrender.com/login
```

Die Person gibt das Passwort ein (dein `ACCESS_TOKEN`) und wird zum Dashboard weitergeleitet.
Das Cookie bleibt **30 Tage** gültig — danach muss das Passwort erneut eingegeben werden.

---

## Hinweise

### Render Free Tier Limitierungen
- Der Server **schläft nach 15 Min Inaktivität** ein
- Nächster Aufruf dauert **~30 Sekunden** (Cold Start)
- Reicht völlig für gelegentliche Nutzung

### API Key aktualisieren
1. Render Dashboard → Dein Service → **"Environment"**
2. `MOEX_API_KEY` Wert ändern
3. **"Save Changes"** → automatischer Redeploy

### Logs ansehen
Render Dashboard → Dein Service → **"Logs"**

### Custom Domain (optional)
Render Dashboard → Dein Service → **"Domains"** → eigene Domain hinzufügen

---

## Lokale Entwicklung (weiterhin möglich)

```bash
# Ohne Passwortschutz (lokales Dev):
python server.py

# Mit Passwortschutz (wie Production):
ACCESS_TOKEN=testpass MOEX_API_KEY=dein_key python server.py
```

Auf Windows:
```cmd
set ACCESS_TOKEN=testpass
set MOEX_API_KEY=dein_key
python server.py
```
