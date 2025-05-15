from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import uuid
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
from dotenv import load_dotenv
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import browser_cookie3
import re

# Load environment variables from .env file
load_dotenv()

# Import LLM modules based on provider
try:
    import openai
except ImportError:
    print("OpenAI package not installed. Install with: pip install openai")

try:
    import anthropic
except ImportError:
    print("Anthropic package not installed. Install with: pip install anthropic")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Secret key for JWT
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')

# Mock database (replace with a real database in production)
users_db = {}
conversations_db = {}
llm_config = {
    "provider": "openai",
    "modelName": "gpt-4o",
    "temperature": 0.7
}

# Load products data globally when the module is initialized
products_list = []

def load_customer_data(data_folder="customer_data"):
    """
    Loads customer data from JSON files in a specified folder.  The filename
    is assumed to be the customer ID.

    Args:
        data_folder (str, optional): The path to the folder containing the
            customer data files. Defaults to "customer_data".

    Returns:
        dict: A dictionary where keys are customer IDs and values are
            the corresponding customer data (loaded from the JSON files).
            Returns an empty dictionary if the folder does not exist,
            if there are no json files or if any error occurs during file processing.
    """
    users = {}
    if not os.path.exists(data_folder):
        print(f"Error: Folder '{data_folder}' not found.")
        return users

    files = [f for f in os.listdir(data_folder) if f.endswith(".json")]

    if not files:
        print(f"Warning: No JSON files found in '{data_folder}'.")
        return users

    for filename in files:
        try:
            user_id = os.path.splitext(filename)[0]
            filepath = os.path.join(data_folder, filename)
            with open(filepath, "r") as f:
                customer_data = json.load(f)
            users[user_id] = customer_data
            # print(f"Loaded customer data for user {user_id}: {customer_data}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in file '{filepath}'. Skipping.")
        except FileNotFoundError:
            print(f"Error: File not found '{filepath}'. This should not happen, check directory.")
        except Exception as e:
            print(f"Error: An unexpected error occurred while processing '{filepath}': {e}")

    return users

def read_products(file_path="products.json"):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            products_data = json.load(f)
        return products_data
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON from {file_path}: {e}")
        return None

# Load products data when the module starts
products_list = read_products()
if products_list:
    print("Successfully loaded product data.")
else:
    print("Failed to load product data.")

# Load customer data when the module starts
users_db = load_customer_data()
print(f"Loaded {len(users_db)} customer profiles.")


# product_recommender.py

def categorize_risk_level(risk):
    if isinstance(risk, str):
        risk_lower = risk.lower()
        if risk_lower == "high":
            return "aggressive"
        elif risk_lower == "medium":
            return "moderate"
        else:
            return "low_risk"
    return "low_risk" # Default if risk level is not a string or recognized

