import requests
import time

# Define the base URL for your Flask server
base_url = "http://127.0.0.1:5000"  # Change the port if your Flask app is running on a different port

# Send a query for website analysis
query_payload = {
    "query": "dummy_query",  # Add a dummy query field
    "mode": "website",
    "websites": [
        "https://neilpatel.com/blog",
        "https://bloggingtips.com/social-media-links/",
        "https://blog.hubspot.com/marketing",
        "https://powerdigitalmarketing.com/blog/"
    ],
    "google_analytics_view_id": "305510627",  # Replace with your provided Google Analytics view ID
    "social_media_platform": "facebook",
    "social_media_access_token": "EAAGGf1OrqvwBO2UfMbVhbOxE0zZCXRy7mOOBVPEz6LHZAuNf3ot0burr3pfyQDFSZCcf5HlMjtjtd6pEzHXiIQIIpHODygIjkGgZCtzZALc1NtvLSV0wzRU3CxoZCB6bQj6ckOPY9JrjaLivSMj8ZCPQuolZCDsTd8L2kJGdp4P98UGNQXMtzwOf9pWZCx5UnqkfaEZAKFaM9nLCXR0XmRp1AT9dQNpjpmZCVEutHxLAPb4baRLMD27mqugxqBD7ZAQORpIiBddcPEzc"
}

response = requests.post(f"{base_url}/query", json=query_payload)
print("POST Response:", response.json())

if response.status_code == 202:
    response_data = response.json()
    query_id = response_data.get('query_id')
    print('Query ID:', query_id)
    print('Waiting for response...')

    # Variable to keep track of waiting message
    waiting_message_shown = False

    while True:
        response = requests.get(f"{base_url}/response?query_id={query_id}")
        if response.status_code == 200:
            response_data = response.json()
            if 'response' in response_data:
                print('Response received:')
                print(response_data['response'])
                break
            else:
                print("No response received yet, waiting...")
                waiting_message_shown = True
        elif response.status_code == 202:
            if not waiting_message_shown:
                print("Response not ready yet, waiting...")
                waiting_message_shown = True
        else:
            print(f"Error retrieving response: {response.status_code}")
        time.sleep(5)
else:
    print('Error sending query:', response.json())

# Send a query for text generation
text_generation_payload = {
    "query": "Generate text based on this input."
}

response = requests.post(f"{base_url}/query", json=text_generation_payload)
print("POST Response:", response.json())

if response.status_code == 202:
    response_data = response.json()
    query_id = response_data.get('query_id')
    print('Query ID:', query_id)
    print('Waiting for text generation response...')

    # Reset waiting message flag
    waiting_message_shown = False

    while True:
        response = requests.get(f"{base_url}/response?query_id={query_id}")
        if response.status_code == 200:
            response_data = response.json()
            if 'response' in response_data:
                print('Generated Text:')
                print(response_data['response'])  # Assuming the response key holds the generated text
                break
            else:
                print("No text generation response received yet, waiting...")
                waiting_message_shown = True
        elif response.status_code == 202:
            if not waiting_message_shown:
                print("Response not ready yet, waiting...")
                waiting_message_shown = True
        else:
            print(f"Error retrieving text generation response: {response.status_code}")
        time.sleep(5)
else:
    print('Error sending text generation query:', response.json())
