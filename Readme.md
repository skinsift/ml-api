# Machine Learning Model API

This project provides APIs for machine learning functionalities specifically designed for skincare applications. The core features include predicting skin type through the analysis of user-uploaded images and assessing skincare products by evaluating their ingredients and aligning them with user needs. The application is containerized using Docker and deployed to Google Cloud Run, ensuring scalability, maintainability, and seamless integration with frontend applications and other backend systems.

## Access Our Deployed API :

[API Model ML SkinSift](https://mlapi-956646968871.asia-southeast2.run.app/).

---

# Key Features:

Skin Type Prediction:
Analyzes user-uploaded images to determine the user's skin type, providing accurate predictions for skincare personalization.

Product Assessment:
Evaluates skincare products based on their ingredients and matches them with user preferences, helping to recommend suitable products.

Containerized Application:
The application is containerized using Docker and deployed to Google Cloud Run, ensuring scalability, easy maintenance, and reliable performance.

---

# API Documentation

[this link](https://field-ridge-34b.notion.site/SkinSift-API-Docs-15960ff96d508037a0aad64f34924953)

---

# Skinsift Database Connection

This project demonstrates how to connect a Python application to a Google Cloud SQL database using SQLAlchemy and Google Cloud SQL Connector. The database credentials are securely managed through Google Cloud Secret Manager.

---

## Prerequisites

Before running the code, ensure the following prerequisites are met:

1. **Google Cloud SQL Instance**:

   - A Cloud SQL instance with the name `skinsift-2024:asia-southeast2:skinsift-app`.
   - The database `skinsift_app` is created inside this instance.

2. **Secrets in Secret Manager**:

   - Create a secret in Google Cloud Secret Manager named `skinsift_sql_pwd` containing the Cloud SQL root password.

3. **Google Cloud SDK**:

   - Install and authenticate the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install).

4. **Dependencies**:
   - Install the required Python libraries using:
     ```bash
     pip install sqlalchemy pymysql google-cloud-secret-manager google-cloud-sql-connector
     ```

## How It Works

### 1. **Database Password Management**

The database password is securely stored in Google Cloud Secret Manager. The `access_secret_version` function fetches the password when required.

### 2. **SQLAlchemy Engine Creation**

The `getconn` function uses Google Cloud SQL Connector to establish a secure connection to the Cloud SQL instance. This connection is then used to create a SQLAlchemy engine with a connection pool.

### 3. **Database Session Handling**

The SQLAlchemy `SessionLocal` object is used to manage database sessions.

## Code Overview

### Main Functions

- **`access_secret_version`**: Retrieves the database password from Secret Manager.
- **`get_db_password`**: Calls `access_secret_version` to fetch the password.
- **`getconn`**: Establishes a secure connection to the Cloud SQL instance.
- **`create_connection_pool`**: Creates a SQLAlchemy engine with a connection pool.
- **`get_db`**: Dependency for managing database sessions.

## Usage

### Running the Code

1. Ensure all prerequisites are met.
2. Set up your Google Cloud credentials with the following command:
   ```bash
   gcloud auth application-default login
   ```
3. Execute the script
   ```bash
   python your_script_name.py
   ```

### Output

The script will:
Establish a connection to the Cloud SQL database.
Print "Connecting to Cloud SQL..." and "Connected to the database!" if successful.

## Troubleshooting

Common Issues
Cloud SQL Connection Errors:

Ensure the instance connection name and database name are correct.
Verify your IAM roles allow access to Secret Manager and Cloud SQL.
Secret Not Found:

Ensure the secret exists in Secret Manager and matches the specified name.
Python Library Import Errors:

Run pip install -r requirements.txt if you're missing dependencies.

---

# Running the Application Locally

## 1. Cloning the Repository

```bash
git clone <repository_url>
cd <project_folder>
```

## 2. Installing Requirements

```bash
pip install -r requirements.txt
```

## 3. Modifying Access to Secret Manager

Open the `connect.py` file.
Update the following section:

```python
sql_password = access_secret_version('YOUR_PROJECT_ID', 'scancare_sql_pwd', '1')
```

Replace YOUR_PROJECT_ID with your Google Cloud project ID.

## 4. Modifying Connection to Database

Open the `connect.py` file.
Update the following section:

```python
def getconn():
    conn = connector.connect(
        "YOUR_SQL_INSTANCE_CONNECTION_NAME",
        "pymysql",
        user="root",
        password=sql_password,
        db="bpom",
    )
    return conn
```

Replace YOUR_SQL_INSTANCE_CONNECTION_NAME with your SQL instance connection name.

## 5. Running the FastAPI Application

Open the `main.py` file.
Update the run configuration:

```python
port = int(os.environ.get('PORT', 8080))
print(f"Listening to http://localhost:{port}")
uvicorn.run(app, host='localhost', port=port)
```

## 6. Starting the Local Server

```bash
python main.py
```

## 7. Accessing the API

- Use the API endpoints as documented earlier.
- Test the endpoints using Postman:
  Open Postman and create a new request.
  Set the request method (e.g., GET, POST) and enter the API endpoint URL (e.g., `http://localhost:8080/<endpoint>`).
  If required, add headers, query parameters, or body data as per the API specifications.
  Send the request and verify the response.

---

# Deploying the Application to Cloud Run

```bash
# Cloning the Repository
git clone <repository_url>

# Change to the destined directory
cd <project_folder>

# Create a Docker Artifact Repository in a specified region
gcloud artifacts repositories create YOUR_REPOSITORY_NAME --repository-format=docker --location=YOUR_REGION

# Build Docker image for the ML API
docker buildx build --platform linux/amd64 -t YOUR_IMAGE_PATH:YOUR_TAG --build-arg PORT=8080 .

# Push the Docker image to the Artifact Repository
docker push YOUR_IMAGE_PATH:YOUR_TAG

# Deploy the Docker image to Cloud Run with allocated memory
gcloud run deploy --image YOUR_IMAGE_PATH:YOUR_TAG --memory 3Gi

# Fetching the service account associated with the newly deployed Cloud Run service
SERVICE_ACCOUNT=$(gcloud run services describe YOUR_SERVICE_NAME --platform=managed --region=YOUR_REGION --format="value(serviceAccountEmail)")

# Grant necessary IAM roles to the service account linked to the Cloud Run service
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member=serviceAccount:${SERVICE_ACCOUNT} --role=roles/cloudsql.client
```
