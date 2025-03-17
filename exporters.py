"""
A module with classes for exporting data to various formats.
"""
import json
import logging
import os
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger('prospekt_scraper')


class JSONExporter:
    """
    A class for exporting data to JSON format.
    """
    
    def __init__(self, output_path: str = 'output.json'):
        self.output_path = output_path
       
    def export(self, data: List[Dict[str, Any]]) -> bool:
        try:
            absolute_path = os.path.abspath(self.output_path)
            logger.debug(f"Абсолютний шлях для збереження: {absolute_path}")
            
            output_dir = Path(absolute_path).parent
            if not output_dir.exists():
                logger.debug(f"Створення директорії: {output_dir}")
                output_dir.mkdir(parents=True, exist_ok=True)
                
            with open(absolute_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Дані успішно експортовано в {absolute_path}")
            return True
            
        except Exception as e:
            logger.error(f"Помилка при експорті даних: {str(e)}")
            return False

def export_to_json(data, output_path):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return True
    except Exception as e:
        logger.error(f"Error when exporting to JSON: {str(e)}")
        return False

def export_to_javascript(data, output_path):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        js_data = json.dumps(data, ensure_ascii=False, indent=2)
        
        js_content = f"// Automatically generated\n"
        js_content += f"// {os.path.basename(output_path)}\n\n"
        js_content += f"const leaflets = {js_data};\n\n"
        js_content += f"// Exporting a variable\n"
        js_content += f"export default leaflets;\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        return True
    except Exception as e:
        logger.error(f"Error exporting to JavaScript: {str(e)}")
        return False 
