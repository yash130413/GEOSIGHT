import pandas as pd
import sqlite3
import os

# Configurations
# Folder holding the datasets and outputs (formerly a personal Desktop path).
# Set GEOSIGHT_DATA_ROOT to use another location; defaults to the repository root.
DATA_ROOT = os.environ.get("GEOSIGHT_DATA_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CSV_PATH = os.path.join(DATA_ROOT, "geosight_manifest_70k.csv")
DB_PATH = os.path.join(DATA_ROOT, "geosight.db")

def build_database():
    print(f"🚀 Reading dataset manifest from: {CSV_PATH}")
    if not os.path.exists(CSV_PATH):
        print("❌ Manifest CSV not found! Please check the path and try again.")
        return
        
    # Read the large CSV file
    df = pd.read_csv(CSV_PATH)
    
    print(f"✅ Loaded {len(df)} records. Writing to SQLite Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    
    # Dump entire dataframe into a table named 'manifest'
    df.to_sql("manifest", conn, if_exists="replace", index=False)
    conn.close()
    
    print("🎉 Database successfully created!")
    print("You can now connect the `geosight-sqlite` MCP server and have the AI run SQL queries on your dataset.")

if __name__ == "__main__":
    build_database()
