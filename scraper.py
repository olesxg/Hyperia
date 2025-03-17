"""
A module with classes for downloading and parsing web pages.
"""
import time
import logging
import requests
from typing import List, Optional, Dict, Any
import json
import os
import asyncio
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
from playwright.async_api import async_playwright
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import httpx
from models import Leaflet
from utils import parse_date_range, validate_url

logger = logging.getLogger('prospekt_scraper')


class Scraper:
    def __init__(self, base_url: str = 'https://www.prospektmaschine.de/hypermarkte/'):
        self.base_url = base_url
        self.session = self._create_session()
        # Список відомих супермаркетів для розпізнавання
        self.known_shops = [
            "Aldi", "Lidl", "Rewe", "Edeka", "Kaufland", "Penny", "Netto", 
            "Real", "Metro", "Globus", "Hit", "Norma", "Marktkauf", "Famila", 
            "Bünting", "Combi", "Tegut", "Kaisers", "Tengelmann", "V-Markt",
            "dm", "Rossmann", "Müller", "Alnatura", "Denn's", "Basic", "Bio Company",
            "Wasgau", "Walmart", "Dohle", "Rewe Center", "E-Center", "EDEKA"
        ]
        
    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
        
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            logger.info(f"Завантаження сторінки: {url}")
            time.sleep(random.uniform(2, 5))         
            response = self.session.get(url, timeout=15)
            response.raise_for_status()       
            with open('debug.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.debug(f"Збережено HTML для відлагодження в debug.html")
            
            return BeautifulSoup(response.text, 'lxml')
            
        except requests.RequestException as e:
            logger.error(f"Error loading page {url}: {str(e)}")
            return None
            
    def _extract_shop_name(self, title: str, texts: List[str]) -> str:
        for shop in self.known_shops:
            if shop.lower() in title.lower():
                return shop
        for text in texts:
            for shop in self.known_shops:
                if shop.lower() in text.lower():
                    return shop
        if " - " in title:
            shop_part = title.split(" - ")[0]
            return shop_part
        for text in texts:
            if "Geschäft" in text:
                parts = text.split("Geschäft")
                if len(parts) > 1:
                    return parts[1].strip().rstrip(',.:;')
                    
        words = title.split()
        if len(words) >= 3:
            return " ".join(words[:2])
        elif len(words) > 0:
            return words[0]
        
        return "Unknown Shop"
    
    def _get_image_url(self, img_tag, base_url: str) -> str:
        if not img_tag:
            return ""
        for attr in ["src", "data-src", "data-lazy-src", "data-original"]:
            img_src = img_tag.get(attr)
            if img_src:
                if not img_src.startswith(("http://", "https://")):
                    img_src = urljoin(base_url, img_src)
                return img_src
                
        srcset = img_tag.get("srcset")
        if srcset:
            urls = re.findall(r'([^\s,]+)', srcset)
            if urls:
                url = urls[0]
                if not url.startswith(("http://", "https://")):
                    url = urljoin(base_url, url)
                return url
                
        return ""

    def parse_leaflets(self) -> List[Dict[str, Any]]:
        soup = self.get_page(self.base_url)
        if not soup:
            logger.error("Не вдалося завантажити основну сторінку")
            return []
            
        leaflets = []
        
        try:
            with open('full_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            logger.debug("Збережено повний HTML в full_page.html")
            prospekt_blocks = []
            vorschau_blocks = soup.find_all(lambda tag: tag.name and "Vorschau" in tag.text and "Prospekt" in tag.text)
            if vorschau_blocks:
                logger.info(f"Знайдено {len(vorschau_blocks)} блоків з текстом 'Vorschau von dem Prospekt'")
                prospekt_blocks.extend(vorschau_blocks)
            zeige_buttons = soup.find_all(lambda tag: tag.name and "Zeige den Prospekt" in tag.text)
            if zeige_buttons:
                logger.info(f"Знайдено {len(zeige_buttons)} кнопок 'Zeige den Prospekt'")
                for button in zeige_buttons:
                    parent = button.parent
                    if parent and parent not in prospekt_blocks:
                        prospekt_blocks.append(parent)
            selectors = [
                "div.item", "article", ".aktuelle-prospekte-item", 
                ".prospekte-block", ".grid-item", ".aktuelle-prospekte .item",
                ".leaflet-preview-container", ".prospekt-container", "article.leaflet",
                "div[class*='leaflet']", "div[class*='prospekt']",
                ".col-md-3", ".col-sm-4"
            ]
            
            for selector in selectors:
                blocks = soup.select(selector)
                if blocks:
                    logger.info(f"Знайдено {len(blocks)} блоків з селектором: {selector}")
                    for block in blocks:
                        if block not in prospekt_blocks:
                            prospekt_blocks.append(block)
            logger.info(f"Загалом знайдено {len(prospekt_blocks)} блоків проспектів для обробки")
            
            for i, block in enumerate(prospekt_blocks):
                try:
                    logger.debug(f"Обробка блоку {i+1}:\n{block}")
                    img = block.find("img")
                    img_src = self._get_image_url(img, self.base_url) if img else ""
                    if not img_src:
                        img_src = "https://www.prospektmaschine.de/static/images/default-leaflet.jpg"
                    texts = [t.strip() for t in block.stripped_strings if t.strip()]
                    if not texts:
                        continue
                    bold_text = block.find(["b", "strong", "h2", "h3", "h4"])
                    title = bold_text.text.strip() if bold_text else texts[0]
                    shop_name = self._extract_shop_name(title, texts)
                    date_text = ""
                    for text in texts:
                        if text.count('.') >= 2:  
                            date_text = text
                            break
                    
                    valid_from, valid_to = parse_date_range(date_text)
                    
                    leaflet = Leaflet(
                        title=title,
                        thumbnail=img_src,
                        shop_name=shop_name,
                        valid_from=valid_from,
                        valid_to=valid_to
                    )
                    
                    leaflets.append(leaflet.to_dict())
                    logger.info(f"Added a prospectus: {title} ({valid_from} - {valid_to})")
                    
                except Exception as e:
                    logger.error(f"Error processing a prospectus block {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing prospectuses: {str(e)}")
        if not leaflets:
            logger.warning("No prospectus found with HTTP method.")
            
        return leaflets


class LeafletScraper(Scraper):
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            html = self.get_page_playwright(url)
            if html:
                return BeautifulSoup(html, 'html.parser')
            return None
        except Exception as e:
            logger.error(f"Error when receiving a page {url}: {str(e)}")
            return None
    
    def get_page_playwright(self, url: str) -> Optional[str]:
        try:
            with async_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser_context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="de-DE",
                    viewport={"width": 1920, "height": 1080},
                    extra_http_headers={
                        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7"
                    }
                )
                
                page = browser_context.new_page()
                page.set_default_timeout(60000)  
                
                logger.info(f"Відкриваю сторінку {url}")
                response = page.goto(url, wait_until="networkidle")
                
                if not response:
                    logger.error("Page loading error")
                    browser.close()
                    return None
                
                if response.status >= 400:
                    logger.error(f"HTTP error: {response.status}")
                    browser.close()
                    return None
                
                time.sleep(random.uniform(1.0, 2.0))
                self._scroll_page(page)
                html = page.content()
                with open('debug_playwright.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.debug("Saved HTML from Playwright to debug_playwright.html")
                
                browser.close()
                return html
                
        except Exception as e:
            logger.error(f"Error using Playwright: {str(e)}")
            return None
            
    def _scroll_page(self, page):
        try:
            height = page.evaluate("document.body.scrollHeight")
            logger.info("Прокручую сторінку для завантаження контенту")
            
            steps = 10
            for i in range(1, steps + 1):
                page.evaluate(f"window.scrollTo(0, {height * i / steps})")
                time.sleep(random.uniform(0.5, 1.0))
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.7)")
            time.sleep(0.5)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error when scrolling the page: {str(e)}")
    
    def parse_leaflets(self) -> List[Dict[str, Any]]:
        html = self.get_page_playwright(self.base_url)
        if not html:
            logger.error("The page could not be retrieved")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        leaflets = []
        
        try:
            with async_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser_context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="de-DE",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = browser_context.new_page()
                page.set_default_timeout(60000)  
                logger.info(f"Відкриваю сторінку {self.base_url}")
                response = page.goto(self.base_url, wait_until="networkidle")
                
                if not response or response.status >= 400:
                    logger.error(f"Error loading page: {response and response.status}")
                    browser.close()
                    return []
                time.sleep(random.uniform(2.0, 3.0))
                self._scroll_page(page)
                selector_groups = [
                    ["//div[contains(text(), 'Prospekt')]", "//div[contains(text(), 'Vorschau')]"],
                    ["//a[contains(text(), 'Zeige den Prospekt')]", "//button[contains(text(), 'Zeige den Prospekt')]"],
                    [".aktuelle-prospekte-item", ".prospekt-item", ".prospektitem"],
                    [".col-sm-4 .item", ".col-md-3 .item", ".grid-item"],
                    ["article.module", "article.item", "div.item"],
                    [".row .prospekt-container", ".leaflet-preview-container"]
                ]
                for selector_group in selector_groups:
                    for selector in selector_group:
                        try:
                            logger.info(f"Searching for prospectuses by selector: {selector}")
                            
                            if selector.startswith('//'):
        
                                items = page.locator(selector)
                            else:
                                items = page.locator(selector)
                                
                            count = items.count()
                            if count > 0:
                                logger.info(f"Found {count} items by selector {selector}")
                                for i in range(min(count, 10)):
                                    try:
                                        item = items.nth(i)
                                        item_html = item.evaluate("el => el.outerHTML")
                                        item_soup = BeautifulSoup(item_html, 'html.parser')
                                        logger.debug(f"Елемент {i+1}: {item_html[:200]}...")
                                        img = item_soup.find("img")
                                        img_src = self._get_image_url(img, self.base_url) if img else ""
                                        texts = [t.strip() for t in item_soup.stripped_strings if t.strip()]
                                        
                                        if not texts and not img_src:
                                            continue
                                        shop_name = self._extract_shop_name(item_soup.text, texts)
                                        title = item_soup.text.strip()

                                        date_text = ""
                                        for text in texts:
                                            if text.count('.') >= 4:  
                                                date_text = text
                                                break
                                                
                                        valid_from, valid_to = parse_date_range(date_text)
                                        if not valid_from or not valid_to:
                                            date_match = re.findall(r'\d{2}\.\d{2}\.\d{4}', ' '.join(texts))
                                            if len(date_match) >= 2:
                                                try:
                                                    date_from = datetime.strptime(date_match[0], "%d.%m.%Y")
                                                    date_to = datetime.strptime(date_match[1], "%d.%m.%Y")
                                                    valid_from = date_from.strftime("%Y-%m-%d")
                                                    valid_to = date_to.strftime("%Y-%m-%d")
                                                except Exception as e:
                                                    logger.error(f"Помилка при парсингу дат: {str(e)}")
                                                    valid_from = datetime.now().strftime("%Y-%m-%d")
                                                    valid_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                                            else:
                                                valid_from = datetime.now().strftime("%Y-%m-%d")
                                                valid_to = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                                                

                                        leaflet = Leaflet(
                                            title=title,
                                            thumbnail=img_src or "https://example.com/default.jpg",
                                            shop_name=shop_name,
                                            valid_from=valid_from,
                                            valid_to=valid_to
                                        )
                                        
                                        leaflet_dict = leaflet.to_dict()
                                        if leaflet_dict not in leaflets: 
                                            leaflets.append(leaflet_dict)
                                            logger.info(f"Додано проспект: {title} ({valid_from} - {valid_to})")
                                        
                                    except Exception as e:
                                        logger.error(f"Error processing an element {i+1}: {str(e)}")
                                        continue
                                        
                            if count > 0 and leaflets:
                                break
                                
                        except Exception as e:
                            logger.error(f"Error when using the selector {selector}: {str(e)}")
                            continue
                            
                    if leaflets:
                        break
                if not leaflets:
                    logger.info("No prospectuses found by selectors, search by images")
                    
                    images = page.locator("img")
                    count = images.count()
                    logger.info(f"Foung {count} images on the page")
                    
                    suitable_images = []
                    for i in range(count):
                        try:
                            img = images.nth(i)
                            is_visible = img.is_visible()
                            if not is_visible:
                                continue
                            src = img.get_attribute("src") or ""
                            alt = img.get_attribute("alt") or ""
                            if not src:
                                continue
                            keywords = ["prospekt", "leaflet", "flyer", "katalog", "angebot", "aktion"]
                            if any(keyword in src.lower() or keyword in alt.lower() for keyword in keywords):
                                suitable_images.append({
                                    "src": src,
                                    "alt": alt,
                                    "index": i
                                })
                                logger.debug(f"A suitable image {i}: {src}")
                        except Exception as e:
                            logger.error(f"Error checking the image {i}: {str(e)}")
                            continue
                            
                    logger.info(f"Found {len(suitable_images)} suitable images")
                    for img_info in suitable_images[:10]:  
                        try:
                            img_src = self._get_image_url(img_info["img"], self.base_url)
                            shop_name = img_info["alt"] or "Unknown store"
                            leaflet = Leaflet(
                                title=f"Prospectus {shop_name}",
                                thumbnail=img_src,
                                shop_name=shop_name,
                                valid_from=datetime.now().strftime("%Y-%m-%d"),
                                valid_to=(datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                            )
                            
                            leaflet_dict = leaflet.to_dict()
                            if leaflet_dict not in leaflets:  
                                leaflets.append(leaflet_dict)
                                logger.info(f"Added a prospectus from the image: {shop_name}")
                            
                        except Exception as e:
                            logger.error(f"Image processing error {img_info['index']}: {str(e)}")
                            continue
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Error parsing prospectuses from Playwright: {str(e)}")
        
        if not leaflets:
            logger.warning("No prospectus found. It is recommended to change the URL or scraping method.")
        
        return leaflets
    def _get_test_leaflets(self):
        self.logger.info("Downloading test data...")
        test_leaflets = [
            Leaflet(
                title="Aldi Nord Акції цього тижня",
                thumbnail="https://example.com/aldi.jpg",
                shop_name="Aldi",
                valid_from="2025-03-18",
                valid_to="2025-03-24"
            ),
            Leaflet(
                title="EDEKA Special offers",
                thumbnail="https://example.com/edeka.jpg",
                shop_name="EDEKA",
                valid_from="2025-03-15",
                valid_to="2025-03-21"
            ),
            Leaflet(
                title="NORMA New catalog",
                thumbnail="https://example.com/norma.jpg",
                shop_name="NORMA",
                valid_from="2025-03-17",
                valid_to="2025-03-23"
            ),
            Leaflet(
                title="Lidl Promotional products",
                thumbnail="https://example.com/lidl.jpg",
                shop_name="Lidl",
                valid_from="2025-03-19",
                valid_to="2025-03-25"
            ),
            Leaflet(
                title="Netto Special offers",
                thumbnail="https://example.com/netto.jpg",
                shop_name="Netto",
                valid_from="2025-03-16",
                valid_to="2025-03-22"
            )
        ]
        
        self.logger.info(f"Downloaded {len(test_leaflets)} of test leaflets")
        return [leaflet.to_dict() for leaflet in test_leaflets] 
