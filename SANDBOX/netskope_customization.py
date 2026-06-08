import json
import os
import boto3
import requests
from botocore.exceptions import ClientError


def get_secret_from_aws(secret_name, region_name="us-east-1"):
    """Fetches the Netskope API token securely from AWS Secrets Manager."""
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        print(f"❌ Error retrieving secret from AWS: {e}")
        raise e

    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
        try:
            secret_dict = json.loads(secret)
            return secret_dict.get("token", secret)
        except json.JSONDecodeError:
            return secret

    return None


def add_app_instances(tenant_url, token, instances_payload):
    """Adds new app instances to the Netskope tenant via API."""
    if not tenant_url.startswith("https://"):
        tenant_url = f"https://{tenant_url}"

    url = f"{tenant_url}/api/v1/app_instances"
    params = {"token": token, "op": "add"}
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            url, params=params, headers=headers, json=instances_payload
        )
        response.raise_for_status()

        print(f"✅ Status Code: {response.status_code}")
        print("Response Body:")
        print(json.dumps(response.json(), indent=4))
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f"❌ HTTP error occurred: {http_err}")
        if response.text:
            print(f"Response text: {response.text}")
    except Exception as err:
        print(f"❌ An error occurred: {err}")


# ==========================================
# Execution Engine
# ==========================================
if __name__ == "__main__":
    # 1. Configuration Constants
    TENANT_URL = "agero.goskope.com"
    AWS_SECRET_NAME = "my-netskope-secret"  # Replace with your AWS Secret Name
    AWS_REGION = "us-east-1"                 # Replace with your AWS Region
    JSON_FILE_PATH = os.path.join(os.path.dirname(__file__), "instances.json")

    print("🚀 Initializing Netskope App Instance provisioning...")

    # 2. Extract context dynamically from the AFT pipeline variables
    # If running locally for testing, falls back to your staging account data
    target_account_id = os.environ.get("VENDED_ACCOUNT_ID", "185708269372")
    
    # AFT passes the requested Account Name down as an environment variable or via SSM.
    # Fallback constructs a default name if it isn't explicitly exposed in your local pipeline context.
    target_account_name = os.environ.get("VENDED_ACCOUNT_NAME", f"testaft2")

    print(f"ℹ️ Target Account Context -> ID: {target_account_id} | Name: {target_account_name}")

    # 3. Load the template instances schema from the localized external JSON file
    try:
        with open(JSON_FILE_PATH, "r") as file:
            payload_data = json.load(file)
            print(f"✅ Successfully loaded structure from template: {JSON_FILE_PATH}")
    except FileNotFoundError:
        print(f"❌ Error: Could not find the template payload file at {JSON_FILE_PATH}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Structural syntax or formatting error in your JSON template: {e}")
        exit(1)

    # 4. In-Memory Replace Loop
    print("🔄 Injecting target account variables into JSON schema fields...")
    modified_count = 0
    for instance in payload_data.get("instances", []):
        if instance.get("instance_id") == "replacewithaccountid":
            instance["instance_id"] = target_account_id
            modified_count += 1
        if instance.get("instance_name") == "replacewithaccountname":
            instance["instance_name"] = target_account_name

    print(f"📋 Tailored {modified_count} app instances for migration.")

    # 5. Fetch the API token securely from AWS Secrets Manager
    print("🔐 Querying AWS Secrets Manager for Netskope credentials...")
    api_token = get_secret_from_aws(AWS_SECRET_NAME, AWS_REGION)

    # 6. Execute API call with payload compilation
    if api_token:
        print("🌐 Transmitting final mapped payload configuration to Netskope Tenant...")
        add_app_instances(TENANT_URL, api_token, payload_data)
    else:
        print("❌ Critical Error: Failed to safely extract authorization token. Terminating block.")
        exit(1)