import requests
import time

# Define the base URL for your Flask server
base_url = "http://127.0.0.1:5000"  # Change the port if your Flask app is running on a different port

query_payload = {"query": "https://www.bluebiz.com", "mode": "website"}
# query_payload = {"query": "Bluebiz is the corporate loyalty programme of Air France, KLM and partner airlines. Reward your company with free tickets.", "mode": "text"}
response = requests.post(f"{base_url}/query", json=query_payload)
# print("POST Response:", response.json())

if response.status_code == 202:
    response_data = response.json()
    query_id = response_data['query_id']
    print('Query ID', query_id)
    print('Getting Results from Model')
    while True:
        response = requests.get(f"{base_url}/response?query_id={query_id}")
        if response.status_code == 200:
            break
        time.sleep(5)
        print('Please be patient')
    response_data = response.json()
    print(response_data['response'])
else:
    print('Error Sending Query')
