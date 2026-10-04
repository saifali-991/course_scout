# 🎓 CourseScout — AI Learning Resource Hub

**Every course on the internet, in one place.** An EdTech aggregator platform that
searches, filters, and compares free & paid learning resources from trusted
platforms — with a UI matching the reference design.

| Layer     | Tech |
|-----------|------|
| Backend   | Django 5.2 LTS + Django REST Framework, MySQL 8.0+ (`learning_platform`) |
| Frontend  | React 18 + Vite (plain JS, no UI lib — custom design system) |
| DB driver | mysqlclient (auto-fallback: PyMySQL) |
| Auth      | none required (Saved page uses localStorage) |

---

## 📁 Project structure

```
Course_Scout/
├─ backend/
│  ├─ config/                  # Django project (settings, urls, wsgi)
│  ├─ resources/               # main app
│  │  ├─ models.py             # Resource + UserProfile
│  │  ├─ views.py              # /api/resources, /categories, /stats, /recommendations
│  │  ├─ serializers.py
│  │  ├─ pagination.py         # ?page=2&page_size=8 (max 48)
│  │  ├─ categories.py         # 6 category definitions
│  │  ├─ classify.py           # weighted keyword → category (shared, single source of truth)
│  │  ├─ creators.py           # ⭐ hand-picked YouTube channels (name, handle, topic, language)
│  │  ├─ langs.py              # English/Hindi detection (script ranges + cue words)
│  │  ├─ thumbnails.py         # SVG placeholder generator (data-URIs)
│  │  ├─ admin.py              # /admin CRUD + filters
│  │  └─ management/commands/
│  │     ├─ import_resources.py  # ⭐ aggregation command (… --only creators = channel crawler)
│  │     ├─ apply_languages.py   # re-detect languages, hide what the site doesn't serve
│  │     └─ recategorize.py      # repairs categories of rows already in MySQL
│  ├─ data/
│  │  ├─ curated_courses_1.json  # hand-verified free courses (Coursera/CS50/MIT/fCC…)
│  │  ├─ curated_courses_2.json
│  │  ├─ curated_courses_3.json  # AI/ML · Python · digital-marketing balance
│  │  ├─ manual_seed.json        # 👈 YOU fill 20-30 Unacademy/PW courses here
│  │  ├─ udemy_courses.csv       # Kaggle dataset (auto-detected)
│  │  └─ coursera_courses.csv    # Kaggle dataset (optional)
│  ├─ setup_db.py                # creates the database from .env
│  ├─ tools/                     # helper scripts (optional)
│  │  ├─ preflight_check.py      # .env + DRF + MySQL health check
│  │  ├─ schema_check.py         # dump table columns / indexes / row count
│  │  └─ install_wheel.py        # unpack a .whl without pip (pip-hang fallback)
│  ├─ .env                       # 🔐 secrets (gitignored)
│  └─ .env.example
├─ frontend/
│  ├─ src/
│  │  ├─ pages/               # Discover.jsx · Categories.jsx · Saved.jsx
│  │  ├─ components/          # Navbar, CourseCard, Footer, Pagination, …
│  │  ├─ hooks/useSaved.js    # localStorage bookmarks
│  │  └─ index.css            # design system from the reference video
│  └─ index.html
└─ myenv/                     # Python virtualenv (already configured)
```

---

## 🚀 Setup (first time only)

### 1. Put your MySQL password in `backend/.env`

Open **`backend/.env`** and fill the DB block (do not paste it in chat):

