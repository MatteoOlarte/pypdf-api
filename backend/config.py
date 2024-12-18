import os
from dotenv import load_dotenv


# Load environment variables from a .env file
load_dotenv()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BASE_DIR, 'static')

# SECRET_KEY is used for security purposes, such as signing tokens or cookies.
# It is loaded from the environment variable T_KEY. This key should be kept secret.
SECRET_KEY = os.getenv('T_KEY')

# ALGORITHM defines the cryptographic algorithm to use for encryption processes,
# such as token generation (e.g., JWT). It is loaded from the environment variable E_ALGORITHM.
ALGORITHM = os.getenv('E_ALGORITHM')

# CONNECTION_STR contains the database connection string, which includes credentials
# and connection information. It is loaded from the environment variable C_STR.
CONNECTION_STR = os.getenv('C_STR')

# ALLOWED_HOSTS is a list of hosts that are allowed to access the application. This improves
# security by restricting access to specified hosts.
# The list includes the GitHub Pages host and the local development host.
ALLOWED_HOSTS = [
    "http://127.0.0.1:5500",
    os.getenv('HOST')
]

# max file size in mb
MAX_FILE_SIZE = 100
