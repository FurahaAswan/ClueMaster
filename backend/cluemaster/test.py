import os
import json
from os.path import join, dirname
from dotenv import load_dotenv

from pathlib import Path

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
load_dotenv()

print([json.loads(os.environ.get('ALLOWED_HOSTS'))])