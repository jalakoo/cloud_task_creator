import os
from google.cloud import tasks_v2
import json
import functions_framework
from basicauth import decode, encode
import time
from google.api_core.exceptions import GoogleAPIError


@functions_framework.http
def create_task(request):
    # Optional Basic Auth
    basic_user = os.environ.get("BASIC_AUTH_USER", None)
    basic_password = os.environ.get("BASIC_AUTH_PASSWORD", None)
    if basic_user and basic_password:
        auth_header = request.headers.get("Authorization")
        if auth_header is None:
            return "Missing authorization credentials", 401
        try:
            request_username, request_password = decode(auth_header)
        except Exception as e:
            return f"Error decoding authorization header: {e}", 401
        if request_username != basic_user or request_password != basic_password:
            return "Unauthorized", 401

    # Get JSON payload
    payload = request.get_json()
    if not payload:
        return "Invalid JSON payload", 400

    # Environment variables
    project = os.environ.get("GCP_PROJECT_ID")
    queue = os.environ.get("QUEUE_ID")
    location = os.environ.get("LOCATION_ID")
    url = os.environ.get("TARGET_FUNCTION_URL")

    if not project or not queue or not location or not url:
        return "Environment variables are not set correctly", 500

    # Encode the Basic Auth credentials
    if basic_user and basic_password:
        encoded_credentials = encode(basic_user, basic_password)
        if encoded_credentials.startswith("Basic "):
            encoded_credentials = encoded_credentials[6:]  # Remove the "Basic " prefix
        auth_header_value = f"Basic {encoded_credentials}"
    else:
        auth_header_value = None

    # Cloud Tasks client
    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(project, location, queue)

    # Task configuration
    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": url,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(payload).encode(),
        }
    }

    # Add the Authorization header if credentials are provided
    if auth_header_value:
        task["http_request"]["headers"]["Authorization"] = auth_header_value

    # Attempt to create the task with retries
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = client.create_task(parent=parent, task=task)
            print(f"Created task {response.name}")
            return "Task created", 200
        except GoogleAPIError as e:
            print(f"Attempt {attempt + 1}: Error creating task: {e}")
            time.sleep(2**attempt)  # Exponential backoff
        except Exception as e:
            print(f"Attempt {attempt + 1}: Unexpected error: {e}")
            return f"Unexpected error: {e}", 500

    return "Error creating task after 3 attempts", 500
