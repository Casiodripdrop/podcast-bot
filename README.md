# Deeptech Daily — Auto-Podcast

Generiert täglich ein ~5-Minuten Podcast-Briefing über Deeptech-, Robotics- und
Space-Startups, hostet es selbst (GitHub Pages) und liefert es als Apple-Podcasts-
abonnierbaren RSS-Feed aus.

## Wie es funktioniert
1. `fetch_news.py` holt Artikel aus den RSS-Feeds in `feeds.json` und filtert nach Keywords.
2. `generate_script.py` schickt die Artikel an die Claude API → 5-Min-Sprechskript.
3. `generate_audio.py` wandelt das Skript per OpenAI TTS in eine MP3.
4. `build_feed.py` schreibt die neue Episode in `docs/episodes.json` und baut
   `docs/feed.xml` (das ist der Podcast-RSS-Feed) neu.
5. GitHub Actions (`.github/workflows/daily-podcast.yml`) führt das jeden Tag
   automatisch aus und committet die neue MP3 + den Feed zurück ins Repo.
6. GitHub Pages serviert den `docs/`-Ordner öffentlich → das ist deine Podcast-URL.

## Setup (einmalig, ca. 15 Minuten)

### 1. API-Keys holen
- **Anthropic**: Account auf https://console.anthropic.com → API Keys → neuen Key erstellen.
  (Achtung: das ist ein separater API-Key, nicht dein claude.ai-Login. Es fallen
  kleine Pay-as-you-go-Kosten an, ca. $0.01–0.03 pro Episode.)
- **OpenAI**: Account auf https://platform.openai.com → API Keys → neuen Key erstellen.
  (TTS kostet ca. $0.015 pro 1000 Zeichen → eine 5-Min-Episode ≈ $0.06.)

### 2. Eigenes GitHub-Repo anlegen
- Neues **privates oder öffentliches** Repo erstellen, z. B. `podcast-bot`.
- Diesen ganzen Ordner-Inhalt hochladen/pushen.

### 3. GitHub Pages aktivieren
- Repo → Settings → Pages → "Deploy from branch" → Branch `main`, Ordner `/docs`.
- Nach ein paar Minuten ist deine Feed-URL erreichbar unter:
  `https://<dein-username>.github.io/<repo-name>/feed.xml`

### 4. Secrets & Variable im Repo eintragen
- Repo → Settings → Secrets and variables → Actions:
  - **Secrets**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
  - **Variables**: `PODCAST_BASE_URL` = `https://<dein-username>.github.io/<repo-name>`

### 5. Ersten Lauf testen
- Repo → Actions → "Daily Podcast" → "Run workflow" (manueller Trigger).
- Nach ein paar Minuten sollte eine neue `episode-YYYY-MM-DD.mp3` in `docs/`
  liegen und `docs/feed.xml` eine neue Episode enthalten.

### 6. Im Podcast-Player abonnieren
- **Apple Podcasts (iOS/Mac)**: App öffnen → oben rechts "..." bzw. unter
  "Library" → "Follow a Show by URL" → deine Feed-URL einfügen.
- **Spotify**: Spotify unterstützt das direkte Abonnieren beliebiger privater
  RSS-Feeds in der normalen App nicht mehr zuverlässig. Praktikabler Weg: den
  Feed zusätzlich (kostenlos) über "Spotify for Podcasters" als "unlisted"
  Show einreichen — sag Bescheid, falls du dabei Hilfe willst.

## Anpassen
- **Quellen ändern**: `feeds.json` bearbeiten.
- **Keywords ändern**: `KEYWORDS`-Liste in `fetch_news.py`.
- **Stimme ändern**: `voice="onyx"` in `generate_audio.py` (Optionen: alloy,
  echo, fable, onyx, nova, shimmer).
- **Häufigkeit ändern**: `cron`-Zeile im Workflow (z. B. `0 5 */2 * *` für jeden
  zweiten Tag).
- **Sprechdauer ändern**: Wortzahl-Vorgabe im Prompt in `generate_script.py`.

## Lokal testen (optional, bevor du es automatisierst)
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export PODCAST_BASE_URL=https://<dein-username>.github.io/<repo-name>
python main.py
```
