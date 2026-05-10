# POČASNÍK

Školní OOP projekt — desktopová aplikace v Pythonu, která zobrazuje aktuální počasí a 7denní předpověď pro uložená oblíbená města přihlášeného uživatele.

- **Kategorie zadání:** Aplikace
- **GUI:** CustomTkinter (moderní tmavý vzhled)
- **Databáze:** SQLite (`pocasnik.db`)
- **Externí API:** [Open-Meteo](https://open-meteo.com) (geokódování + předpověď, **bez API klíče**)
- **Architektura:** MVVM
- **Autentizace:** vlastní registrace + přihlášení (PBKDF2-SHA256, 100 000 iterací, náhodná sůl)
- **Easter egg:** skrytý terminálový minigame, otevře se zkratkou `Ctrl + Shift + E`

---

## Splnění bodů zadání

| Požadavek | Splněno v |
|---|---|
| Moderní GUI | `app/views/*` (CustomTkinter) |
| Napojení na DB | `app/database.py` (SQLite) |
| Externí API | `app/services/weather_service.py` (Open-Meteo) |
| Validace na datové vrstvě | `Entity.validate()`, volá se v `Repository.save()` |
| Architektura (MVVM) | složky `models/` `repositories/` `services/` `viewmodels/` `views/` |
| Login + registrace | `AuthService`, `LoginView`, `RegisterView` |
| OOP, struktura ve složkách | viz níže |
| Polymorfismus | `Entity`, `Repository[T]`, `BaseView` |
| `.exe` + vlastní ikona | `app.spec` (PyInstaller) + `app/assets/icon.ico` |
| Postupné commity | git history |
| Easter egg | `app/easter_egg/terminal_game.py`, zkratka v `Application._bind_easter_egg` |

---

## Mapa struktury projektu

```
ClientRadar/
├── app/                           # zdrojový kód aplikace
│   ├── __init__.py
│   ├── __main__.py                # vstupní bod (python -m app)
│   ├── app.py                     # Application – přepínání oken, easter egg
│   ├── database.py                # SQLite wrapper (singleton-like)
│   │
│   ├── models/                    # M (Model) – doménové entity
│   │   ├── base.py                #   Entity (abstract), ValidationError
│   │   ├── user.py                #   User(Entity)
│   │   └── city.py                #   City(Entity)
│   │
│   ├── repositories/              # datová vrstva
│   │   ├── base.py                #   Repository[T] (abstract, generická)
│   │   ├── user_repo.py           #   UserRepository(Repository[User])
│   │   └── city_repo.py           #   CityRepository(Repository[City])
│   │
│   ├── services/                  # aplikační logika
│   │   ├── auth_service.py        #   PBKDF2 hash, login/register
│   │   └── weather_service.py     #   Open-Meteo klient (urllib)
│   │
│   ├── viewmodels/                # VM (ViewModel)
│   │   ├── auth_vm.py             #   AuthViewModel
│   │   └── weather_vm.py          #   WeatherViewModel
│   │
│   ├── views/                     # V (View) – CustomTkinter
│   │   ├── base_view.py           #   BaseView (abstract)
│   │   ├── login_view.py          #   LoginView(BaseView)
│   │   ├── register_view.py       #   RegisterView(BaseView)
│   │   ├── main_view.py           #   MainView(BaseView)
│   │   └── search_city_view.py    #   SearchCityView(BaseView)
│   │
│   ├── easter_egg/
│   │   └── terminal_game.py       #   TerminalGameWindow(tk.Toplevel)
│   │
│   └── assets/
│       └── icon.ico               #   ikona aplikace
│
├── terminal_game/                 # standalone verze easter-eggu
│   ├── __init__.py
│   └── __main__.py                #   TerminalGame(tk.Tk) – samostatné okno
│
├── app.spec                       # PyInstaller config (build .exe)
├── requirements.txt
└── README.md
```

### Dědičnost (kdo od koho dědí)

```
ABC
└── Entity
    ├── User
    └── City

Generic[T] + ABC
└── Repository[T]
    ├── UserRepository  (T = User)
    └── CityRepository  (T = City)

customtkinter.CTkFrame
└── BaseView (abstract)
    ├── LoginView
    ├── RegisterView
    ├── MainView
    └── SearchCityView

tkinter.Toplevel
└── TerminalGameWindow              (easter egg uvnitř aplikace)

tkinter.Tk
└── TerminalGame                    (standalone v terminal_game/)
```

### Kde je polymorfismus

| Polymorfní rozhraní | Místo definice | Konkrétní implementace |
|---|---|---|
| `Entity.validate()` | `app/models/base.py` | `User.validate`, `City.validate` |
| `Entity.to_dict()` | `app/models/base.py` | `User.to_dict`, `City.to_dict` |
| `Repository._table_name` / `_columns` / `_row_to_entity` | `app/repositories/base.py` | `UserRepository`, `CityRepository` |
| `BaseView.build()` / `on_show()` | `app/views/base_view.py` | každý konkrétní View |

`Repository.save()` volá polymorfní `entity.validate()` — datová vrstva **vždy** validuje, ať se použije jakákoliv entita.

### Tok dat (MVVM)

```
View  ─▶  ViewModel  ─▶  Service  ─▶  Repository  ─▶  SQLite
                              │
                              └──▶  WeatherService  ─▶  Open-Meteo (HTTP)
```

---

## Schéma databáze

```sql
users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    salt          TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
)

cities (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    country    TEXT    NOT NULL,
    latitude   REAL    NOT NULL,
    longitude  REAL    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)
```

---

## Validační pravidla (datová vrstva)

| Entita | Pole | Pravidlo |
|---|---|---|
| `User` | `username` | regex `^[A-Za-z0-9_]{3,32}$` |
| `User` | `password_hash`, `salt` | nesmí být prázdné |
| `City` | `user_id` | kladné celé číslo |
| `City` | `name`, `country` | 1–80 znaků |
| `City` | `latitude` | rozsah −90 až 90 |
| `City` | `longitude` | rozsah −180 až 180 |

Heslo (před hashováním) se kontroluje na **min. 6 znaků** v `AuthService.register`.

---

## Spuštění (vývojový režim)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

První spuštění vytvoří soubor `pocasnik.db` v rootu repa.

---

## Build `.exe`

V kořeni repa, s aktivovaným venv s nainstalovaným PyInstallerem:

```powershell
pip install pyinstaller
pyinstaller --noconfirm app.spec
```

Výsledek: `dist/Pocasnik.exe` (s vlastní ikonou, bez konzole).

---

## Easter egg

Kdekoliv v aplikaci (i na přihlašovací obrazovce) stiskni:

```
Ctrl + Shift + E
```

Otevře se skrytý terminálový minigame. Příkazy: `help`, `auth OZ-CORE`, `scan`, `breach NEON`, `purge ROOTWORM`, `reboot`. Lze ho spustit i samostatně přes `python -m terminal_game`.
