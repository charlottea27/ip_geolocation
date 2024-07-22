import requests
import pandas as pd
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set the base logging level
    format="%(asctime)s %(levelname)s:%(message)s",  # Log message format
    handlers=[
        logging.FileHandler("geocode_ips.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the terminal
    ],
)

# Constants
API_KEY = "e64746da9ae6433c9232268ef1cc465c"
API_URL = "https://api.ipgeolocation.io/ipgeo"
INPUT_CSV = "ip-addresses.csv"
OUTPUT_CSV = "geocoded_ip_addresses.csv"
REQUESTS_PER_MINUTE = 60  # Rate limit as per free account


def get_geolocation(ip):
    """Fetch geolocation data for a given IP address."""
    params = {
        "apiKey": API_KEY,
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


def geocode_ips(ip_list):
    """Geocode a list of IP addresses."""
    results = []
    for index, ip in enumerate(ip_list):
        if index > 0 and index % REQUESTS_PER_MINUTE == 0:
            logging.info("Rate limit reached, sleeping for a minute")
            time.sleep(60)  # Sleep to stay within rate limit
        data = get_geolocation(ip)
        if data:
            results.append(data)
        else:
            results.append({"ip": ip, "error": "Failed to fetch data"})
    return results


def main():
    """Main function to read IPs, geocode them, and save the results."""
    # Read IP addresses from CSV without a header
    try:
        df = pd.read_csv(INPUT_CSV, header=None, names=["ip"])
        ip_list = df["ip"].tolist()
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        return

    # Geocode IP addresses
    results = geocode_ips(ip_list)

    # Convert results to DataFrame and save to CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Geocoding completed. Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