```env
DB_NAME=learning_platform
DB_USER=root
DB_PASSWORD=<your-mysql-root-password>
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 2. Create the database + tables

```powershell
cd d:\Course_Scout
myenv\Scripts\python.exe backend\setup_db.py          # creates `learning_platform`
cd backend
..\myenv\Scripts\python.exe manage.py makemigrations resources
..\myenv\Scripts\python.exe manage.py migrate
```

### 3. Import 300+ resources

```powershell
..\myenv\Scripts\python.exe manage.py import_resources
```

Sources it consumes automatically:
- `data/curated*.json` — **105 hand-verified free courses** (Coursera, edX/MITx, CS50, MIT OCW,
  freeCodeCamp, Google, IBM, Microsoft, Kaggle, NPTEL, HubSpot, Moz, Semrush, fast.ai, Hugging Face,
  Karpathy, 3Blue1Brown, Figma, Laws of UX…)
- `data/udemy_courses.csv` — Kaggle Udemy dataset (thousands of courses; rows whose subject is
  outside the six categories, e.g. *Musical Instruments*, are skipped instead of mis-labelled)
- `data/coursera_courses.csv` — Kaggle Coursera dataset (optional)
- `data/manual_seed.json` — your Unacademy / Physics Wallah entries
  (placeholder rows titled `EXAMPLE …` are ignored automatically)
- YouTube Data API — only if `YOUTUBE_API_KEY` is set in `.env`. The keyword search is pinned to
  `regionCode=IN` and every query runs twice — `relevanceLanguage=en` and `relevanceLanguage=hi` —
  so the crawler cannot pull a Japanese / Chinese / Korean result that merely ranks well globally.

Deduplication is by **normalized link**; broken links (404/410) are dropped, while
bot-blocked (403/405/429) and temporarily down (5xx/timeout) pages are kept.
Resources with no image in their source get a **topic-matched stock photo**
(see [Course images](#-course-images)). Re-runs are safe.

> **Current snapshot:** **3,810 live resources** — 2,810 from the Kaggle Udemy CSV, 95 curated,
> 86 found by keyword search and 819 crawled from 27 hand-picked YouTube channels (links checked):
> web-development 1,567 · data-analytics 1,329 · ui-ux-design 565 · ai-machine-learning 203 ·
> python 85 · digital-marketing 61 — and **English 3,369 / Hindi 441**.
> Off-topic CSV subjects (Musical Instruments, Fitness, …) are dropped, not misfiled, and courses
> in a language the site does not serve are hidden rather than mislabelled
> (see [Languages & top creators](#-languages--top-creators)).

Useful flags:

```powershell
..\myenv\Scripts\python.exe manage.py import_resources --only curated   # one source only
..\myenv\Scripts\python.exe manage.py import_resources --dry-run        # report, write nothing
..\myenv\Scripts\python.exe manage.py import_resources --skip-verify    # skip link checking (fast)
..\myenv\Scripts\python.exe manage.py import_resources --verbose        # list every dropped URL
..\myenv\Scripts\python.exe manage.py recategorize --apply --drop-offtopic   # repair categories already in MySQL
..\myenv\Scripts\python.exe manage.py attach_thumbnails          # report rows without a real image
..\myenv\Scripts\python.exe manage.py attach_thumbnails --apply  # store topic-matched photo URLs in MySQL
..\myenv\Scripts\python.exe manage.py clean_invalid_titles          # report titles in a foreign writing system
..\myenv\Scripts\python.exe manage.py clean_invalid_titles --apply  # delete exactly those rows (never a table wipe)
```

### The YouTube crawler (`--only creators`)

`resources/creators.py` is the hand-picked channel list — one row per channel with its handle,
default topic, language and the search terms the keyword crawler uses. `--only creators` walks
each channel's own uploads **and** playlists straight through the YouTube Data API, so nothing
in the ★ Top creators filter depends on search ranking:

```powershell
..\myenv\Scripts\python.exe manage.py import_resources --only creators --skip-verify
..\myenv\Scripts\python.exe manage.py import_resources --only creators --creators CodeWithHarry,chaiaurcode `
    --videos-per-creator 40 --playlists-per-creator 25 --skip-verify   # deeper re-crawl of a few channels
```

Each channel costs ~13 API units for 25 uploads + 8 playlists (the free quota is 10,000/day),
uploads under 2 minutes (Shorts) are skipped, and every row is deduped by link, so re-runs are
cheap and safe. `--creators` takes comma-separated names or `@handles`;
`--videos-per-creator` / `--playlists-per-creator` set the depth.

<!-- README_PART2 -->

## ▶️ Running the app (every time)

**Terminal 1 — backend (port 8000):**
```powershell
cd d:\Course_Scout\backend
..\myenv\Scripts\python.exe manage.py runserver
```

**Terminal 2 — frontend (port 5173):**
```powershell
cd d:\Course_Scout\frontend
Copy-Item .env.example .env   # first time only — sets VITE_API_URL (see "Frontend env" below)
npm run dev
```

