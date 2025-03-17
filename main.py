import argparse
import logging
import sys
import json
from datetime import datetime

from scraper import LeafletScraper
from exporters import export_to_json, export_to_javascript

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Скрапер проспектів з сайту')
    parser.add_argument('-o', '--output', type=str, default='./output.json', help='Шлях до вихідного файлу')
    parser.add_argument('-v', '--verbose', action='store_true', help='Детальний вивід')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    from scraper import Scraper
    scraper_http = Scraper()
    
    try:
        logger.info("Attempting to retrieve prospectuses using HTTP requests...")
        leaflets = scraper_http.parse_leaflets()
        
        if leaflets:
            logger.info(f"Successfully received {len(leaflets)} of prospectuses using HTTP requests")
        else:
            logger.info("Attempting to retrieve prospectuses using Playwright...")
            from scraper import LeafletScraper
            scraper_playwright = LeafletScraper(verbose=args.verbose)
            leaflets = scraper_playwright.get_leaflets()
            
            if not leaflets:
                logger.error("Unable to obtain prospectuses")
                return 1
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for leaflet in leaflets:
            if "parsed_time" not in leaflet:
                leaflet["parsed_time"] = timestamp
        
        output_path = args.output
        output_js_path = output_path.replace('.json', '.js') if output_path.endswith('.json') else output_path + '.js'
        
        export_to_json(leaflets, output_path)
        logger.info(f"Data has been successfully exported to {output_path}")
        
        export_to_javascript(leaflets, output_js_path)
        logger.info(f"Data has been successfully exported to {output_js_path}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error while scraping: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
