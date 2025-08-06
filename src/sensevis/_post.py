import asyncio
import websockets
import json

from _upscaler import generate_image_from_centroids
from _upscaler import generate_blank

from sensevis import SenseScraper

# CLIENT_ID = "3aeba6d2-6abe-4d90-bbfc-4bc779c32eb4"
BASE_CLIENT_ID = "python-client"

async def connect_and_receive(sensor_name):
    # Create unique client ID for each sensor
    CLIENT_ID = f"{BASE_CLIENT_ID}-{sensor_name}"
    uri = f"wss://dev.sense-ai.org/ws/register?clientId={CLIENT_ID}"
    print(f"Connecting with Client ID: {CLIENT_ID}")
    async with websockets.connect(uri) as websocket:
        try:
            while True:
                # Receive a message from the server
                response = await websocket.recv()
                jsondoc = json.loads(response)
                bboxes = jsondoc.get('payload', {}).get('bboxes')
                if bboxes is not None:
                    centroids = []
                    for bbox in bboxes:
                        if len(bbox) >= 3:
                            centroid = bbox[-3:-1]  # 2nd last and 3rd last values
                            centroids.append(centroid)
                    if centroids:
                        write_json(centroids)
                        break
                    else:
                        write_json([0, 0])
                        break
                        
        except Exception as e:
            print(f'Error, exiting: {e}')

def clear_json():
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_json_path = os.path.join(root_dir, 'data.json')
    with open(data_json_path, 'w') as file:
        file.truncate(0)

def write_json(bbox):
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_json_path = os.path.join(root_dir, 'data.json')
    with open(data_json_path, 'w', encoding='utf-8') as file:
        json.dump(bbox, file)

# Run the client
if __name__ == "__main__":
    userInput = input("Enter the sensor name: ")
    asyncio.run(connect_and_receive(userInput))
