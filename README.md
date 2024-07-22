
# IP Geocoding Script

This repository contains two versions of an IP geocoding script. The first version is designed to run locally and is fully executable. The second version is structured for integration with Google Cloud Platform (GCP), using Cloud Functions and Google Cloud Storage (GCS).

## Local Version

### Description

The local version of the IP geocoding script reads a list of IP addresses from a CSV file, uses an external geolocation API to retrieve location data for each IP address, and writes the results to an output CSV file.

### Dependencies

- requests
- pandas

## GCP Version

### Description

The GCP version of the IP geocoding script is designed to run as a Google Cloud Function, triggered by a new file upload to a Google Cloud Storage (GCS) bucket. It retrieves IP addresses from the uploaded CSV file, uses an external geolocation API to retrieve location data, and writes the results to another GCS bucket.

### Dependencies

- requests
- pandas
- google-cloud-storage
- google-cloud-logging
- google-cloud-secretmanager