Open **http://localhost:5173** (or **http://127.0.0.1:5173**) — Discover / Categories / Saved pages.
Admin panel: **http://localhost:8000/admin** — or the same page through the dev
proxy at **http://localhost:5173/admin**. On the *Resources* list the **title** is the link that
opens the edit form (`list_display_links = ('title',)` in `resources/admin.py`), because the first
column is the thumbnail image — keep that in mind if you ever add `list_editable`: a field cannot
be in both lists (`admin.E121`).

**Admin login:** this checkout ships one staff account — **`admin` / `course1234`**
(local dev only, verified working). There is no other staff user, so that is the
one to use. To change the **password or the username**:

| Where | How |
|---|---|
| **Easiest — helper script** (asks twice, input hidden, prints what happened, works from any folder) | `cd d:\Course_Scout` then `myenv\Scripts\python.exe backend\tools\reset_admin_password.py` — add `--username X` for another account, `--password PW --force` to skip the prompts |
| **Change the username** | `cd d:\Course_Scout` then `myenv\Scripts\python.exe backend\tools\reset_admin_password.py --rename boss` (password stays as it is; add `--password NEW` to change both at once). Plain Django form, from `backend\`: `..\myenv\Scripts\python.exe manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.username='boss'; u.save(update_fields=['username'])"` — after either one, log in with the **new** name |
| Terminal (asks twice, input hidden) | `cd d:\Course_Scout\backend` then `..\myenv\Scripts\python.exe manage.py changepassword admin` |
| Terminal, non-interactive/scripted | `..\myenv\Scripts\python.exe manage.py shell -c "from django.contrib.auth.models import User; u=User.objects.get(username='admin'); u.set_password('YOUR-NEW-PASSWORD'); u.save()"` |
| Browser, after logging in | **http://localhost:8000/admin/password_change/** (the ⚙️ *Change password* link, top-right of every admin page) |
| Browser, for someone else | *Users → admin → this form* → **http://localhost:8000/admin/auth/user/1/password/change/** |
| Start over with a new account | `..\myenv\Scripts\python.exe manage.py createsuperuser` |

