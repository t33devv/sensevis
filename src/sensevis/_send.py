import httpx
import urllib.parse

def send_request(sensor_name = "InnoWing-12"):
    # Base URL and query parameters
    base_url = "https://dev.sense-ai.org/api/subscribe/occupancy"
    topic = f"senseai/{sensor_name}/tx"
    
    # URL encode the topic parameter
    encoded_topic = urllib.parse.quote(topic)
    
    # Construct the full URL with query parameters
    url = f"{base_url}?topic={encoded_topic}"
    
    # Create unique client ID for each sensor
    client_id = f"python-client-{sensor_name}"
    print(f"Using Client ID: {client_id}")
    
    # Headers
    headers = {
        'X-Client-Id': client_id
    }
    
    try:
        # Make the POST request
        with httpx.Client() as client:
            response = client.post(url, headers=headers)
            
            # Print response details
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Body: {response.text}")
            
            return response
            
    except httpx.RequestError as e:
        print(f"Error making request: {e}")
        return None

if __name__ == "__main__":
    sensor_name = input("Enter sensor name: ")
    if (sensor_name == ""):
        send_request()
    else:
        send_request(sensor_name)