def recommend_products(customer, products, min_score_threshold=50):
    """
    Recommends products to a customer based on their profile and a list of products.

    Args:
        customer (dict): The customer's profile data.
        products (list): A list of product dictionaries.
        min_score_threshold (int, optional): The minimum score for a product to be
            considered a recommendation. Defaults to 50.

    Returns:
        dict: A dictionary containing product recommendations, categorized by risk level.
              Returns an empty dict if products list is empty.
    """
    recommendations = {
        "aggressive": [],
        "moderate": [],
        "low_risk": []
    }

    if not products:
        return recommendations

    for product in products:
        score = 0
        reasons = []

        category = categorize_risk_level(product.get("riskLevel", "low"))

        # Ensure product_offerings and existing_products exist and are iterable
        if (
            customer.get("product_offerings") and
            isinstance(customer["product_offerings"].get("existing_products"), list) and
            product.get("productName") in customer["product_offerings"]["existing_products"]
        ):
            continue

        # Ensure all necessary keys exist and handle potential None values
        if (
            customer.get("product_eligibility", {}).get("age_eligibility_met") and
            customer.get("personal_details", {}).get("kyc_status", {}).get("uk_resident") and
            customer.get("financial_profile", {}).get("employment_type") in product.get("applicabilityRules", {}).get("applicableCustomerTypes", [])
        ):
            score += 15

        if customer.get("risk_profile", {}).get("risk_tolerance") in product.get("requiredRiskTolerance", []):
            score += 20
        else:
            reasons.append("Risk tolerance does not match")

        if (
            customer.get("personal_details", {}).get("kyc_status", {}).get("identity_verified") and
            customer.get("regulatory_compliance", {}).get("fca_suitability_assessment") and
            customer.get("regulatory_compliance", {}).get("mifid_ii_compliance")
        ):
            score += 15

        if (
            product.get("applicabilityRules", {}).get("openBankingRequired") and
            "open_banking_data" in customer.get("financial_profile", {})
        ):
            score += 10

        if customer.get("financial_profile", {}).get("disposable_income_after_debts", 0) >= 500:
            score += 10
        else:
            reasons.append("Low disposable income")

        if customer.get("financial_goals", {}).get("timeline", "").lower() == "long-term":
            score += 10

        score += 20  # Not a duplicate product

        if score >= min_score_threshold: # Use the min_score_threshold directly
            recommendations[category].append({
                "productId": product.get("productId"),
                "productName": product.get("productName"),
                "score": score,
                "confidence": f"{score}%",
                "reasoning": reasons if reasons else ["Meets all major criteria"]
            })

    return recommendations




