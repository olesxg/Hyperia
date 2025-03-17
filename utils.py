"""
A module with utilities for date processing and other auxiliary functionality.
"""
import re
import logging
from datetime import datetime
from typing import Tuple, Optional

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('prospekt_scraper')


def parse_date_range(date_text: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        current_year = datetime.now().year
        date_pattern = r'(\d{2}\.\d{2}\.\d{4})'
        dates = re.findall(date_pattern, date_text)
        
        if len(dates) >= 2:
            from_date = datetime.strptime(dates[0], "%d.%m.%Y")
            to_date = datetime.strptime(dates[1], "%d.%m.%Y")
            if from_date.year > current_year + 1 or to_date.year > current_year + 1:
                logger.warning(f"Dates with a future year are detected: {dates[0]}, {dates[1]}. I use the current year.")
                from_date = from_date.replace(year=current_year)
                to_date = to_date.replace(year=current_year)
            
            valid_from = from_date.strftime("%Y-%m-%d")
            valid_to = to_date.strftime("%Y-%m-%d")
            return valid_from, valid_to
        else:
            short_date_pattern = r'(\d{2}\.\d{2})'
            short_dates = re.findall(short_date_pattern, date_text)
            
            if len(short_dates) >= 2:
                from_date = datetime.strptime(f"{short_dates[0]}.{current_year}", "%d.%m.%Y")
                to_date = datetime.strptime(f"{short_dates[1]}.{current_year}", "%d.%m.%Y")
                
                valid_from = from_date.strftime("%Y-%m-%d")
                valid_to = to_date.strftime("%Y-%m-%d")
                return valid_from, valid_to
                
            logger.warning(f"Не вдалося розпізнати дві дати у тексті: {date_text}")
            today = datetime.now()
            valid_from = today.strftime("%Y-%m-%d")
            valid_to = (today.replace(day=today.day+7)).strftime("%Y-%m-%d")
            return valid_from, valid_to
            
    except Exception as e:
        logger.error(f"Error parsing dates from text '{date_text}': {str(e)}")
        today = datetime.now()
        valid_from = today.strftime("%Y-%m-%d")
        valid_to = (today.replace(day=today.day+7)).strftime("%Y-%m-%d")
        return valid_from, valid_to


def validate_url(url: str) -> str:
    if not url:
        return ""

    if url and not url.startswith(('http://', 'https://')):
        url = 'https:' + url if url.startswith('//') else 'https://' + url
        
    return url 
