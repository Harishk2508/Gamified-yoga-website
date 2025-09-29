# create_db.py
from backend.database.connection import initialize_database

print("Attempting to create a new, clean database...")
initialize_database()
print("Script finished.")
