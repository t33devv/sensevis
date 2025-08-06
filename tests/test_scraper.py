from sensevis.readdata import SenseScraper

if __name__ == "__main__":
    aPath = '/Users/tommyzhou/Desktop/endeavours/senseai_finalproject/src/sensevis'
    scraper = SenseScraper()
    scraper.write_bbox(aPath, 9)