import requests
import pandas as pd
import time
import logging
from google.cloud import storage, secretmanager

# Initialise Cloud Logging
from google.cloud import logging as cloud_logging

client = cloud_logging.Client()
client.setup_logging()

# Constants
PROJECT_ID = "FAKE_PROJECT_ID"  # Dummy Google Cloud project ID
SECRET_NAME = "ipgeolocation-api-key"  # Dummy Google Cloud secret name
REQUESTS_PER_MINUTE = 60  # Rate limit as per free account
API_URL = "https://api.ipgeolocation.io/ipgeo"
OUTPUT_BUCKET_NAME = "output-bucket"  # Output bucket placeholder


def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the payload for the given secret version if one exists.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    return payload


def get_geolocation(api_key, ip):
    """Fetch geolocation data for a given IP address."""
    params = {
        "apiKey": api_key,
        "ip": ip,
        "fields": "geo",  # Fetch only geolocation fields for simplicity
    }
    try:
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 423:
            logging.error(
                f"Bogon IP address {ip}: {http_err} - Status Code: {response.status_code}"
            )
        else:
            logging.error(
                f"HTTP error occurred for IP {ip}: {http_err} - Status Code: {response.status_code}"
            )
    except requests.exceptions.ConnectionError as conn_err:
        logging.error(f"Connection error occurred for IP {ip}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logging.error(f"Timeout error occurred for IP {ip}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request exception occurred for IP {ip}: {req_err}")
    return None


def geocode_ips(api_key, ip_list):
    """Geocode a list of IP addresses."""
    results = []
    for index, ip in enumerate(ip_list):
        if index > 0 and index % REQUESTS_PER_MINUTE == 0:
            logging.info("Rate limit reached, sleeping for a minute")
            time.sleep(60)  # Sleep to respect rate limit
        data = get_geolocation(api_key, ip)
        if data:
            results.append(data)
        else:
            results.append({"ip": ip, "error": "Failed to fetch data"})
    return results


def process_csv(data, context):
    """Triggered by a change to a Cloud Storage bucket. Processes the CSV file."""
    # Retrieve the API key from Secret Manager
    api_key = access_secret_version(PROJECT_ID, SECRET_NAME)

    # Initialise the GCS client
    client = storage.Client()

    # Get the bucket and file information from the event data
    bucket_name = data["bucket"]
    file_name = data["name"]
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    # Download and read the CSV data
    csv_data = blob.download_as_string().decode("utf-8")
    df = pd.read_csv(pd.compat.StringIO(csv_data), header=None, names=["ip"])
    ip_list = df["ip"].tolist()

    # Geocode IP addresses
    results = geocode_ips(api_key, ip_list)

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Save results to a new CSV file in the output bucket
    output_file_name = f"geocoded_{file_name}"
    output_bucket = client.get_bucket(OUTPUT_BUCKET_NAME)
    output_blob = output_bucket.blob(output_file_name)

    output_blob.upload_from_string(results_df.to_csv(index=False), "text/csv")
    logging.info(
        f"Geocoding completed. Results saved to {output_file_name} in bucket {OUTPUT_BUCKET_NAME}"
    )
