# Deployment & Rollback — MOEX Scalper Dashboard

## Branch-Strategie

```
main        ← Production (stable, deployed auf Render)
  └── dev   ← Testing (neue Features zuerst hier testen)
       └── feature/*  ← Einzelne Features/Experimente
```

### Regeln

| Branch | Wann nutzen | Deploy |
|--------|------------|--------|
| `main` | Nur stabile, getestete Änderungen | → Render Production |
| `dev` | Neue Features, Bugfixes testen | → Lokal oder Render Staging |
| `feature/*` | Experimente, große Umbauten | → Nur lokal |

---

## Normaler Workflow (Feature entwickeln)

```bash
# 1. Dev-Branch auschecken und aktualisieren
git checkout dev
git pull origin dev

# 2. Feature-Branch erstellen
git checkout -b feature/neue-charts

# 3. Entwickeln + committen
git add .
git commit -m "feat: neue Chart-Option hinzugefügt"

# 4. Lokal testen
python server.py
# → Browser: http://localhost:8081/scalper-dashboard.html
# → Health:  http://localhost:8081/health

# 5. Wenn alles funktioniert → in dev mergen
git checkout dev
git merge feature/neue-charts
git push origin dev

# 6. Auf Render Staging testen (falls eingerichtet)
# → https://moex-staging.onrender.com/health

# 7. Wenn stabil → in main mergen und deployen
git checkout main
git merge dev
git push origin main
# → Render deployed automatisch
```

---

## 🔴 ROLLBACK — Wenn Production kaputt ist

### Option 1: Schneller Rollback (letzten stabilen Stand wiederherstellen)

```bash
# 1. Commit-History ansehen
git log --oneline -10

# Ausgabe z.B.:
# e26a35b Improve chart Y-axis scaling     ← KAPUTT
# fd983dd server: add start/stop logging   ← STABIL
# 2604b48 extract shared CSS               ← STABIL

# 2. Zum letzten stabilen Commit zurück
git checkout main
git revert e26a35b          # Erstellt einen neuen Commit, der die Änderung rückgängig macht
git push origin main        # → Render deployed den reverteten Stand
```

### Option 2: Hard Rollback (zu einem bestimmten Commit zurückspringen)

```bash
# 1. Stabilen Commit finden
git log --oneline -10

# 2. Main auf diesen Stand zurücksetzen
git checkout main
git reset --hard fd983dd    # ACHTUNG: Alle Commits danach gehen verloren (lokal)

# 3. Force-Push (ACHTUNG: überschreibt History auf GitHub)
git push origin main --force
```

### Option 3: Dev als Rettung (wenn main komplett kaputt ist)

```bash
# Wenn main nicht mehr zu retten ist:
git checkout main
git reset --hard dev        # Main = Dev-Stand
git push origin main --force
```

---

## 🔍 Production testen / debuggen

### Health-Check (ohne Login)

```bash
# Production
curl https://moex-scalper-dashboard.onrender.com/health

# Lokal
curl http://localhost:8081/health
```

Antwort:
```json
{
  "status": "ok",
  "uptime": "2h 15m 30s",
  "api_key": "configured",
  "auth": "enabled",
  "port": 8081,
  "python": "3.11.5",
  "timestamp": "2026-01-15T14:30:00"
}
```

**Wichtig:** Wenn `"api_key": "missing"` → MOEX_API_KEY Umgebungsvariable fehlt auf Render!

### Render Logs checken

1. Render Dashboard → Service → **Logs**
2. Nach `[ERROR]` suchen
3. Nach `[AUTH]` suchen (Login-Probleme)

### Lokal mit Production-Settings testen

```bash
# Windows (CMD):
set ACCESS_TOKEN=testpass
set MOEX_API_KEY=eyJhbGci...
python server.py

# Windows (PowerShell):
$env:ACCESS_TOKEN="testpass"
$env:MOEX_API_KEY="eyJhbGci..."
python server.py
```

---

## 🛡️ Preventiv: Render Staging Environment (empfohlen)

Einen **zweiten Render-Service** für Testing aufsetzen:

1. Render Dashboard → **"New +"** → **"Web Service"**
2. Gleiches GitHub Repo verbinden
3. **Branch: `dev`** einstellen (statt `main`)
4. Name: `moex-staging`
5. Gleiche ENV-Variablen wie Production setzen
6. Deploy!

**Ergebnis:**
- `main` Branch → `moex-scalper-dashboard.onrender.com` (Production)
- `dev` Branch → `moex-staging.onrender.com` (Testing)

→ Änderungen in `dev` werden automatisch auf Staging deployed und können getestet werden, **bevor** sie auf Production gehen.

---

## 📋 Checkliste vor jedem Deploy

- [ ] `python server.py` läuft lokal ohne Fehler
- [ ] `/health` gibt `"api_key": "configured"` zurück
- [ ] Dashboard lädt und zeigt Daten
- [ ] Login funktioniert (mit `ACCESS_TOKEN`)
- [ ] Änderungen sind in `dev` gemerged und getestet
- [ ] Commit-Message beschreibt die Änderung klar

---

## 🔧 Nützliche Git-Befehle

```bash
# Was hat sich geändert seit letztem Deploy?
git log main..dev --oneline

# Welche Dateien haben sich geändert?
git diff main..dev --stat

# Einen bestimmten Commit anschauen
git show fd983dd

# Alles auf den letzten Commit-Stand zurücksetzen (lokale Änderungen verwerfen)
git checkout .
git clean -fd
```