> **`changepassword` seems to "do nothing"?** It is almost always one of these:
> **(1) wrong folder** — the command in this README starts with `..\` so it only
> works *after* `cd d:\Course_Scout\backend`; from the repo root you get
> `The term '..\myenv\Scripts\python.exe' is not recognized…` (or, with a plain
> `python manage.py …`, `can't open file 'D:\Course_Scout\manage.py'`);
> **(2) typing is invisible** — `Password:` never echoes anything, and
> `Password (again):` must match or it repeats forever;
> **(3) a weak password is refused** and it silently re-asks — Django rejects
> anything shorter than 8 characters, a common password, or all digits
> (`1234` → *too short* + *too common* + *entirely numeric*). Pick e.g.
> `Scout@2026pass`. `set_password()` (the script / one-liner above) skips those
> validators, which is how the `course1234` local-dev value is kept in place;
> **(4) a typo in the username** → `CommandError: user 'X' does not exist`
> (although MySQL's case-insensitive collation here still matches `Admin` → `admin`).
>
> Each run ends with `Password changed successfully for user 'admin'` — if you
> do not see that line, the password was **not** stored.

> **Forgotten the password?** It cannot be read back — Django stores only a
> one-way `pbkdf2_sha256` hash (`auth_user.password`, e.g.
> `pbkdf2_sha256$1000000$qtvkvrQPwW…`), so "show me my password" is impossible
> by design; even this repo's owner only gets `check_password()` = *does this
> string match?*. Set a new one with any row above — that is also the fix if the
> value here stops working because someone changed it.

> The dev server proxies `/api` (and `/admin`, `/static`, `/media`) to the backend URL
> taken from **`frontend/.env` → `VITE_API_URL`** (`frontend/vite.config.js`), so every
> browser request stays same-origin (no CORS, no `localhost`-IPv6 vs `127.0.0.1`
> mismatches) and the UI works on whichever port Vite picks (5173, 5174, …).
> Pointing the frontend at another backend? Edit that one variable and restart
> `npm run dev` — nothing in `src/` has a URL in it any more.

> **Admin login keeps reloading?** Two things used to cause it, both already fixed in
> `config/settings.py`: (1) the proxied login POST arrives with
> `Origin: http://localhost:5173` but `Host: 127.0.0.1:8000`, which Django's CSRF
> check rejects — `CSRF_TRUSTED_ORIGINS` now lists the Vite dev origins; (2) any
> non-`localhost` host (e.g. `http://192.168.x.x:8000`) answered
> `400 Invalid HTTP_HOST header` — while `DEBUG=True`, `ALLOWED_HOSTS` also accepts `*`.
> If it ever fails again, check the login POST's status in DevTools → Network:
> `403` = CSRF/origin, `400` = host, `200` (form re-renders) = wrong credentials.
> Vite binds IPv4 only, so `http://[::1]:5173` will not connect — use `localhost`
> or `127.0.0.1`.

---

## 🐳 Docker — full stack in one command

Everything (MySQL + Django/gunicorn + nginx-served React) starts together. Only Docker
Desktop is needed — no Python, no Node, no manual migrations:

```powershell
cd d:\Course_Scout
docker compose up --build     # first run builds both images (a few minutes)
```

| URL | What |
|---|---|
| **http://localhost** | the React site (nginx, port 80) |
| **http://localhost/admin** | Django admin — `admin` / `course1234` |
| **http://localhost:8000** | backend directly (gunicorn — optional, for debugging) |

First boot runs automatically: migrations → **seeds the bundled
`data/curated_courses_*.json`** (96 courses, no YouTube API key needed) → gunicorn.
A later restart prints `[entrypoint] database already has 96 resources (seed runs only below 1) — skipping seed`,
so your edits are never overwritten. Data lives in the `mysql_data` volume and survives
restarts.

Day-to-day commands (repo root):

| Command | Does |
|---|---|
| `docker compose ps` | container status — `(healthy)` = OK |
| `docker compose logs -f backend` | watch migrate/seed/gunicorn output |
| `docker compose up -d --build` | rebuild after changing code, run detached |
| `docker compose down` | stop all three (database volume is kept) |
| `docker compose down -v` | stop **and delete** the database → next boot seeds fresh |
| `docker compose exec backend python manage.py <cmd>` | run any `manage.py` command inside the container |

Configuration — every value has a working default in `docker-compose.yml`; override with a
**root `.env` file** (git-ignored) or inline:

| Variable | Default | Meaning |
|---|---|---|
| `FRONTEND_PORT` | `80` | site port (`80` needs Admin mode on Windows; use `FRONTEND_PORT=8080` otherwise) |
| `BACKEND_PORT` | `8000` | direct API port |
| `SECRET_KEY` | `compose-local-only-change-me` | set your own for anything shared |
| `DB_PASSWORD` | `coursescout` | MySQL root password **inside** the container |
| `DB_NAME` | `learning_platform` | database name |
| `DB_HOST` / `DB_PORT` | `db` / `3306` | point at your **own** MySQL instead: `DB_HOST=host.docker.internal DB_PASSWORD=<yours> docker compose up` |
| `SEED_ON_FIRST_RUN` | `1` | `0` = never auto-seed |
| `SEED_IF_ROWS_BELOW` | `1` | seed **only** while the DB has fewer rows than this — `1` = empty DB only, `1000` = also seed a fresh DB with up to 999 rows. If the row count cannot be read (remote DB down/error), seeding is skipped automatically |
| `VITE_API_URL` | *(empty)* | frontend **build-arg**; empty → bundle calls `/api` on the same origin and nginx proxies it (no CORS). Set only if the browser must reach Django on another origin |

> The container gets its config from compose's `environment:` block — your
> `backend/.env` is **not** baked into the image (`.dockerignore` excludes it). Put DB
> overrides in the **root `.env`** (this repo's root `.env` points the Docker backend at
> the Clever Cloud MySQL `bo5wcz2flycdklakrejg`, so the site shows your real data).
> With no root `.env`, Docker falls back to its own local MySQL seeded with the 96
> curated courses instead.

Verified working end-to-end: `/` 200, `/api/stats/` 200 (also via `:8000`), `/admin/login/`
200, `/static/admin/css/base.css` 200 (WhiteNoise), SPA routes (`/categories`) fall back to
`index.html`, and the built JS contains **no** `localhost:8000` — it calls the same origin.

---

## ⚙️ Frontend env — where the backend URL lives

The frontend never hardcodes a backend address: it reads **`VITE_API_URL`** (only names
starting with `VITE_` reach the browser, and Vite replaces them at build time).

| File | Committed? | Purpose |
|---|---|---|
| `frontend/.env.example` | ✅ yes — the sample to copy from (holds no secrets) | documents the variable |
| `frontend/.env` | ❌ **gitignored** — your machine's real value | `VITE_API_URL=http://localhost:8000` |

```powershell
cd d:\Course_Scout\frontend
Copy-Item .env.example .env     # once per machine
```

* The value is an **origin only** — no trailing slash, no `/api` (`src/api.js` appends `/api`).
* `npm run dev` → the Vite proxy sends `/api`, `/admin`, `/static`, `/media` to that URL
  (`vite.config.js`), so the browser stays same-origin.
* `npm run build` → the URL is **baked into `dist/`**, so a deployed bundle cannot read a
  `.env` file at runtime. Change the variable → **rebuild/redeploy**.
* Escape hatch: `VITE_API_BASE=https://site.com/v2/api` wins over both rules above.
* Missing variable? The dev server prints a clear `[CourseScout] VITE_API_URL is missing…`
  warning instead of failing silently.
* Left in the repo on purpose: `src/api.js` and `vite.config.js` mention
  `http://localhost:8000` inside **comments and that warning text** — there is no live URL
  in any code path.

---

## 🚀 Deploying on Render (and where `VITE_API_URL` goes)

Render runs two services from this repo — a **web service** for Django and a **static site**
for the React build:

> **Shortcut — `render.yaml` (Blueprint):** the repo ships a blueprint that defines both
> services. Render dashboard → **New + Blueprint** → point it at this repo → it creates
> `coursescout-api` (Python, runs `docker-entrypoint.sh` → migrate → seed → gunicorn) and
> `coursescout-web` (static site). You still set the secrets yourself
> (`SECRET_KEY`, `DB_*`, `YOUTUBE_API_KEY`) and **`VITE_API_URL`** under
> *Environment → Environment Variables* before/at first deploy. Prefer manual setup? The
> two tables below are exactly what the blueprint encodes.

**1. Backend — Web Service** (`backend/`)

| Render setting | Value |
|---|---|
| Build Command | `pip install -r requirements.txt` (add `gunicorn` to it — Render needs a WSGI server, `runserver` is dev-only) |
| Start Command | `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT` |
| Environment → **Environment Variables** | `SECRET_KEY=…`, `DEBUG=False`, `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` (a Render MySQL/Postgres URL or your hosted MySQL), `ALLOWED_HOSTS=your-api.onrender.com`, `CORS_ALLOWED_ORIGINS=https://your-frontend.onrender.com`, `YOUTUBE_API_KEY=…` — `CSRF_TRUSTED_ORIGINS` needs no separate value: `settings.py` starts it from `CORS_ALLOWED_ORIGINS` (`CSRF_TRUSTED_ORIGINS = set(CORS_ALLOWED_ORIGINS)`) |

**2. Frontend — Static Site** (`frontend/`)

| Render setting | Value |
|---|---|
| Build Command | `npm ci && npm run build` |
| Publish Directory | `dist` |
| Environment → **Environment Variables** | **`VITE_API_URL=https://your-api.onrender.com`** ← this is the one the question is about |

```text
Render dashboard → your FRONTEND service → Environment (left menu)
                → Environment Variables → Add Environment Variable
                     Key   : VITE_API_URL
                     Value : https://coursescout-api.onrender.com
                → Save Changes  →  it redeploys (or hit "Manual Deploy")
```

Notes for a first deploy:

* Set the variable **before** the first build: Vite freezes it into the JS bundle, so a later
  edit only takes effect after a **redeploy** (not just a restart).
* Same key name as in `.env` — `VITE_API_URL`. Do not add `/api` at the end.
* Then set the backend's `CORS_ALLOWED_ORIGINS` to the frontend's `https://….onrender.com` URL,
  otherwise the browser calls are blocked (that is the CORS error you would see in the console).
  One variable is enough — the admin login's CSRF list is derived from it in `settings.py`.
* `.env` is never uploaded — Render only uses the dashboard variables.

---

## 🔌 API reference

| Endpoint | Purpose |
|---|---|
| `GET /api/resources/` | list/search — `?search=python&category=python&is_free=true&level=beginner&resource_type=youtube&language=hi&provider=CodeWithHarry&top_creators=true&ordering=-rating&page=1&page_size=9&ids=1,2,3` |
| `GET /api/resources/<id>/` | single resource detail |
| `GET /api/categories/` | 6 categories with live course counts |
| `GET /api/creators/?platform=youtube` | every provider with `{name, count, languages, is_top}` — top creators first, so the channel dropdown needs one call |
| `GET /api/languages/` | `[{code, label, course_count}]` — the languages the catalog actually serves (English + Hindi) |
| `GET /api/stats/` | `{total, free, paid, platforms}` for the hero badge |
| `GET /api/recommendations/` | top picks; `?interests=python,ai-machine-learning` (or from UserProfile) |

Every card carries `language`, `language_label` and `is_top_creator`, so the UI can badge
a Hindi course or a starred channel without a second request.
`thumbnail_url` is **never empty** — see below. Default `page_size` is 9 so the
Discover grid fills three rows of three cards.

### Every Discover filter is a URL parameter

`http://localhost:5173/?q=…&category=<slug>&type=youtube&free=free&lang=hi&creator=CodeWithHarry&top=1`
— links are shareable and browser **Back** works, because the query string is the single source
of truth for the page:

| Link | Shows |
|---|---|
| `/?category=web-development` | every course **in** that category (exact match — this is where a category card sends you) |
| `/?type=youtube` | the **YouTube courses** tab — every resource whose link is a YouTube video/playlist (API: `?platform=youtube`), hand-picked channels first |
| `/?lang=hi` | **Hindi** courses only (API: `?language=hi`; `?lang=en` for English) |
| `/?type=youtube&creator=CodeWithHarry` | one channel's uploads and playlists (API: `?provider=CodeWithHarry`) |
| `/?type=youtube&top=1` | the **★ Top creators** tab — only the channels starred in `resources/creators.py` (API: `?top_creators=true`) |
| `/?q=react&category=python&free=free&lang=en` | free-text search, combinable with the tabs, dropdowns and language |

> Category cards link by **slug** (`?category=`), never by text: searching the phrase
> “Web Development” only matches rows whose title/provider/description literally contain those
> words, which is a completely different set from `category='web-development'`. That mismatch is
> what used to open a 1,000+ course category with only a handful of cards.

---

## 🌐 Languages & top creators

The hub teaches **English and Hindi** only, and language is stored per row (`Resource.language`),
never guessed in the browser:

* `resources/langs.py` decides. First the writing system wins: Devanagari ⇒ `hi`, and any other
  non-Latin script (Malayalam, Tamil, Arabic, Cyrillic, CJK, …) is reported as that language so
  the row can be hidden. Latin-script titles then fall back to the channel's own list entry
  (`language=` in `resources/creators.py`) and to Hindi cue words (`kya`, `kaise`, `full course
  hindi`, …).
* The crawler writes that tag as it imports; `manage.py apply_languages --apply` re-tags the
  whole table afterwards and sets `is_active=False` on anything outside `SUPPORTED_LANGUAGES`
  (`--apply` writes, without it the command only reports). Hidden rows stay in MySQL for the
  audit trail but disappear from every API response and count.
* A Hindi channel stays Hindi even when it titles a video in English — that is why the channel
  list, not the title, has the final say for crawled rows.
* **Leftover rows from older imports** are removed by writing system, not by a language guess:
  `manage.py clean_invalid_titles` reads each title's letters with the stdlib `unicodedata` module
  and reports (then, with `--apply`, deletes) everything that is neither **Latin** (English) nor
  **Devanagari** (Hindi) — CJK / kana / Hangul / Thai / Arabic / Cyrillic / Greek / Bengali / Tamil
  / Telugu / Malayalam … Digits, `–`, `©` and emoji are ignored, a lone maths `π` inside an English
  title is treated as a symbol, and Hindi titles are never matched. Add `--include-latin-foreign`
  to also drop Latin-script foreign titles (`Curso de …`, `Türkçe eğitim`) via the same
  `FOREIGN_MARKERS` list. Without `--apply` nothing is written, and the summary always prints
  *deleted* vs *left*:

  ```powershell
  ..\myenv\Scripts\python.exe manage.py clean_invalid_titles --apply
  # deleted 54 row(s) · 3911 left (3810 live, 101 hidden)
  # re-check: 0 remaining title(s) in a non English/Hindi script
  ```
* Both rules are covered by `..\myenv\Scripts\python.exe manage.py test resources` (script
  detection, the cleanup command's dry-run/apply behaviour, and the admin title link).

---

## 🖼️ Course images

The Kaggle CSVs ship no image column, so a card's picture resolves in this order
(`resources/thumbnails.py`, exposed as `Resource.display_thumbnail` and used by
the API serializer **and** the admin list):

1. the video's **own frame** when the link is a YouTube watch URL — derived from the
   video id as `https://i.ytimg.com/vi/<id>/hqdefault.jpg`, so no API key or quota is
   needed (playlist links have no such frame and fall through to the photo pool);
2. `thumbnail_url` from the source itself (curated JSON / YouTube API thumbnails);
3. a **topic-matched stock photo** — `CATEGORY_PHOTOS` holds ~7 hand-picked
   Unsplash/Pexels CDN URLs per category (code screens for Python, dashboards for
   data-analytics, wireframes for UI/UX, …). The pick is `hash(resource_id) % len(pool)`,
   so a course always shows the same photo and pages never reshuffle;
4. an on-the-fly **SVG gradient card** with the course initials (only if a category
   has no photo pool at all) — plus the React card swaps to the same style locally
   if a CDN URL ever fails, so a tile is never blank.

```powershell
# MySQL itself has no image, so the DB only stores SVG data-URIs? Fix that:
cd d:\Course_Scout\backend
..\myenv\Scripts\python.exe manage.py attach_thumbnails --apply
```

* Don't like a picture / want your own? Edit `CATEGORY_PHOTOS` in
  `backend/resources/thumbnails.py` (one list per category slug) and re-run
  `attach_thumbnails --apply --refill`.
* Images are hotlinked from the CDN — nothing is downloaded or stored, in line with
  the "URLs only" rule. Credits: [Unsplash license](https://unsplash.com/license)
  and [Pexels license](https://pexels.com/license) (both allow hotlinking; a few
  rows mix both providers so each topic has 7 options).
* The grid is **three cards per row** (`.grid-courses`, ≥901px), two cards per row from
  641–900px and one column on phones, and `page_size` defaults to **9** so a full page
  is exactly three rows.

---

## 🗄️ View tables in MySQL Workbench

1. Open MySQL Workbench → connect to `127.0.0.1:3306` (user `root`).
2. In the query tab run:
   ```sql
   USE learning_platform;
   SELECT COUNT(*) FROM resources_resource;
   SELECT category, COUNT(*) FROM resources_resource GROUP BY category;
   SELECT platform, COUNT(*) FROM resources_resource GROUP BY platform;
   SELECT id, title, provider, platform, category, is_free, rating
   FROM resources_resource LIMIT 20;
   ```
3. Main tables: `resources_resource`, `resources_userprofile`, plus Django auth tables.

---

## 🧯 Troubleshooting

| Problem | Fix |
|---|---|
| `Access denied for user 'root'` | Fill `DB_PASSWORD` in `backend/.env`, re-run `setup_db.py` |
| `Unknown database 'learning_platform'` | Run `myenv\Scripts\python.exe backend\setup_db.py` |
| `mysqlclient` build error | `myenv\Scripts\python.exe -m pip install PyMySQL` (auto-detected by settings) |
| Frontend shows "Backend not reachable" | Click **Retry** on the page (it also auto-retries twice). Make sure Django is up: `..\myenv\Scripts\python.exe manage.py runserver` — the page now prints the exact URL that failed. Requests go through the Vite proxy, so no CORS setup is needed in dev |
| Two frontend servers (5173 + 5174) | Vite auto-shifts the port when 5173 is taken — stop the extra terminal, or just use the URL Vite printed (the proxy works on any port) |
| Card image looks generic or repeats | Expected — the CSV sources ship no images, so a topic-matched stock photo is chosen per category (`CATEGORY_PHOTOS` in `backend/resources/thumbnails.py`). Swap the URLs there, then `..\myenv\Scripts\python.exe manage.py attach_thumbnails --apply --refill` |
| Card image is a flat gradient with initials | A CDN photo failed to load (offline / blocked). Cards fall back to a local SVG so nothing is blank; check internet access, or replace that URL in `CATEGORY_PHOTOS` |
| Import count < 300 | Add the Kaggle CSVs to `backend/data/` and/or set `YOUTUBE_API_KEY`, then re-run `import_resources` |
| Courses land in the wrong category (e.g. guitar under Python) | Categories come from `resources/classify.py`; fix the keywords/maps there, then run `..\myenv\Scripts\python.exe manage.py recategorize` (report only) and finally add `--apply --drop-offtopic` to repair the stored rows (add `--source all` to include curated/manual rows too) |
| A valid link is reported as broken | `check_one_url` retries and re-checks with GET; if a specific host still fails, lower the parallelism in `verify_entries` or add the URL manually via `/admin` |
| Forgot the admin password | Not recoverable — `auth_user.password` holds a one-way `pbkdf2_sha256` hash. Easiest fix: `cd d:\Course_Scout` → `myenv\Scripts\python.exe backend\tools\reset_admin_password.py` (asks twice, prints what it did). Alternatives are in the admin-login table above |
| `changepassword admin` "does nothing" | Wrong folder (it needs `cd d:\Course_Scout\backend` first), invisible typing (`Password:` echoes nothing, the repeat must match), or a weak password being refused in a loop (`1234` → too short/too common/entirely numeric) — details in the admin-login table above. Use `backend\tools\reset_admin_password.py` if it keeps confusing you |
| Want to rename the `admin` account | `cd d:\Course_Scout` → `myenv\Scripts\python.exe backend\tools\reset_admin_password.py --rename NewName` (password untouched; add `--password PW` to change both). Django has no built-in rename command — only the shell edit shown in the admin-login table. Afterwards log in with the new name; MySQL here is case-insensitive so `Boss` collides with an existing `boss` |
| Course titles in Japanese / Chinese / Korean / Arabic … | They came from a search that ran without a language or region. `..\myenv\Scripts\python.exe manage.py clean_invalid_titles` reports them, `--apply` deletes only those rows (English + Hindi titles are untouched); the crawler now searches `regionCode=IN` in `en` and `hi` |
| `--verify` too slow | `python manage.py import_resources --skip-verify` |
| `System check identified some issues` → `mysql.W003` (unique CharField > 255) | Harmless: `url` is `varchar(500)` with a `UNIQUE KEY`, which fits MySQL 8's 3072-byte index limit — the migration applies fine |
| Django 6.x error: *"MySQL 8.4.0 or later is required"* | MySQL 8.0.44 is installed, so we pin **Django 5.2 LTS** (`Django==5.2.17`) instead of upgrading MySQL |
| `pip install -r requirements.txt` hangs / never downloads | Download the wheel URL from `https://pypi.org/pypi/Django/json` with `Invoke-WebRequest`, then unpack it: `myenv\Scripts\python.exe backend\tools\install_wheel.py <wheel-file>` |
| Want a quick health check | `myenv\Scripts\python.exe backend\tools\preflight_check.py` (env, DRF, MySQL) and `schema_check.py` (tables, columns, row count). Admin password stuck? `myenv\Scripts\python.exe backend\tools\reset_admin_password.py` |

---

## 🛡️ Data rules

- **No scraping of Unacademy / Physics Wallah** — only via `manual_seed.json` (you fill it).
- Only **URLs** are stored in MySQL — never downloaded files.
- `.env` is gitignored; `.env.example` ships with empty secrets.
- Kaggle CSVs & the YouTube API are official/public data sources.
- Course images are **hotlinked** Unsplash/Pexels URLs (never downloaded) — see
  [Course images](#-course-images).

*Built for the Course_Scout project — Django + DRF + MySQL + React (Vite).*

