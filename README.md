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

- Insert or update records using an external ID or record ID via Bulk API 2.0
- Handle batching and API limits by splitting the CVS files into n number of records per file. 
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

## If staging of data in MSSQL is needed:

Driver required on local machine:
MSSQL ODBC Driver

## Folder structure 

Create a top containing folder, the name of the folder should be the same as the organization name, e.g.: causeway. 
Create sub folders for intake, logs, outuput, and staging of files; e.g.: in, logs, out, stage. These subfolder names will then be provided to the scripts via input parameter values.

## Config files 

Salesforce related configurations, named as config_[organization].json, example: config_causeway.json.
- max_day_range: the number of days plus from the last extract run date to derive the lower-bound CDC date. 
- max_records_per_file: the number records to send to Salesforce for bulk API 2.0 operation (limit is 150 MB, and Salesforce will break into batches of 2,000).    
- transform_sf_system_fields: boolean, when true Salesforce object system fields are inserted with specified values, i.e.: Enable 'Create Audit Fields'  
- db: the name of the Mongo or MSSQL database name, leave blank when not inserting record into a staging database.
- target_objects: the object name when the source data is to be transformed into another object. For each target object specify the source object, the related objects, and the field on the related object to lookup to the source object.
- Example:

    ```json
    {
        "max_day_range": 365,
        "max_records_per_file": 200000,
        "sf_api_version": "64.0",
        "extract_add_sf_system_fields": false,
        "transform_sf_system_fields": true,
        "db": "",
        "target_objects": [
            {
                "source_object": {"name": "asset"},
                "target_object": {"name": "InsurancePolicy",
                                  "source_id_field": "Source_Asset_Id__c",   
                                  "related_objects": [
                                        {
                                            "related_object": "case",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "AssetId"
                                        },
                                        {
                                            "related_object": "task",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "event",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "claims_contact_staging__c",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "pcipal_transaction__c",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "sms_staging__c",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "endorsement__c",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "claim",
                                            "relationship_field": "PolicyNumberId",
                                            "source_field": "AssetId__c"
                                        },
                                        {
                                            "related_object": "messagingsession",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        },
                                        {
                                            "related_object": "coi_details__c",
                                            "relationship_field": "Insurance_Policy__c",
                                            "source_field": "Policy__c"
                                        }                                    
                                  ]},            
                "external_id_field": "Source_Asset_Id__c"
            }
        ]
    }
    
    ```

MSSQL/MongoDB credentials, named as db_config_[organization].json, example: db_config_causeway.json. Best practice is to store this information in environment variables. 

Salesforce login credentials, named as login_[organization].json, example: login_causeway.json. Best practice is to store this information in environment variables. 
Create an External Client App, enable Client Credential Flow, generate Consumer Key and Secret.
- consumer_key: the consumer key from the External Client App
- consumer_secret: the secret from the External Client App
- domain: the my domain name up to "my", example: "causeway--testing.sandbox.my", this is a workaround for simple_salesforce's lack of support for custom domains.

## Usage
- Extraction: the sf_data_extract_all.py script looks for 2 files for each source object in the folder specified in the -objdir parameter
    - file containing the last run date; file name = [source object api name]_last_run.txt, e.g.: account_last_run.txt. The datetime value stored in the file is in the UTC format, e.g.: 2025-12-23T05:27:15Z, and it's used as the lower-bound CDC date (SOQL filter on SystemModStamp) 
    - file containing the source object field api names to be extracted, delimited by comma or JSON string; file name = [source object api name].txt, e.g.: account.txt. When transforming a source object's data to a target object then the JSON string is configuration information to a field mapping file as in this example:
    ```json
     {
       "format": "Excel",
       "file": "Asset to Insurance Policy Mapping.xlsx",
       "source_field_column_name": "Asset Field Name",
       "target_field_column_name": "Policy Field Name",
       "transformation_column_name": "Transformation"
     }
    ``` 
- Determine if you will need to work with related objects, i.e. you need to re-link the child/lookup relationship after completing the ETL work for the source or source-to-target object. If yes, then modify the config_[organization].json accordingly.
- For each object the sf_data_extract.py is called to executes the extraction using the Salesforce REST API, the results is formatted as csv files and placed into the folder named in the -datadir parameter.
- Insert the extracted data into a database when there is a need to profile the data for quality such as missing values or values not defined in a pick list field.
- Transformation: the sf_data_transform_all.py reads all files in the folder specified in the -stagedir parameter, for each file the sf_data_transform.py script is invoked. Field transformation logic/rule is defined in the field mapping in the column named by "transformation_column_name" in configuration.
- Load: splitting of csv files by n number of record might be required to manage the number of nonconcurrent batch runs on Salesforce. For example, a csv file with 200,000 records will result in 20 batches. The sf_data_load_all.py script reads all csv files in the folder specified by the -stagedir parameter and invoke sf_data_load.py for each file.   

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
