"""
A module that contains classes for representing prospectus data.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import re


class Leaflet:
    
    def __init__(
        self,
        title: str,
        thumbnail: str,
        shop_name: str,
        valid_from: str,
        valid_to: str,
        parsed_time: Optional[str] = None
    ):
        self.title = self._clean_string(title)
        self.thumbnail = thumbnail
        self.shop_name = self._clean_string(shop_name)
        
        if not self.shop_name or self.shop_name == self.title:
            parts = self.title.split(" - ", 1)
            if len(parts) > 1:
                self.shop_name = parts[0]
            else:
                words = self.title.split()
                if words:
                    self.shop_name = words[0]
                else:
                    self.shop_name = "Unknown"
        
        self.valid_from = self._validate_date(valid_from)
        self.valid_to = self._validate_date(valid_to)
        
        if parsed_time:
            self.parsed_time = parsed_time
        else:
            self.parsed_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _clean_string(self, text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r'\s+', ' ', text.strip())
        cleaned = re.sub(r'[^\w\s\-&,.]', '', cleaned)
        return cleaned
    
    def _validate_date(self, date_str: str) -> str:
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                current_year = datetime.now().year
                if date_obj.year > current_year + 1:
                    return date_str.replace(str(date_obj.year), str(current_year))
                
                return date_str
            except ValueError:
                return datetime.now().strftime("%Y-%m-%d")
        else:
            return datetime.now().strftime("%Y-%m-%d")
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "thumbnail": self.thumbnail,
            "shop_name": self.shop_name,
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "parsed_time": self.parsed_time
        } 
