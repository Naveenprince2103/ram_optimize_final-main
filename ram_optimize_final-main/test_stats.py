import requests
import json
import time

try:
    response = requests.get('http://127.0.0.1:5000/api/stats')
    data = response.json()
    print(json.dumps(data['system'], indent=2))
except Exception as e:
    print(e)
