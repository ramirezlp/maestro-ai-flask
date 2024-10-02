import sys
import os
import requests
import json
import uuid
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import maestro_gpt4o

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
executor = ThreadPoolExecutor()

tasks = {}

@app.route('/maestro', methods=['POST'])
def index():
    objective = request.form.get('objective')
    webhook_url = request.form.get('webhook_url')
    if objective and webhook_url:
        transaction_id = str(uuid.uuid4())
        executor.submit(process_maestro, transaction_id, objective, webhook_url)
        tasks[transaction_id] = {"status": "processing"}
        return jsonify({"transaction_id": transaction_id}), 202 
    return jsonify({"error": "Missing objective or webhook_url"}), 400

def process_maestro(transaction_id, objective, webhook_url):
    try:
        results = maestro_gpt4o.refined_output(objective)
        payload = {
            "result": results
        }
        response = requests.post(webhook_url, params={
            "transaction_id": transaction_id
        })
        response.raise_for_status()
        tasks[transaction_id] = {"status": "completed", "webhook_response": response.status_code, "data": results}
    except Exception as e:
        print(f"Error processing the objective: {e}")
        tasks[transaction_id] = {"status": "failed", "error": str(e)}

@app.route('/maestro/status/<transaction_id>', methods=['GET'])
def task_status(transaction_id):
    task_info = tasks.get(transaction_id)
    if task_info:
        return jsonify(task_info)
    return jsonify({"error": "Transaction ID not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)