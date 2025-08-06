# sensevis

a python tool for web scraping and generating pixelized images for senseAI 

## Installation

### For UV Users (Recommended)
```bash
uv pip install "git+https://github.com/t33devv/sensevis.git"

*installs 10-100x faster than pip*
```

### with traditional pip
```bash
pip install git+https://github.com/yourusername/sensevis.git
```

### development mode
```bash
git clone https://github.com/yourusername/sensevis.git
cd sensevis
uv pip install -e ".[dev]"  # Editable install with dev dependencies
```

## Quick Start
```bash
from sensevis.readdata import SenseScraper

# Basic usage
aPath = '/Users/tommyzhou/Desktop/endeavours/senseai_finalproject/src/sensevis'
scraper = SenseScraper()
scraper.write_bbox(aPath, 9)
```

## Documentation

### SenseScraper class:
```bash
SenseScraper().write_bbox(absolute_path, sensor_number)

# absolute_path is the Absolute Path (duh)
# sensor_number is the sensor number found on manage.sense-ai.org (duh)

# -> returns the bounding box(es) coordinates in data.json in the root folder
```

### ImageGenerator class:
```bash
ImageGenerator().generate_image(centroids, file_name)

# centroids is an array of tuples or arrays of length 2
# file_name is what you want to name the file

# -> returns file_name.png in /bounding_box_gen/ in the root directory
```

## Made with ❤️ by Tommy
