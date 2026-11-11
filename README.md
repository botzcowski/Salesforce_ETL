# Salesforce_ETL

Python-based ETL (Extract, Transform, Load) tooling for moving data into and out of Salesforce.

## Objective

This repository uses Python to **extract**, **transform**, and **load** data stored in Salesforce or sourced from CSV files. Data is pulled from its source, staged, cleaned and reshaped according to business rules, and then upserted back into Salesforce.

## How It Works

```
 ┌────────────────────┐     ┌──────────────────┐     ┌────────────────────┐
 │  Salesforce / CSV  │ ──► │   Extract &      │ ──► │   Transform        │
 │  (data sources)    │     │   Stage          │     │   (staged data)    │
 └────────────────────┘     └──────────────────┘     └─────────┬──────────┘
                                                               │
                                                               ▼
                                                     ┌────────────────────┐
                                                     │  Upsert to         │
                                                     │  Salesforce        │
                                                     └────────────────────┘
```

## Code Modules

The code is organized into three groups of scripts, one for each stage of the pipeline.

### 1. Extraction and Staging
Scripts that retrieve data from its source and land it in a staging area.

- Extract records from Salesforce (e.g., via SOQL queries or the Bulk API)
- Read and load data from CSV files
- Write the raw data to a staging location for downstream processing

### 2. Transformation
Scripts that operate on the staged data to prepare it for loading.

- Clean and validate data (nulls, duplicates, formatting, data types)
- Apply business rules and field mappings
- Reshape the data to match the target Salesforce object schema

### 3. Upsert to Salesforce
Scripts that load the transformed data back into Salesforce.

- Upsert records using an external ID or other unique key
- Handle batching and API limits
- Capture and report success and error results

## Repository Structure

> Update the paths below to match your actual layout.

```
.
├── sf_data_extract_all.py           # Extraction script for all parent objects
├── sf_data_extract.py               # Extraction script for each parent object
├── sf_data_extract_related_all.py   # Optional; extraction script for all related objects
├── sf_data_extract_related.py       # Optional; extraction script for each related object
├── sf_data_transform_all.py         # Transformation script for all parent objects
├── sf_data_transform.py             # Transformation script for each parent object
├── sf_data_transform_related_all.py # Transformation script for all related objects
├── sf_data_transform_related.py     # Transformation script for each related objects
├── sf_data_transform_split_all.py   # Script to split a large csv file into smaller files for upsert into Salesforce - for all objects. 
├── sf_data_transform_split.py       # Script to split a large csv file into smaller files for upsert into Salesforce - for an object.
├── sf_data_load_all.py              # Script to upsert into Salesforce - for all objects.
├── sf_data_load.py                  # Script to upsert into Salesforce - for an object.
├── sf_data_delete_all.py            # Script to delete records inserted into Salesforce - for all object.
├── sf_data_delete.py                # Script to delete records inserted into Salesforce - for an object.
├── sf_utility.py
├── mongodb_utility.py                    
└── README.md
```

## Prerequisites

- Python 3.9+
- A Salesforce account with API access
- Salesforce credentials or a connected app (stored securely, never committed)

## Setup

```bash
# Clone the repository
git clone <repository-url>
cd <repository-name>

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
python3 -m pip install simple_salesforce salesforce_bulk pandas tabulate openpyxl pymongo sqlalchemy pyodbc
```

Provide Salesforce credentials through environment variables or a local `.env` file (excluded via `.gitignore`):

```
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=
SF_DOMAIN=login   # or "test" for sandbox
```

## If staging of data in MSSQL is needed:

Driver required on local machine:
MSSQL ODBC Driver

## Folder structure 

Create a top containing folder, the name of the folder should be the same as the organization name, e.g.: causeway. 
Create sub folders for intake, logs, outuput, and staging of files; e.g.: in, logs, out, stage. These subfolder names will then be provided to the scripts via input parameter values.

## Config files 

Salesforce related configurations, named as config_<organization>.json, example: config_causeway.json.
- max_day_range: the number of days back from the last extract run date to derive the lower-bound CDC date. 
- max_records_per_file: the number records to send to Salesforce for bulk API 2.0 operation (limit is 150 MB, and Salesforce will break into batches of 2,000).    
- transform_sf_system_fields: boolean, when true Salesforce object system fields are inserted with specified values, i.e.: Enable 'Create Audit Fields'  
- db: the name of the Mongo or MSSQL database name, leave blank when not inserting record into a staging database.
- target_objects: for each target object specify the source object and the related objects.

MSSQL/MongoDB credentials, named as db_config_<organization>.json, example: db_config_causeway.json. Best practice is to store this information in environment variables. 

Salesforce login credentials, named as login_<organization>.json, example: login_causeway.json. Best practice is to store this information in environment variables. 
Create an External Client App, enable Client Credential Flow, generate Consumer Key and Secret.
- consumer_key: the consumer key from the External Client App
- consumer_secret: the secret from the External Client App
- domain: the my domain name up to "my", example: "causeway--testing.sandbox.my", this is a workaround for simple_salesforce's lack of support for custom domains.

## Usage

Run each stage in order:

```bash
python extract/<extract_script>.py
python transform/<transform_script>.py
python load/<upsert_script>.py
```

## Notes

- Never commit credentials, API tokens, or staged data containing sensitive information.
- Test against a Salesforce sandbox before running upserts in production.

## Contributing

Contributions are welcome. Please open an issue or submit a pull request.

## License

GNU General Public License v3.0
