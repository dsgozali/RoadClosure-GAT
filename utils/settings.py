import os
from distutils.util import strtobool

from dotenv import load_dotenv

load_dotenv()

APP_DEBUG = bool(strtobool(os.getenv("DEBUG", "True")))
# SNOWFLAKE_API_KEY = os.getenv("SNOWFLAKE_API_KEY")
# AWS_API_KEY = os.getenv("AWS_API_KEY")
