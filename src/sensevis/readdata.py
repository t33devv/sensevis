import subprocess
import time

class SenseScraper:
    def write_bbox(self, aPath, sensor_num):
        print('hello')
        """Start both testpost.py and sendrequest.py for a specific sensor"""
        sensor_name = f"InnoWing-{sensor_num}"
        backend_path = aPath
        
        # Terminal 1: testpost.py
        testpost_cmd = f"cd '{backend_path}' && echo '{sensor_name}' | uv run _post.py"
        
        subprocess.Popen([
            'osascript', '-e', 
            f'tell app "Terminal" to do script "{testpost_cmd}"'
        ])
        
        time.sleep(0.5)
        
        # Terminal 2: sendrequest.py  
        sendrequest_cmd = f"cd '{backend_path}' && echo '{sensor_name}' | uv run _send.py"
        
        subprocess.Popen([
            'osascript', '-e',
            f'tell app "Terminal" to do script "{sendrequest_cmd}"'
        ])