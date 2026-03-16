from dotenv import load_dotenv
load_dotenv()
from urllib.parse import quote_plus
import os
password = quote_plus(os.getenv("DB_PASSWORD"))
print(password)