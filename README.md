# POČASNÍK

Školní OOP projekt — desktopová aplikace v Pythonu pro sledování počasí v uložených městech přihlášeného uživatele. Nabízí přehled v stylu Apple Weather (tmavá šedá „frosted“ paleta), emoji ikony podle WMO kódů počasí, hodinovou a sedmidenní předpověď, živé vyhledávání měst a **interaktivní mapu** s počasím u markerů.

| Položka | Hodnota |
|---------|---------|
| **Kategorie zadání** | Aplikace |
| **GUI** | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) |
| **Databáze** | SQLite (`pocasnik.db` vedle spustitelného souboru / v kořeni vývojového repa) |
| **Externí API** | [Open-Meteo](https://open-meteo.com) — geokódování + předpověď (**bez API klíče**, pouze HTTP GET přes `urllib`) |
| **Offline data** | Bundlovaný katalog měst `app/assets/cities.json` (~120 záznamů) pro mapu |
| **Architektura** | MVVM (oddělené modely, repozitáře, služby, viewmodely, pohledy) |
| **Autentizace** | Registrace + přihlášení, PBKDF2-HMAC-SHA256 (100 000 iterací), náhodná sůl |
| **Easter egg** | Skrytý terminálový minigame — zkratka `Ctrl + Shift + E` |

---

## Funkce aplikace

- **Přihlášení / registrace** — popisky nad poli, nápovědy k formátu uživatelského jména a hesla.
- **Hlavní obrazovka** — hero karta (velká teplota + emoji + popis stavu), **hodinová předpověď** (24 h od aktuální hodiny), **sedmidenní předpověď** (řádky s emoji, šancí na srážky, teplotní „slider“), statistiky vlhkosti / větru / pocitové teploty.
- **Postranní panel „Moje města“** — u každého města **emoji počasí a aktuální teplota** (načítání na pozadí).
- **Přidat město** — **živé vyhledávání** při psaní (debounce); výsledky z Open-Meteo Geocoding API.
- **Mapa** — tlačítko „Mapa“ v postranním panelu; interaktivní mapa ([tkintermapview](https://github.com/TomSchimansky/TkinterMapView), OpenStreetMap dlaždice), zoom kolečkem / tažením. Markery ukazují **emoji + název + teplotu**; uložená města uživatele mají odlišnou barvu markeru od katalogových měst.
- **Logika měst na mapě** — podle **úrovně zoomu** se z katalogu zobrazují jen města nad určitým prahem populace (viz níže); města uživatele jsou **vždy**. Oblast bez dlaždic se omezuje výřezem mapy (bounding box).
- **Ikona aplikace** — vlastní `app/assets/icon.ico` (více rozlišení v jednom souboru).

---

## Splnění bodů zadání (kategorie Aplikace)

| Požadavek | Kde to je |
|-----------|-----------|
| Moderní GUI | `app/views/*.py`, vizuální paleta `app/views/theme.py` |
| Napojení na DB | `app/database.py`, tabulky `users`, `cities` |
| Externí API | `app/services/weather_service.py` (forecast + geokódování přes Open-Meteo) |
| Validace na datové vrstvě | `Entity.validate()` v modelech; volá `Repository.save()` |
| Architektura MVVM | `models/`, `repositories/`, `services/`, `viewmodels/`, `views/` |
| Login + registrace | `AuthService`, `LoginView`, `RegisterView`, `AuthViewModel` |
| OOP, struktura ve složkách | Viz strom projektu níže |
| Polymorfismus | `Entity`, generický `Repository[T]`, abstraktní `BaseView` |
| Dokumentace + mapa struktury | Tento soubor + sekce *Dědičnost* / *Polymorfismus* |
| Spustitelný `.exe` + vlastní ikona | `app.spec` + `app/assets/icon.ico`; build viz sekce *Build* |
| Easter egg | `app/easter_egg/terminal_game.py`, globální bind v `app/app.py` |

**Poznámka k odevzdání:** Učitel často vyžaduje **odkaz na GitHub/GitLab** a **funkční `.exe`** — repozitář musí být nahraný a build lokálně ověřený.

---

## Mapa struktury projektu

```
ClientRadar/
├── app/
│   ├── __init__.py
│   ├── __main__.py                 # vstupní bod: python -m app
│   ├── app.py                      # Application – přepínání obrazovek, easter egg
│   ├── database.py                 # SQLite, inicializace schématu
│   │
│   ├── models/                     # Model – doménové entity
│   │   ├── base.py                 # Entity (ABC), ValidationError
│   │   ├── user.py                 # User(Entity)
│   │   └── city.py                 # City(Entity)
│   │
│   ├── repositories/               # Datová vrstva (SQLite)
│   │   ├── base.py                 # Repository[T] (ABC, generické CRUD)
│   │   ├── user_repo.py            # UserRepository
│   │   └── city_repo.py            # CityRepository
│   │
│   ├── services/                   # Služby (business + externí systémy)
│   │   ├── auth_service.py         # PBKDF2, registrace / přihlášení
│   │   ├── weather_service.py      # Open-Meteo (urllib), emoji podle WMO kódů
│   │   └── city_catalog.py         # Offline katalog měst (JSON), prahy podle zoomu
│   │
│   ├── viewmodels/
│   │   ├── auth_vm.py              # AuthViewModel
│   │   └── weather_vm.py          # WeatherViewModel
│   │
│   ├── views/
│   │   ├── theme.py                # Sdílená barevná paleta (Apple-like šedá)
│   │   ├── base_view.py            # BaseView (ABC)
│   │   ├── login_view.py
│   │   ├── register_view.py
│   │   ├── main_view.py            # Hlavní přehled + sidebar s počasím u měst
│   │   ├── search_city_view.py     # Živé vyhledávání města
│   │   └── map_view.py             # Interaktivní mapa (tkintermapview)
│   │
│   ├── easter_egg/
│   │   └── terminal_game.py        # TerminalGameWindow (tkinter.Toplevel)
│   │
│   └── assets/
│       ├── icon.ico                # Ikona aplikace (.exe / okno)
│       └── cities.json             # Katalog měst (název, země, lat/lon, populace)
│
├── terminal_game/                  # Samostatné spuštění easter-eggu
│   ├── __init__.py
│   └── __main__.py                 # TerminalGame(tk.Tk)
│
├── app.spec                        # PyInstaller (onefile, windowed, datas)
├── requirements.txt
├── pocasnik.db                     # SQLite DB (generuje se při prvním běhu; v .gitignore)
└── README.md
```

---

## Dědičnost (schéma)

```
ABC
└── Entity
    ├── User
    └── City

ABC + Generic[T]
└── Repository[T]
    ├── UserRepository     (T = User)
    └── CityRepository     (T = City)

customtkinter.CTkFrame
└── BaseView (ABC)
    ├── LoginView
    ├── RegisterView
    ├── MainView
    ├── SearchCityView
    └── MapView

_MainView pomocné komponenty_
└── _CityListItem(CTkFrame)        # položka města v sidebaru (není BaseView)

tkinter.Toplevel
└── TerminalGameWindow             # easter egg uvnitř aplikace

tkinter.Tk
└── TerminalGame                   # standalone: python -m terminal_game
```

---

## Polymorfismus

| Rozhraní / hook | Definice | Implementace |
|-----------------|----------|----------------|
| `Entity.validate()`, `to_dict()` | `app/models/base.py` | `User`, `City` |
| `Repository._table_name`, `_columns`, `_row_to_entity` | `app/repositories/base.py` | `UserRepository`, `CityRepository` |
| `BaseView.build()`, `on_show()` | `app/views/base_view.py` | všechny konkrétní views |

`Repository.save()` vždy volá `entity.validate()` před zápisem do SQLite.

---

## Tok dat (MVVM)

```
View  →  ViewModel  →  Service  →  Repository  →  SQLite
              │              │
              │              ├── WeatherService  →  Open-Meteo (HTTP)
              │              └── AuthService     →  (hashování, bez DB přímého zápisu z View)
              │
MapView (volitelně)  →  WeatherService (načtení počasu pro markery)
                     →  CityCatalogService  →  cities.json (offline)
```

---

## Externí API a offline data

### Open-Meteo (síť)

- **Geokódování:** `https://geocoding-api.open-meteo.com/v1/search` — vyhledávání měst při přidávání.
- **Předpověď:** `https://api.open-meteo.com/v1/forecast` — aktuální stav (teplota, pocitová teplota, vlhkost, vítr, WMO kód, den/noc), hodinová řada, denní max/min, kódy počasí, pravděpodobnost srážek, východ/západ (podle toho, co API vrátí v jedné odpovědi).

### Emoji počasí

Funkce `weather_emoji(code, is_day)` v `weather_service.py` mapuje WMO weather code na unicode emoji (např. jasno v noci ↔ měsíc). Popisky stavů: `describe_weather_code()`.

### Katalog měst na mapě (`cities.json`)

Statický seznam hlavních měst s přibližnou **populací**. Slouží k tomu, aby se při **malém zoomu** nezahltily mapa ani API — zobrazí se jen větší města; po přiblížení se přidávají menší.

Prah populace podle zoomu (implementace `CityCatalogService.min_population_for_zoom`):

| Zoom (celé číslo) | Min. populace města z katalogu |
|-------------------|--------------------------------|
| &lt; 4 | 8 000 000 |
| 4 | 3 000 000 |
| 5 | 1 500 000 |
| 6 | 700 000 |
| 7 | 300 000 |
| 8 | 150 000 |
| 9 | 80 000 |
| ≥ 10 | 0 (všechna katalogová města v záběru) |

Města uživatele z databáze se na mapě zobrazují **vždy**, bez ohledu na zoom a katalog.

---

## Schéma databáze

```sql
users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    salt          TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

cities (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    name       TEXT    NOT NULL,
    country    TEXT    NOT NULL,
    latitude   REAL    NOT NULL,
    longitude  REAL    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## Validační pravidla (datová vrstva)

| Entita | Pole | Pravidlo |
|--------|------|----------|
| `User` | `username` | Regex `^[A-Za-z0-9_]{3,32}$` |
| `User` | `password_hash`, `salt` | Nesmí být prázdné |
| `City` | `user_id` | Kladné celé číslo |
| `City` | `name`, `country` | Délka 1–80 znaků |
| `City` | `latitude` | −90 … 90 |
| `City` | `longitude` | −180 … 180 |

Před uložením uživatele kontroluje heslo také **`AuthService.register`** (min. 6 znaků, shoda hesel).

---

## Závislosti

Soubor `requirements.txt`:

- **customtkinter** — moderní widgety nad Tkinterem  
- **tkintermapview** — mapa (OSM dlaždice, markery, zoom)  
- **Pillow** — závislost ekosystému mapy / obrázků  

Pro build `.exe` se **doinstaluje zvlášť** PyInstaller (viz níže), v repu není nutné ho mít jako závislost vývojové aplikace.

---

## Spuštění ve vývoji

```powershell
cd D:\Projects\ClientRadar
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app
```

Při prvním spuštění se v kořeni projektu vytvoří **`pocasnik.db`** (uživatelská data). Soubor je v `.gitignore` a do repa se normálně necommituje.

---

## Build spustitelného souboru (Windows)

V kořeni projektu s aktivovaným virtuálním prostředím:

```powershell
pip install pyinstaller
python -m PyInstaller --noconfirm app.spec
```

Výstup: **`dist\Pocasnik.exe`** (jednosouborový, bez konzolového okna, vlastní ikona z `app/assets`).

> Pokud příkaz `pyinstaller` přímo v terminálu „není rozpoznán“, používej vždy **`python -m PyInstaller`**, který volá PyInstaller z aktivního Pythonu.

Soubor `app.spec` zahrnuje datové soubory balíčků **customtkinter** a **tkintermapview** a kopíruje **`icon.ico`** a **`cities.json`** do výsledného bundlu.

---

## Easter egg

Kdykoliv běží hlavní okno aplikace, stiskni:

```
Ctrl + Shift + E
```

Otevře se terminálový minigame (`TerminalGameWindow`). Příkazy např.: `help`, `auth OZ-CORE`, `scan`, `breach NEON`, `purge ROOTWORM`, `reboot`.

Samostatně (bez hlavní aplikace):

```powershell
python -m terminal_game
```

---

## Řešení problémů

| Problém | Návrh |
|---------|--------|
| Mapa je prázdná / dlouho načítá | První stažení OSM dlaždic může chvíli trvat; zkontroluj internet. |
| `tkintermapview` po instalaci nejde importovat | Ověř `pip install -r requirements.txt` ve stejném venv jako `python -m app`. |
| Build `.exe` neobsahuje města na mapě | Ověř, že `app/assets/cities.json` je zabalený (v `app.spec` je v `datas`). |

---

*Tento dokument odpovídá stavu kódu v repozitáři ClientRadar (projekt POČASNÍK).*
