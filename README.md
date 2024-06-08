# Google Cloud Function

For creating a task from an HTTP call, to another Google Function that actually does processing.

## Requirements

- The associated Google Service account has permission to enqueue tasks to target Google Task Queue.

## Local Running

GCP_PROJECT= \
QUEUE_ID= \
LOCATION_ID=us-east1 \
TARGET_FUNCTION_URL= \
BASIC_AUTH_USER= \
BASIC_AUTH_PASSWORD= \
poetry run functions-framework --target=create_task
