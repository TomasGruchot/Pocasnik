from __future__ import annotations

import os
import platform
import random
import subprocess
import time
from datetime import datetime
from queue import Queue

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from clientradar.core.parser import DataParser
from clientradar.models.lead import Lead
from clientradar.models.search_config import SearchConfig


class GoogleMapsScraper:
    _USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    ]

    def __init__(self, config: SearchConfig, result_queue: Queue | None = None) -> None:
        self._config = config
        self._queue = result_queue
        self._parser = DataParser()
        self._stop_flag = False
        self._driver = None

    @staticmethod
    def _detect_chrome_version() -> int | None:
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["reg", "query",
                     r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
                     "/v", "version"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if "version" in line.lower() and "REG_SZ" in line:
                        ver_str = line.split("REG_SZ")[-1].strip()
                        return int(ver_str.split(".")[0])
            else:
                for binary in ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium"):
                    try:
                        result = subprocess.run(
                            [binary, "--version"],
                            capture_output=True, text=True, timeout=5,
                        )
                        if result.returncode == 0:
                            parts = result.stdout.strip().split()
                            for part in parts:
                                if "." in part:
                                    return int(part.split(".")[0])
                    except FileNotFoundError:
                        continue
        except Exception:
            pass
        return None

    @staticmethod
    def _kill_stale_chromedriver() -> None:
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/IM", "chromedriver.exe"],
                    capture_output=True, timeout=5,
                )
            else:
                subprocess.run(
                    ["pkill", "-f", "chromedriver"],
                    capture_output=True, timeout=5,
                )
        except Exception:
            pass

    def _init_driver(self) -> None:
        import undetected_chromedriver as uc

        chrome_major = self._detect_chrome_version()
        last_error: Exception | None = None

        for attempt in range(3):
            if attempt > 0:
                self._kill_stale_chromedriver()
                time.sleep(2)
                self._emit("progress", 0, 0, f"Pokus {attempt + 1}/3 spustit Chrome…")

            try:
                options = uc.ChromeOptions()
                width = random.randint(1280, 1440)
                height = random.randint(800, 900)
                options.add_argument(f"--window-size={width},{height}")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_argument("--no-first-run")
                options.add_argument("--no-default-browser-check")
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument(f"--user-agent={random.choice(self._USER_AGENTS)}")
                if self._config.headless:
                    options.add_argument("--headless=new")

                kwargs: dict = {
                    "options": options,
                    "use_subprocess": True,
                    "driver_executable_path": None,
                }
                if chrome_major:
                    kwargs["version_main"] = chrome_major

                self._driver = uc.Chrome(**kwargs)
                self._driver.set_page_load_timeout(30)
                return
            except Exception as exc:
                last_error = exc
                try:
                    if self._driver:
                        self._driver.quit()
                except Exception:
                    pass
                self._driver = None

        raise last_error or RuntimeError("Nepodařilo se spustit Chrome po 3 pokusech.")

    def _emit(self, msg_type: str, *args) -> None:
        if self._queue:
            self._queue.put((msg_type, *args))

    def search(self) -> list[Lead]:
        try:
            self._emit("progress", 0, 0, "Spouštím Chrome…")
            self._init_driver()
        except Exception as exc:
            msg = str(exc)
            chrome_ver = self._detect_chrome_version()
            hint = f" (Chrome {chrome_ver})" if chrome_ver else ""
            self._emit(
                "error",
                f"Nelze spustit Chrome{hint}: {msg[:120]}",
            )
            return []

        try:
            self._emit("progress", 0, 0, "Otevírám Google Maps…")
            self._driver.get("https://www.google.com/maps")

            self._accept_cookies()

            wait = WebDriverWait(self._driver, 15)
            search_box = wait.until(
                EC.presence_of_element_located((By.ID, "searchboxinput"))
            )
            search_box.clear()
            search_box.send_keys(self._config.search_query())
            search_box.send_keys(Keys.ENTER)

            self._emit("progress", 0, 0, "Čekám na výsledky…")
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'div[role="feed"], div.section-result')
                )
            )

            urls = self._collect_listing_urls()
            if self._stop_flag:
                self._emit("done", 0)
                return []

            leads = self._scrape_all_listings(urls)
            self._emit("done", len(leads))
            return leads
        except Exception as exc:
            self._emit("error", str(exc))
            return []
        finally:
            self.close()

    def _accept_cookies(self) -> None:
        try:
            wait = WebDriverWait(self._driver, 5)
            accept_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     'button[aria-label*="Accept"], '
                     'button[aria-label*="Přijmout"], '
                     'button[aria-label*="Souhlasím"], '
                     'form:nth-child(2) button')
                )
            )
            accept_btn.click()
            WebDriverWait(self._driver, 3).until(EC.staleness_of(accept_btn))
        except Exception:
            pass

    def _collect_listing_urls(self) -> list[str]:
        self._emit("progress", 0, 0, "Sbírám výsledky…")
        urls: list[str] = []
        seen: set[str] = set()
        no_new_count = 0

        feed = None
        try:
            feed = WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
            )
        except Exception:
            pass

        while len(urls) < self._config.max_results and not self._stop_flag:
            links = self._driver.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')
            new_found = False
            for link in links:
                href = link.get_attribute("href")
                if href and href not in seen and "/maps/place/" in href:
                    seen.add(href)
                    urls.append(href)
                    new_found = True
                    if len(urls) >= self._config.max_results:
                        break

            self._emit("progress", len(urls), self._config.max_results, f"Nalezeno {len(urls)} výsledků…")

            if not new_found:
                no_new_count += 1
                if no_new_count >= 3:
                    break
            else:
                no_new_count = 0

            if feed and len(urls) < self._config.max_results:
                try:
                    self._driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight", feed
                    )
                    WebDriverWait(self._driver, 4).until(
                        lambda d: len(d.find_elements(By.CSS_SELECTOR, 'a[href*="/maps/place/"]')) > len(seen) - 1
                    )
                except Exception:
                    pass

        return urls[: self._config.max_results]

    def _scrape_all_listings(self, urls: list[str]) -> list[Lead]:
        leads: list[Lead] = []
        total = len(urls)
        for idx, url in enumerate(urls):
            if self._stop_flag:
                break
            self._emit("progress", idx + 1, total, f"Scrapuji {idx + 1}/{total}…")
            lead = self._scrape_single(url)
            if lead:
                if self._config.fetch_emails and lead.website:
                    self._emit("progress", idx + 1, total, f"Hledám email: {lead.name}…")
                    lead.email = self._parser.extract_email_from_website(lead.website)
                leads.append(lead)
                self._emit("result", lead)
            delay = random.uniform(1.5, 3.5)
            self._interruptible_wait(delay)
        return leads

    def _interruptible_wait(self, seconds: float) -> None:
        elapsed = 0.0
        step = 0.1
        while elapsed < seconds and not self._stop_flag:
            time.sleep(step)
            elapsed += step

    def _scrape_single(self, url: str) -> Lead | None:
        for attempt in range(3):
            if self._stop_flag:
                return None
            try:
                self._driver.get(url)
                WebDriverWait(self._driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, 'h1, [data-header-feature-id]')
                    )
                )

                name = self._safe_get(By.CSS_SELECTOR, "h1")
                if not name:
                    continue

                category = self._safe_get(
                    By.CSS_SELECTOR,
                    'button[jsaction*="category"], span.DkEaL'
                )

                address = self._safe_get(
                    By.CSS_SELECTOR,
                    'button[data-item-id="address"] div.fontBodyMedium, '
                    'button[data-item-id*="address"] .Io6YTe'
                )

                city = self._extract_city(address)

                phone = self._safe_get(
                    By.CSS_SELECTOR,
                    'button[data-item-id*="phone"] div.fontBodyMedium, '
                    'button[data-tooltip="Zkopírovat telefonní číslo"] .Io6YTe, '
                    'button[data-item-id*="phone"] .Io6YTe'
                )
                phone = self._parser.clean_phone(phone)

                website = self._safe_get(
                    By.CSS_SELECTOR,
                    'a[data-item-id="authority"] div.fontBodyMedium, '
                    'a[data-item-id="authority"] .Io6YTe',
                )
                if website and not website.startswith("http"):
                    website_link = self._safe_get(
                        By.CSS_SELECTOR,
                        'a[data-item-id="authority"]',
                        attribute="href",
                    )
                    website = website_link if website_link else f"https://{website}"

                rating_raw = self._safe_get(
                    By.CSS_SELECTOR,
                    'div.fontDisplayLarge, span.ceNzKf, span[aria-hidden="true"]'
                )
                rating = self._parser.normalize_rating(rating_raw)

                review_raw = self._safe_get(
                    By.CSS_SELECTOR,
                    'span[aria-label*="recen"], span[aria-label*="review"], button[jsaction*="reviews"] span'
                )
                review_count = self._parser.parse_review_count(review_raw)

                return Lead(
                    id=None,
                    name=name,
                    category=category,
                    address=address,
                    city=city,
                    phone=phone,
                    website=website,
                    email="",
                    rating=rating,
                    review_count=review_count,
                    google_maps_url=url,
                    scraped_at=datetime.now(),
                )
            except Exception:
                if attempt < 2:
                    self._interruptible_wait(2.0)
                continue
        return None

    def _extract_city(self, address: str) -> str:
        if not address:
            return ""
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 2:
            city_part = parts[-1].strip()
            cleaned = "".join(c for c in city_part if not c.isdigit()).strip()
            return cleaned if cleaned else city_part
        return parts[0] if parts else ""

    def _safe_get(self, by, selector: str, attribute: str = "text") -> str:
        try:
            el = self._driver.find_element(by, selector)
            if attribute == "text":
                return (el.text or "").strip()
            return (el.get_attribute(attribute) or "").strip()
        except Exception:
            return ""

    def stop(self) -> None:
        self._stop_flag = True

    def close(self) -> None:
        driver = self._driver
        self._driver = None
        if driver:
            try:
                driver.quit()
            except OSError:
                pass
            except Exception:
                pass
            finally:
                self._kill_stale_chromedriver()