# Authentication middleware
def token_required(f):
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Authentication token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user_id = data['user_id']
            current_user = users_db.get(current_user_id)
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            # Pass the actual user object to the decorated function
            return f(current_user, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

    decorated.__name__ = f.__name__
    return decorated

def build_system_prompt(user_profile=None):
    """Builds the system prompt based on the user profile."""
    system_prompt = f"""
    As RetireIQ, a retirement agent chatbot with access to the customer's structured personal and financial data in JSON format, begin a short, personalized conversation to guide the customer toward the sub-intent "Choose retirement investments." First, extract the customer's first name from the field personal_details.first_name and use it naturally to address them throughout the interaction. Acknowledge their current financial stage without repeating known details. Ask if they’re currently more focused on growing long-term retirement savings or keeping flexibility for short-term needs. Based on their response, follow up to understand whether they prefer a hands-on investment style or an automated, guided approach. If needed, ask if they have specific preferences or exclusions (e.g., ESG, sectors to avoid). Keep the conversation friendly and concise, ask only relevant questions (up to five), and stop once enough information is gathered to recommend suitable retirement investment options tailored to their goals and preferences.

    Once intent and sub-intent are known, output your understanding in the following structured JSON format only and don't add any other text anywhere in response:
    {{
        "intent": "<detected primary intent>",
        "sub_intent": "<detected sub-intent details>",
        "summary": "<short natural-language summary of what the customer wants>"
    }}

    User Profile Data: {user_profile}
    """
    print(f"system_prompt: {system_prompt}")
    return system_prompt

def prepare_openai_messages(system_prompt, conversation_history, message):
    """Prepares the list of messages for the OpenAI API."""
    messages = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        for msg in conversation_history:
            if msg["type"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["type"] == "bot":
                messages.append({"role": "assistant", "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    return messages


def prepare_azure_openai_messages(system_prompt, conversation_history, message):
    """Prepares the list of messages for the Azure OpenAI API."""
    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        for msg in conversation_history:
            if msg["type"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["type"] == "bot":
                messages.append({"role": "assistant", "content": msg["content"]})

    messages.append({"role": "user", "content": message})
    return messages

def call_openai_api(messages, model, temperature):
    """Calls the OpenAI API and returns the response content."""
    try:
        # Ensure 'proxies' argument is NOT present here
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        # print(f"OpenAI client: {client}")
        if not client.api_key:
            print("OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
            return "I'm sorry, the OpenAI API key is not configured correctly."
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=500
        )
        return response.choices[0].message.content
    except openai.APIError as e:
        print(f"OpenAI API Error: {e}")
        return f"I'm sorry, there was an issue with the OpenAI API: {e}"
    except openai.AuthenticationError as e:
        print(f"OpenAI Authentication Error: {e}")
        return f"I'm sorry, there was an authentication error with the OpenAI API: {e}"
    except openai.RateLimitError as e:
        print(f"OpenAI Rate Limit Error: {e}")
        return "I'm sorry, I'm currently experiencing high demand. Please try again later."
    except Exception as e:
        print(f"Error with OpenAI API: {e}")
        return f"I'm sorry, I encountered an error processing your request: {e}"


def call_azure_openai_api_with_key(messages, model, temperature=0.7, max_tokens=500):
    """Calls the Azure OpenAI API and returns the response content."""
    try:
        # Load required environment variables for Azure OpenAI
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_base = os.getenv("AZURE_OPENAI_ENDPOINT")  # e.g., https://your-resource.openai.azure.com/
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-12-01-preview")  # default API version

        if not api_key or not api_base:
            print("Azure OpenAI API key or endpoint not found. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT environment variables.")
            return "I'm sorry, the Azure OpenAI API key or endpoint is not configured correctly."

        # Configure the OpenAI SDK for Azure
        openai.api_type = "azure"
        openai.api_key = api_key
        openai.api_base = api_base
        openai.api_version = api_version

        print("openai.api_type", openai.api_type)
        print("openai.api_key", openai.api_key)
        print("openai.api_base", openai.api_base)
        print("openai.api_version", openai.api_version)

        # Call the Azure OpenAI chat completion API
        response = openai.ChatCompletion.create(
            engine=model,  # Use your Azure deployment name (e.g., gpt-4)
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Return the content from the response
        return response['choices'][0]['message']['content']

    except openai.error.OpenAIError as e:
        print(f"Azure OpenAI API Error: {e}")
        return f"I'm sorry, there was an issue with the Azure OpenAI API: {e}"

    except openai.error.AuthenticationError as e:
        print(f"Azure OpenAI Authentication Error: {e}")
        return f"I'm sorry, there was an authentication error with the Azure OpenAI API: {e}"

    except openai.error.RateLimitError as e:
        print(f"Azure OpenAI Rate Limit Error: {e}")
        return "I'm sorry, I'm currently experiencing high demand. Please try again later."

    except Exception as e:
        print(f"Error with Azure OpenAI API: {e}")
        return f"I'm sorry, I encountered an error processing your request: {e}"

def prepare_anthropic_prompt(system_prompt, conversation_history, message):
    """Prepares the prompt for the Anthropic API."""
    conversation = ""
    if conversation_history:
        for msg in conversation_history:
            if msg["type"] == "user":
                conversation += f"\n\nHuman: {msg['content']}"
            elif msg["type"] == "bot":
                conversation += f"\n\nAssistant: {msg['content']}"
    prompt = f"{system_prompt}\n\n{conversation}\n\nHuman: {message}\n\nAssistant:"
    return prompt

def call_anthropic_api(prompt, model, temperature):
    """Calls the Anthropic API and returns the completion."""
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        if not client.api_key:
            print("Anthropic API key not found. Set the ANTHROPIC_API_KEY environment variable.")
            return "I'm sorry, the Anthropic API key is not configured correctly."
        response = client.completions.create(
            prompt=prompt,
            model=model,
            max_tokens_to_sample=500,
            temperature=temperature
        )
        return response.completion
    except anthropic.APIError as e:
        print(f"Anthropic API Error: {e}")
        return f"I'm sorry, there was an issue with the Anthropic API: {e}"
    except anthropic.AuthenticationError as e:
        print(f"Anthropic Authentication Error: {e}")
        return f"I'm sorry, there was an authentication error with the Anthropic API: {e}"
    except anthropic.RateLimitError as e:
        print(f"Anthropic Rate Limit Error: {e}")
        return "I'm sorry, I'm currently experiencing high demand. Please try again later."
    except Exception as e:
        print(f"Error with Anthropic API: {e}")
        return f"I'm sorry, I encountered an error processing your request: {e}"

def generate_ai_response(message, user_profile=None, conversation_history=None, llm_config=None):
    """Generates an AI response based on the configured provider."""
    llm_config = {
        "provider": os.getenv("LLM_PROVIDER", "azure_openai"),
        "modelName": os.getenv("LLM_MODEL_NAME", "gpt-4o"),
        "temperature": float(os.getenv("LLM_TEMPERATURE", 0.7))
    }
    provider = llm_config.get("provider")
    model = llm_config.get("modelName")
    temperature = llm_config.get("temperature")

    system_prompt = build_system_prompt(user_profile)

    if provider == "openai":
        messages = prepare_openai_messages(system_prompt, conversation_history, message)
        return call_openai_api(messages, model, temperature)
    elif provider == "azure_openai":
        prompt = prepare_azure_openai_messages(system_prompt, conversation_history, message)
        ai_response = call_azure_openai_api_with_key(prompt, model, temperature)
        print(f"AI Response: {ai_response}")
        extrectedAIResponse = extract_json(ai_response)
        print('------extrectedAIResponse------')
        print(f"{extrectedAIResponse}")
        if validate_intent_response(extrectedAIResponse):
            print(f"Intent and sub-intent identfied, calling agent: {extrectedAIResponse}")
            final_res = call_agent_api(extrectedAIResponse, user_profile['id'])
            print(f"-----------Final output---------: {final_res}")
            return final_res
        else:
            print('-----else part-----')
            return ai_response
    else:
        return "I'm sorry, the configured AI provider is not available. Please check your settings."


def validate_intent_response(api_response):
    if isinstance(api_response, dict):
        # Already a dictionary, so it's valid JSON
        return True
    elif isinstance(api_response, str):
        try:
            # Try correcting single quotes to double quotes (best effort)
            corrected_str = api_response.replace("'", '"')
            json_obj = json.loads(corrected_str)
            return True
        except json.JSONDecodeError as e:
            return False
    else:
        return False

def extract_json(input_text):
    print(f"--------input_text input print")
    print(f"{input_text}")
    # Regex to find JSON object (starting with { and ending with })
    match = re.search(r'\{.*\}', input_text, re.DOTALL)
    if match:
        try:
            # Load JSON to ensure it's valid
            extracted_json = json.loads(match.group())
            print(f"--------No JSON object found in the input text.")
            print(f"{extracted_json}")
            return extracted_json
        except json.JSONDecodeError:
            print("---------Found JSON-like text, but it's not valid JSON.")
            return input_text
    else:
        print("----------No JSON object found in the input text.")
        return input_text


# def call_agent_api(intent="", user_id=""):

def generateAgentAPIToken():
    # Replace 'example.com' with your target domain
    target_domain = "https://dev.lionis.ai/error/500?status=success"
    # Try to load cookies from Chrome
    cookies = browser_cookie3.load(domain_name=target_domain)  
    # Print cookie names and values
    for cookie in cookies:
        print(f"{cookie.name} = {cookie.value}")

def call_agent_api(intent="", user_id=""):
    # user = users_db.get(current_user['id'])

    # Endpoint URL
    agentUrl = 'https://dev.lionis.ai/api/v1/agents/68259fbd69d8809665943d87/query'
    # Headers
    headers = {
        'x-client-id': '7b4e7797-1bdf-40a0-908f-4827041f4b99',
        'x-project-id': 'e317e372-b9a8-43c1-bfbb-0bf9e472a49d',
        'x-workspace-id': '8e4e13b7-41bf-4f51-a797-652c6f32d176',
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Il9GcnhmUVZTbFBVbHZHWjVIdmRrTlN1Z1FzeXJkbjB1cWxXSkdJTVlfWXcifQ.eyJ0eXBlIjoiYXQiLCJjbGllbnRJZCI6IjEyNmJjNDU0LTJjZDYtNDlmZS05Y2RmLTJjZjdlZjNhOWNlNyIsImlkcCI6Im1zZnQiLCJpc3MiOiJodHRwczovL2Rldi5saW9uaXMuYWkiLCJyb2xlcyI6WyJzdXBlcl91c2VyIl0sImp0aSI6IkVlYU5DUnZiN0oiLCJVc2VySW5mbyI6eyJpZCI6IjEyZDQ1ZmFlLWY3ZGEtNGE0OC1iMWZkLTlhN2Q5YzMyOTgzZCIsImVtYWlsIjoidmlqa2FsZUBwdWJsaWNpc2dyb3VwZS5uZXQiLCJkaXNwbGF5TmFtZSI6IlZpamF5IEthbGUifSwiYXBwS2V5Ijoic2tfZGFlZDk5YzgwODE5OSIsImFwcElkIjoiYjBmMmQ4MmEtZWVjMy00MTBiLWE5ZTQtYWI5NzgzNzcyMWI4Iiwic2VydmljZXMiOlsibGxtIiwicHJvamVjdHMiLCJhc3NldC1hbmFseXplciIsImFzc2V0IiwiYXVkaWVuY2UiLCJzdGF0ZSIsImJvZGhpIiwiZGF0YSIsImludmVudG9yeSIsIm5vdGlmaWNhdGlvbiJdLCJhcHBOYW1lIjoiYXBwLWZyYW1ld29yayIsImluZHVzdHJ5IjoiMDg3YzBmMzMtZGEwMC00MTZlLTk3MDEtY2UyN2YzYWRiY2Q5IiwiaWF0IjoxNzQ3MzE4NTcxLCJleHAiOjE3NDczMjU3NzF9.vGHsI_Uh8NkU7TqzLeHk772fiCkNzB0vKASzAKs8wo9iVv_qFJkvk_IH5VhVyPV3oIoaKkoRrc5-9tqWnDVGIRMFqN3hpxgalwU6e2byW5zuZHmU5lVSR41K5K6t5bk0J6gb7HU2Ouc6lbWwlO1B9_35cVR5853Ny6JiDPXaXi1lKq-hn8-XPD1BWsuN0syVDTXUBrdFOD3KHs3CRdzltWpUnPLCrMHJXFF6JYJJDKKTTM7zNEGNBhVo_LUqOgqnFZen3GWlq9HNRFXkbmkR-k-Fjjv8ciGDSJB01whxwZaKKIw2oHnrEL70fNPAWIT5D49bCNlSZyxPK3KJmIdSrg'
    }
    # Payload
    user_intent = f"intent: {intent['intent']}, sub-intent: {intent['sub_intent']}"
    data = {
        "input_params": {
            "user_intent": user_intent,
            "user_id": user_id
        }
    }
    print("Agent APi payload")
    print(json.dumps(data, indent=4))
    
    # Make the POST request
    response = requests.post(agentUrl, headers=headers, json=data)

    # Output the response
    print(f"Status Code------------: {response.status_code}")
    print("---------Response Body:----------")
    print(response.json())
    if response.status_code == 200:
        res = response.json()
        event_res = call_agent_api_get_final_response(res['correlation_id'])
        print("---------event_res:----------")
        print(event_res)
        return event_res
    else:
        return 'Something went wrong, Please try again.'

def call_agent_api_get_final_response(correlation_id):
    # user = users_db.get(current_user['id'])

    # Endpoint URL
    agentUrl = f'https://dev.lionis.ai/api/v1/events/events?correlationId={correlation_id}'
    # Headers
    headers = {
        'x-client-id': '7b4e7797-1bdf-40a0-908f-4827041f4b99',
        'x-project-id': 'e317e372-b9a8-43c1-bfbb-0bf9e472a49d',
        'x-workspace-id': '8e4e13b7-41bf-4f51-a797-652c6f32d176',
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Il9GcnhmUVZTbFBVbHZHWjVIdmRrTlN1Z1FzeXJkbjB1cWxXSkdJTVlfWXcifQ.eyJ0eXBlIjoiYXQiLCJjbGllbnRJZCI6IjEyNmJjNDU0LTJjZDYtNDlmZS05Y2RmLTJjZjdlZjNhOWNlNyIsImlkcCI6Im1zZnQiLCJpc3MiOiJodHRwczovL2Rldi5saW9uaXMuYWkiLCJyb2xlcyI6WyJzdXBlcl91c2VyIl0sImp0aSI6IktuMjZ5Sm9Vbk4iLCJVc2VySW5mbyI6eyJpZCI6IjEyZDQ1ZmFlLWY3ZGEtNGE0OC1iMWZkLTlhN2Q5YzMyOTgzZCIsImVtYWlsIjoidmlqa2FsZUBwdWJsaWNpc2dyb3VwZS5uZXQiLCJkaXNwbGF5TmFtZSI6IlZpamF5IEthbGUifSwiYXBwS2V5Ijoic2tfZGFlZDk5YzgwODE5OSIsImFwcElkIjoiYjBmMmQ4MmEtZWVjMy00MTBiLWE5ZTQtYWI5NzgzNzcyMWI4Iiwic2VydmljZXMiOlsibGxtIiwicHJvamVjdHMiLCJhc3NldC1hbmFseXplciIsImFzc2V0IiwiYXVkaWVuY2UiLCJzdGF0ZSIsImJvZGhpIiwiZGF0YSIsImludmVudG9yeSIsIm5vdGlmaWNhdGlvbiJdLCJhcHBOYW1lIjoiYXBwLWZyYW1ld29yayIsImluZHVzdHJ5IjoiMDg3YzBmMzMtZGEwMC00MTZlLTk3MDEtY2UyN2YzYWRiY2Q5IiwiaWF0IjoxNzQ3MzEwOTQ1LCJleHAiOjE3NDczMTgxNDV9.LFFWUlysMnSBfOX1g905_B7Jbjj7KsvEe8pW_7XB87Gbmx_U-LAIpntLuBnqxBeasVAm9TyMdxui-ccw1igkSxJ6RizZXs-oqVoWLkaGwj7KYzVeCAVJAA5brV5cFtLbaHSKzkoma7H5uVw6Fd_phNm4Afu1Wmnya_E8HqQiO1UcG1Po76K-geotD-wXsbjdD6iDTLZiG0hyUQlWek1m-IAxknf_kSlN80gflcPwJXoeXI8CHAPqvCE8LG_vcFTTnR7qf3LsDw-LRhOv0qKvk0jI5gZq7fu2IRnCV6HDnaY7LIhW3ldQEdiJ_yDif7kg2yw6NQtOM3A6b_tjP0d7gw'
    }

    # Make the GET request
    response = requests.get(agentUrl, headers=headers)
    if response.status_code == 200:
        # Output the response
        print(f"Event Status Code------------: {response.status_code}")
        print("Event Response Body:----------")
        res = response.json()
        print(res)
        print("agentStatus:----------")
        print(res[0]['agentStatus'])

        if res[0]['agentStatus'] == 'completed':
            print("output:----------")
            print(res[0]['output']['response_text'])
            return res[0]['output']['response_text']
        else:
            time.sleep(5)
            return call_agent_api_get_final_response(correlation_id)
    else:
        return 'Something went wrong, Please try again.'

# Generate suggested follow-up questions based on conversation
def generate_suggested_questions(message, response):
    # In a real implementation, you would use an LLM to generate relevant follow-up questions
    # For this example, we'll return predetermined questions
    return [
        {"id": str(uuid.uuid4()), "text": "How much do I need to save monthly?", "category": "planning"},
        {"id": str(uuid.uuid4()), "text": "What investment strategy is best for me?", "category": "investment"},
        {"id": str(uuid.uuid4()), "text": "How does inflation affect my retirement?", "category": "planning"},
        {"id": str(uuid.uuid4()), "text": "What are tax advantages of retirement accounts?", "category": "investment"}
    ]

# Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400

    email = data['email']

    for user in users_db.values():
        if user.get('personal_details', {}).get('contact_details', {}).get('email') == email:
            return jsonify({'message': 'User with this email already exists'}), 409

    user_id = str(uuid.uuid4())

    new_user = {
        'id': user_id,
        'personal_details': {
            'contact_details': {'email': email},
            'first_name': data.get('firstName', ''),
            'last_name': data.get('lastName', '')
        },
        'password': generate_password_hash(data['password']),
        'financial_profile': {},
        'risk_profile': {},
        'financial_goals': {},
        'product_eligibility': {},
        'regulatory_compliance': {},
        'cognitive_digital_accessibility': {},
        'product_offerings': {},
        'tax_efficiency': {}
    }

    users_db[user_id] = new_user

    # Generate JWT token
    token = jwt.encode({
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'user_id': user_id,
        'email': email,
        'firstName': data.get('firstName', ''),
        'lastName': data.get('lastName', ''),
        'token': token
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400

    # Find user by email
    user = None
    for u in users_db.values():
        if u.get("personal_details", {}).get("contact_details", {}).get("email") == data['email']:
            user = u
            break

    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401

    # Generate JWT token
    token = jwt.encode({
        'user_id': user['id'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        'user_id': user['id'],
        'email': user.get("personal_details", {}).get("contact_details", {}).get("email", ""),
        'firstName': user.get("personal_details", {}).get('first_name', ''),
        'lastName': user.get("personal_details", {}).get('last_name', ''),
        'token': token
    })

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    user = users_db.get(current_user['id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    # generateAgentAPIToken()
    # extract_json('test')
    profile = {
        "personal_details": user.get("personal_details", {}),
        "financial_profile": user.get("financial_profile", {}),
        "risk_profile": user.get("risk_profile", {}),
        "financial_goals": user.get("financial_goals", {}),
        "product_eligibility": user.get("product_eligibility", {}),
        "regulatory_compliance": user.get("regulatory_compliance", {}),
        "cognitive_digital_accessibility": user.get("cognitive_digital_accessibility", {}),
        "product_offerings": user.get("product_offerings", {}),
        "tax_efficiency": user.get("tax_efficiency", {}),
    }

    return jsonify({
        'user_id': current_user['id'],
        'email': user.get("personal_details", {}).get("contact_details", {}).get("email", ""),
        'firstName': user.get("personal_details", {}).get('first_name', ''),
        'lastName': user.get("personal_details", {}).get('last_name', ''),
        **profile
    })

@app.route('/api/unauth/profile', methods=['GET'])
def get_profile_unauth():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Missing user_id parameter'}), 400

    user = users_db.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    return jsonify(user)



@app.route('/api/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    user = users_db.get(current_user['id'])

    if not data:
        return jsonify({'message': 'No data provided'}), 400

    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Update the allowed profile fields safely
    if "personal_details" in data:
        user["personal_details"] = {**user.get("personal_details", {}), **data["personal_details"]}
    if "financial_profile" in data:
        user["financial_profile"] = {**user.get("financial_profile", {}), **data["financial_profile"]}
    if "risk_profile" in data:
        user["risk_profile"] = {**user.get("risk_profile", {}), **data["risk_profile"]}
    if "financial_goals" in data:
        user["financial_goals"] = {**user.get("financial_goals", {}), **data["financial_goals"]}
    if "product_eligibility" in data:
        user["product_eligibility"] = {**user.get("product_eligibility", {}), **data["product_eligibility"]}
    if "regulatory_compliance" in data:
        user["regulatory_compliance"] = {**user.get("regulatory_compliance", {}), **data["regulatory_compliance"]}
    if "cognitive_digital_accessibility" in data:
        user["cognitive_digital_accessibility"] = {**user.get("cognitive_digital_accessibility", {}), **data["cognitive_digital_accessibility"]}
    if "product_offerings" in data:
        user["product_offerings"] = {**user.get("product_offerings", {}), **data["product_offerings"]}
    if "tax_efficiency" in data:
        user["tax_efficiency"] = {**user.get("tax_efficiency", {}), **data["tax_efficiency"]}

    users_db[current_user['id']] = user # Ensure the database is updated

    return jsonify({
        'user_id': current_user['id'],
        'email': user.get("personal_details", {}).get("contact_details", {}).get("email", ""),
        'firstName': user.get("personal_details", {}).get('first_name', ''),
        'lastName': user.get("personal_details", {}).get('last_name', ''),
        'message': "Profile updated successfully"
    })


@app.route('/api/recommend', methods=['GET'])
@token_required
def recommend(current_user):
    user = users_db.get(current_user['id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404

    result = recommend_products(user, products_list)
    return jsonify(result)


@app.route('/api/unauth/recommend', methods=['GET'])
def get_recommendation_unauth():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'message': 'Missing user_id parameter'}), 400

    user = users_db.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    result = recommend_products(user, products_list)
    return jsonify(result)

@app.route('/api/chat/message', methods=['POST'])
@token_required
def send_message(current_user):
    data = request.get_json()

    if not data or not data.get('message'):
        return jsonify({'message': 'No message provided'}), 400

    user_id = current_user['id']
    message_text = data['message']
    conversation_id = data.get('conversation_id')

    # Get or create conversation
    if not conversation_id or conversation_id not in conversations_db:
        conversation_id = str(uuid.uuid4())
        conversations_db[conversation_id] = {
            'user_id': user_id,
            'messages': []
        }

    # Get user profile for personalized responses
    user = users_db.get(user_id)

    # Save user message
    user_message = {
        'id': str(uuid.uuid4()),
        'content': message_text,
        'type': 'user',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    conversations_db[conversation_id]['messages'].append(user_message)

    # Generate AI response
    ai_response = generate_ai_response(
        message_text,
        user,
        conversations_db[conversation_id]['messages']
    )

    # Save bot response
    bot_message = {
        'id': str(uuid.uuid4()),
        'content': ai_response,
        'type': 'bot',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    conversations_db[conversation_id]['messages'].append(bot_message)

    # Generate suggested follow-up questions
    suggested_questions = generate_suggested_questions(message_text, ai_response)

    return jsonify({
        'conversation_id': conversation_id,
        'message_id': bot_message['id'],
        'response': ai_response,
        'suggested_questions': suggested_questions
    })

@app.route('/api/chat/history', methods=['GET'])
@token_required
def get_chat_history(current_user):
    conversation_id = request.args.get('conversation_id')

    if not conversation_id or conversation_id not in conversations_db:
        return jsonify({'message': 'Conversation not found'}), 404

    conversation = conversations_db[conversation_id]

    # Check if the conversation belongs to the current user
    if conversation['user_id'] != current_user['id']:
        return jsonify({'message': 'Not authorized to view this conversation'}), 403

    return jsonify({
        'conversation_id': conversation_id,
        'messages': conversation['messages']
    })

@app.route('/api/config/llm', methods=['GET'])
@token_required
def get_llm_config(current_user):
    # In a real implementation, you would fetch user-specific config from database
    return jsonify(llm_config)

@app.route('/api/config/llm', methods=['PUT'])
@token_required
def update_llm_config(current_user):
    global llm_config
    data = request.get_json()

    if not data:
        return jsonify({'message': 'No data provided'}), 400

    # Update config fields
    for key in ['provider', 'modelName', 'temperature']:
        if key in data:
            llm_config[key] = data[key]

    return jsonify(llm_config)

if __name__ == '__main__':
    # Instructions for using the API
    print("=" * 80)
    print("RetireIQ Python Backend API")
    print("=" * 80)
    # print("API is running at http://localhost:5000/api")
    # print("To use with OpenAI, set the OPENAI_API_KEY environment variable")
    # print("To use with Anthropic, set the ANTHROPIC_API_KEY environment variable")
    # print("For production, change the JWT_SECRET_KEY environment variable")
    port = int(os.environ.get('PORT', 5000))
    print("=" * 80)

    # Run the Flask app
    app.run(debug=False, host='0.0.0.0', port=port)