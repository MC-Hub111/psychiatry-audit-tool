from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Example API keys (Replace with actual keys if required)
DRUGBANK_API_KEY = "YOUR_DRUGBANK_API_KEY"
OPENFDA_BASE_URL = "https://api.fda.gov/drug/label.json"
DRUGBANK_INTERACTIONS_API = "https://api.drugbank.com/v1/interactions"  # Placeholder URL

# Function to fetch medication information from OpenFDA
def get_medication_info(med_name):
    try:
        generic_response = requests.get(f"{OPENFDA_BASE_URL}?search=openfda.generic_name:{med_name}&limit=1")
        generic_response.raise_for_status()
        data = generic_response.json()

        if "results" not in data or not data["results"]:
            # Fallback to trade name search if generic name fails
            brand_response = requests.get(f"{OPENFDA_BASE_URL}?search=openfda.brand_name:{med_name}&limit=1")
            brand_response.raise_for_status()
            data = brand_response.json()
            if "results" not in data or not data["results"]:
                return {"error": "Medication not found in OpenFDA database"}

        return data["results"][0]
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to OpenFDA API"}
    except requests.exceptions.Timeout:
        return {"error": "Request to OpenFDA API timed out"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"API request failed: {req_err}"}
    except ValueError:
        return {"error": "Invalid response received from API"}

# Function to check potential interactions using DrugBank API
def check_interactions(med_list):
    if not isinstance(med_list, list) or not all(isinstance(med, str) for med in med_list):
        return {"error": "Invalid input format. Expected a list of medication names."}

    try:
        # Batch request optimization - sending all medications at once
        response = requests.post(
            DRUGBANK_INTERACTIONS_API, 
            json={"medications": med_list}, 
            headers={"Authorization": f"Bearer {DRUGBANK_API_KEY}"}
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}"}
    except requests.exceptions.ConnectionError:
        return {"error": "Failed to connect to DrugBank API"}
    except requests.exceptions.Timeout:
        return {"error": "Request to DrugBank API timed out"}
    except requests.exceptions.RequestException as req_err:
        return {"error": f"Interaction API request failed: {req_err}"}
    except ValueError:
        return {"error": "Invalid response received from DrugBank API"}

@app.route("/check_medications", methods=["POST"])
def check_medications():
    data = request.get_json()

    if not isinstance(data, dict) or "medication" not in data:
        return jsonify({"error": "No medication provided or incorrect JSON format"}), 400

    med_name = data["medication"].strip()
    if not med_name:
        return jsonify({"error": "Medication name cannot be empty"}), 400

    info = get_medication_info(med_name)
    return jsonify({"medication": med_name, "info": info})

@app.route("/check_interactions", methods=["POST"])
def check_medication_interactions():
    data = request.get_json()

    if not isinstance(data, dict) or "medications" not in data:
        return jsonify({"error": "No medications provided or incorrect JSON format"}), 400

    med_list = [med.strip() for med in data["medications"] if isinstance(med, str) and med.strip()]
    if not med_list:
        return jsonify({"error": "Medication list cannot be empty or contain invalid values"}), 400

    interactions = check_interactions(med_list)
    return jsonify({"interactions": interactions})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
