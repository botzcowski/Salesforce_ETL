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
├── extract/        # Extraction and staging scripts
├── transform/      # Transformation scripts
├── load/           # Salesforce upsert scripts
├── staging/        # Staged data (not committed to version control)
├── config/         # Configuration (field mappings, object settings)
├── requirements.txt
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
pip install -r requirements.txt
```

Provide Salesforce credentials through environment variables or a local `.env` file (excluded via `.gitignore`):

```
SF_USERNAME=
SF_PASSWORD=
SF_SECURITY_TOKEN=
SF_DOMAIN=login   # or "test" for sandbox
```

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

Specify your license here.
