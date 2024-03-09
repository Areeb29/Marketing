import threading
from flask import Flask, request, jsonify
from ctransformers import AutoModelForCausalLM
import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# Replace with your actual Google Analytics API key
GA_API_KEY = "AIzaSyAiVPX8kKzxIzZJU_tkqC4DvtJoUFZYGXk"

# Replace with your chosen social media platform's API keys
FACEBOOK_API_KEY = "facc316128c0e8947cf0993ec330168c"
TWITTER_API_KEY = "enmI6dwCTZu2di8EU4KYmS1MB"
LINKEDIN_API_KEY = "h4Q4thw3dVfCQN5u"

# Replace Facebook access token with your provided token
FACEBOOK_ACCESS_TOKEN = "EAAGGf1OrqvwBO2UfMbVhbOxE0zZCXRy7mOOBVPEz6LHZAuNf3ot0burr3pfyQDFSZCcf5HlMjtjtd6pEzHXiIQIIpHODygIjkGgZCtzZALc1NtvLSV0wzRU3CxoZCB6bQj6ckOPY9JrjaLivSMj8ZCPQuolZCDsTd8L2kJGdp4P98UGNQXMtzwOf9pWZCx5UnqkfaEZAKFaM9nLCXR0XmRp1AT9dQNpjpmZCVEutHxLAPb4baRLMD27mqugxqBD7ZAQORpIiBddcPEzc"

# Set gpu_layers to the number of layers to offload to GPU. Set to 0 if no GPU acceleration is available on your system.
model = AutoModelForCausalLM.from_pretrained("TheBloke/Mistral-7B-v0.1-GGUF", model_file="mistral-7b-v0.1.Q5_K_M.gguf", model_type="mistral", gpu_layers=0, max_new_tokens=512, context_length=1024)

# Global lock for thread safety
thread_lock = threading.Lock()

