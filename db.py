import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

db = MySQLdb.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    passwd=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME")
)

cursor = db.cursor()
