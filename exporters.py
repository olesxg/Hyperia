"""
Модуль з класами для експорту даних в різні формати.
"""
import json
import logging
import os
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger('prospekt_scraper')


class JSONExporter:
    """
    Клас для експорту даних в JSON-формат.
    """
    
    def __init__(self, output_path: str = 'output.json'):
        """
        Ініціалізація експортера.
        
        Args:
            output_path: Шлях до файлу виводу
        """
        self.output_path = output_path
        
    def export(self, data: List[Dict[str, Any]]) -> bool:
        """
        Експортує дані в JSON-файл.
        
        Args:
            data: Список словників з даними проспектів
            
        Returns:
            bool: True, якщо експорт успішний, False в іншому випадку
        """
        try:
            # Конвертуємо відносний шлях в абсолютний
            absolute_path = os.path.abspath(self.output_path)
            logger.debug(f"Абсолютний шлях для збереження: {absolute_path}")
            
            # Створюємо директорію, якщо вона не існує
            output_dir = Path(absolute_path).parent
            if not output_dir.exists():
                logger.debug(f"Створення директорії: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
                
            # Записуємо дані в JSON-файл
            with open(absolute_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Дані успішно експортовано в {absolute_path}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка при експорті даних: {str(e)}")
            return False

def export_to_json(data, output_path):
    """
    Експорт даних в JSON файл.
    
    Args:
        data (list): Список об'єктів для експорту
        output_path (str): Шлях до вихідного файлу
    
    Returns:
        bool: True, якщо експорт успішний, False в іншому випадку
    """
    try:
        # Створюємо директорію, якщо вона не існує
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Експортуємо дані
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Помилка при експорті в JSON: {str(e)}")
        return False

def export_to_javascript(data, output_path):
    """
    Експорт даних в JavaScript файл.
    
    Args:
        data (list): Список об'єктів для експорту
        output_path (str): Шлях до вихідного файлу
    
    Returns:
        bool: True, якщо експорт успішний, False в іншому випадку
    """
    try:
        # Створюємо директорію, якщо вона не існує
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Конвертуємо дані в JavaScript
        js_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        # Оформлюємо в вигляді змінної
        js_content = f"// Автоматично згенеровано\n"
        js_content += f"// {os.path.basename(output_path)}\n\n"
        js_content += f"const leaflets = {js_data};\n\n"
        js_content += f"// Експортуємо змінну\n"
        js_content += f"export default leaflets;\n"
        
        # Записуємо в файл
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        return True
    except Exception as e:
        logger.error(f"Помилка при експорті в JavaScript: {str(e)}")
        return False 