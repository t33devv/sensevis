import json
import os
from sensevis.generateimage import ImageGenerator

if __name__ == "__main__":
    generator = ImageGenerator()
    
    # Read centroids from data.json in the project root
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_json_path = os.path.join(root_dir, 'data.json')
    
    with open(data_json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Convert data format: if it's [x, y], convert to [(x, y)]
    if isinstance(data, list) and len(data) == 2 and isinstance(data[0], (int, float)):
        # Single coordinate pair [x, y] -> [(x, y)]
        centroids = [(data[0], data[1])]
    elif isinstance(data, list) and all(isinstance(item, list) and len(item) == 2 for item in data):
        centroids = [(item[0], item[1]) for item in data]
    else:
        centroids = data
 
    file_name = "test"
    
    generator.generate_image(centroids, file_name)