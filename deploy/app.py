import threading
from flask import Flask, request, jsonify, Response
from ctransformers import AutoModelForCausalLM
import requests
from bs4 import BeautifulSoup

# Set gpu_layers to the number of layers to offload to GPU. Set to 0 if no GPU acceleration is available on your system.
model = AutoModelForCausalLM.from_pretrained("TheBloke/Mistral-7B-v0.1-GGUF", model_file="mistral-7b-v0.1.Q5_K_M.gguf", model_type="mistral", gpu_layers=0, max_new_tokens=512, context_length=1024)

# Global lock for thread safety
thread_lock = threading.Lock()

def get_website_details(url):
    # Make an HTTP request to get the HTML content of the website
    response = requests.get(url)

    if response.status_code == 200:
        # Parse HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = f"URL: {url}\n"
        try:
            # Extract relevant details
            title = soup.title.string.strip() if soup.title else "No title found"
            result += f'Title: {title}\n'
        except:
            pass

        try:
            # Get meta description
            meta_description = soup.find("meta", {"name": "description"})
            description = meta_description["content"] if meta_description else "No description found"
            result += f'Description: {description}\n'
        except:
            pass
        
        try:
            # Extract categories or topics (based on HTML tags or classes)
            categories = [tag.text.strip() for tag in soup.find_all("a", class_="category-class")]
            result += f'Categories: {categories}\n'
        except:
            pass
        return result
    else:
        print(f"Error: Unable to fetch the website. Status code: {response.status_code}")

def generate_response(query):
    global thread_lock
    with thread_lock:  # Ensure exclusive model access for each request
        response = model(query)

    return response

app = Flask(__name__)

@app.route("/query", methods=["POST"])
def handle_query():
    request_data = request.get_json()
    if not request_data or "query" not in request_data:
        return jsonify({"error": "Missing query in request data"}), 400

    query = request_data["query"]
    mode = request_data['mode']

    # parse the query for the use case
    if mode == 'website':
        query = get_website_details(query)

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

Output: 
""" % query

    # Create a new thread for each request to handle concurrency efficiently
    thread = threading.Thread(target=handle_query_thread, args=(prompt,))
    thread.start()

    # Generate a unique query ID and return it in the response
    query_id = len(responses) + 1
    return jsonify({"status": "Query accepted", "query_id": query_id}), 202

@app.route("/response", methods=["GET"])
def get_response():
    # No query ID provided or invalid format
    if not request.args.get("query_id") or not request.args.get("query_id").isnumeric():
        return jsonify({"error": "Invalid or missing query ID"}), 400

    query_id = int(request.args.get("query_id"))

    # Check if response is ready, avoiding unnecessary blocking
    if responses.get(query_id):
        response = responses.pop(query_id)
        return jsonify({"response": response}), 200
    else:
        return jsonify({"status": "Response not ready yet"}), 202

def handle_query_thread(query):
    response = generate_response(query)
    query_id = len(responses) + 1
    responses[query_id] = response

if __name__ == "__main__":
    responses = {}  # Dictionary to store query IDs and corresponding responses
    app.run(debug=True, host="0.0.0.0")  # Bind to all interfaces for accessibility