# Placeholder function for fetching data from Google Analytics API
def get_google_analytics_data(view_id, ga_api_key):
    """
    Fetches comprehensive data from the Google Analytics API.

    Args:
        view_id (str): The ID of the Google Analytics view (e.g., "ga:12345678").
        ga_api_key (str): Your Google Analytics API key.

    Returns:
        dict or None: A dictionary containing the fetched data or None if an error occurs.
    """

    base_url = "https://www.googleapis.com/analytics/reporting/v4/reports"
    params = {
        "access_token": ga_api_key,
        # Replace with your desired metrics and dimensions
        "metrics": ["ga:sessions", "ga:users", "ga:pageviews", "ga:bounceRate"],
        "dimensions": ["ga:source", "ga:medium"],
        "start-date": "7DaysAgo",
        "end-date": "yesterday",
        "filters": "ga:sessionSource!=(direct)",  # Filter out direct traffic
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise an exception if not successful

        data = response.json()
        if data.get("reports"):
            report = data["reports"][0]
            rows = report.get("data", {}).get("rows", [])
            # Process rows and return the data in a desired format
            return {  # Example data structure
                "sessions": rows[0].get("metrics")[0].get("values")[0],
                "users": rows[0].get("metrics")[1].get("values")[0],
            }
        else:
            print("No data found in Google Analytics response.")
            return None

    except requests.exceptions.RequestException as e:
        # Remove or comment out the print statement below
        # print(f"Error fetching Google Analytics data: {e}")
        return None


def get_social_media_data(platform, access_token):
    """
    Fetches comprehensive data from a social media platform (example implementation for Facebook).

    Args:
        platform (str): The social media platform name (e.g., "facebook").
        access_token (str): Your access token for the specified platform.

    Returns:
        dict or None: A dictionary containing the fetched data or None if an error occurs.
    """

    if platform.lower() == "facebook":
        base_url = "https://graph.facebook.com/v13.0/me/insights"
        params = {
            "access_token": access_token,
            "fields": "likes,shares,comments,reach",
            "period": "7days"  # Example period
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "likes": data.get("data", {}).get(0, {}).get("values", [0])[0].get("value"),
                "shares": data.get("data", {}).get(1, {}).get("values", [0])[0].get("value"),
                "comments": data.get("data", {}).get(2, {}).get("values", [0])[0].get("value"),
                "reach": data.get("data", {}).get(3, {}).get("values", [0])[0].get("value"),
            }

        except requests.exceptions.RequestException as e:
            # Remove or comment out the print statement below
            # print(f"Error fetching social media data: {e}")
            return None

    else:
        # Implement logic for other social media platforms if needed
        print(f"Unsupported platform: {platform}")
        return None

# Function to fetch website details
def get_website_details(url):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        result = f"URL: {url}\n"
        try:
            title = soup.title.string.strip() if soup.title else "No title found"
            result += f'Title: {title}\n'
        except:
            pass

        try:
            meta_description = soup.find("meta", {"name": "description"})
            description = meta_description["content"] if meta_description else "No description found"
            result += f'Description: {description}\n'
        except:
            pass
        
        try:
            categories = [tag.text.strip() for tag in soup.find_all("a", class_="category-class")]
            result += f'Categories: {categories}\n'
        except:
            pass
        return result
    else:
        # Remove or comment out the print statement below
        # print(f"Error: Unable to fetch the website. Status code: {response.status_code}")
        return None

# Function to generate model response
def generate_response(query):
    global thread_lock
    with thread_lock:
        response = model(query)
    return response

# Function to generate text using GPT-2
def generate_text(text):
    # Determine an appropriate maximum length based on your requirements
    max_length = 4000  # Adjust this value as needed

    # Generate text using GPT-2
    text_generation_pipeline = pipeline("text-generation", model="gpt2")
    generated_text = text_generation_pipeline(text, max_length=max_length, num_return_sequences=1)

    # Extract the generated text
    generated_text = generated_text[0]['generated_text']

    return generated_text

app = Flask(__name__)

@app.route("/query", methods=["POST"])
def handle_query():
    request_data = request.get_json()
    if not request_data or "query" not in request_data:
        return jsonify({"error": "Missing query in request data"}), 400

    query = request_data["query"]
    mode = request_data.get('mode', 'website')

    if mode == 'website':
        websites = request_data.get('websites', [])
        results = []
        for website in websites:
            website_details = get_website_details(website)
            google_analytics_data = get_google_analytics_data(request_data.get('google_analytics_view_id'), GA_API_KEY)
            social_media_data = get_social_media_data(request_data.get('social_media_platform'), FACEBOOK_ACCESS_TOKEN)

            # Combine the data and generate a response
            prompt = """
Instruction: Generate customized digital marketing strategy for website in the industry. 
Analyze business website for best digital marketing strategy and layout for increased engagement, effectiveness and accessibility.
Based on the type of business and market trend, provide a detailed Digital marketing strategy for that unique business.

Persona: professional and knowledgeable in Digital marketing strategist, capable of adapting its communication to various industries and languages.
Format: The format should be structured, professionally written and very detailed, offering comprehensive strategies and insights for businesses, inclusive of social media strategy, homepage strategy and website strategy, using paragraph and markdown, use H2 as section header.
Tone: The tone must be informative, authoritative, and approachable, making complex data and strategies accessible to a wide range of users.

###
Website Details:
%s
###

Google Analytics Data:
%s

Social Media Data:
%s

Output:
""" % (website_details, google_analytics_data, social_media_data)

            results.append(prompt)

        # Create a new thread for each request to handle concurrency efficiently
        thread = threading.Thread(target=handle_query_thread, args=(results,))
        thread.start()

        # Generate a unique query ID and return it in the response
        query_id = len(responses) + 1
        return jsonify({"status": "Query accepted", "query_id": query_id}), 202

    elif mode == 'text_generation':
        text = request_data.get('text', '')
        generated_text = generate_text(text)
        return jsonify({"generated_text": generated_text}), 200

    else:
        return jsonify({"error": "Invalid mode"}), 400

@app.route("/response", methods=["GET"])
def get_response():
    if not request.args.get("query_id") or not request.args.get("query_id").isnumeric():
        return jsonify({"error": "Invalid or missing query ID"}), 400

    query_id = int(request.args.get("query_id"))

    if responses.get(query_id):
        response = responses.pop(query_id)
        return jsonify({"response": response}), 200
    else:
        return jsonify({"status": "Response not ready yet"}), 202

def handle_query_thread(results):
    for result in results:
        response = generate_response(result)
        query_id = len(responses) + 1
        responses[query_id] = response

if __name__ == "__main__":
    responses = {}  # Dictionary to store query IDs and corresponding responses
    app.run(debug=True, host="0.0.0.0")  # Bind to all interfaces for accessibility
