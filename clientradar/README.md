# ClientRadar 📡

Desktopová aplikace pro hledání potenciálních klientů přes Google Maps a správu kontaktů v CRM stylu.

## Co aplikace dělá

- **Scrapuje Google Maps** — zadejte klíčové slovo (např. "instalatér") a lokalitu (např. "Praha"), aplikace najde firmy a uloží je do lokální databáze
- **CRM tabulka** — spravujte nalezené leady, měňte jejich status (Nový, Kontaktován, Má zájem, Nezájem, Ignorován)
- **Hledání emailů** — automaticky prohledává webové stránky firem a hledá kontaktní emaily
- **Export do Excelu** — exportujte leady do .xlsx souboru se stylovaným formátováním
- **Filtrování a vyhledávání** — fulltextové hledání + filtr podle statusu
- **Lokální databáze** — vše běží offline, data v SQLite

## Požadavky

- **Python 3.11+**
- **Google Chrome** musí být nainstalován (používá se pro scraping)
- Windows / macOS / Linux

## Instalace

```bash
cd clientradar
pip install -r requirements.txt
```

## Spuštění

```bash
python main.py
```

## Jak používat

1. **Spusťte aplikaci** — otevře se tmavé desktopové okno
2. **Zadejte hledání** — v levém panelu vyplňte klíčové slovo a lokalitu
3. **Nastavte parametry** — počet výsledků, headless režim, hledání emailů
4. **Klikněte na "Spustit hledání"** — aplikace otevře Chrome a začne scrapovat
5. **Sledujte průběh** — ve spodní liště vidíte progress bar a počet nalezených výsledků
6. **Spravujte leady** — klikněte na lead v tabulce pro zobrazení detailů vpravo
7. **Měňte status** — pravým klikem na lead nebo v detailním panelu
8. **Přidejte poznámky** — v detailním panelu můžete psát vlastní poznámky ke každému leadu
9. **Exportujte** — klikněte na "Export do Excelu" pro uložení dat do .xlsx souboru
