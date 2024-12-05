from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from google.cloud.sql.connector import Connector
import sqlalchemy
from google.cloud import secretmanager

# Function to retrieve CloudSQL instance password from Secret Manager
def access_secret_version(project_id, secret_id, version_id):
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")

    return payload

# Store CloudSQL instance password in a local variable    
def get_db_password():
    return access_secret_version('skinsift-2024', 'skinsift_sql_pwd', '2')

# Initialize Connector object
connector = Connector()

# Function to return CloudSQL database connection
def getconn():
    print("Connecting to Cloud SQL...")
    sql_password = get_db_password()
    conn = connector.connect(
        "skinsift-2024:asia-southeast2:skinsift-app",
        "pymysql",
        user="root",
        password=sql_password,
        db="skinsift_app",
    )
    print("Connected to the database!")
    return conn

# Create connection pool for SQLAlchemy
def create_connection_pool():
    return sqlalchemy.create_engine(
        "mysql+pymysql://",
        creator=getconn,
        pool_size=5,  # Set desired pool size
        max_overflow=10  # Set desired max overflow value
    )

# Inisialisasi connection pool untuk SQLAlchemy
engine = create_connection_pool()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency untuk session database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
