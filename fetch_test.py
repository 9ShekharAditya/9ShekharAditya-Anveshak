import requests   # library to make HTTP calls (like a browser visiting a URL)
import pandas as pd  # library to work with tables of data
from io import StringIO  # lets pandas read text as if it were a file

# This is NASA's Exoplanet Archive API endpoint
URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# This is a SQL query — it asks NASA's database:
# "Give me the first 10 Kepler candidates that are NOT confirmed yet"
query = """
SELECT kepid, koi_disposition, koi_period, koi_prad, koi_teq, koi_insol, koi_steff
FROM cumulative
WHERE koi_disposition = 'CANDIDATE'
ORDER BY koi_insol ASC
"""

# Send the request to NASA (like visiting a URL in your browser)
response = requests.get(URL, params={
    "query": query,
    "format": "csv"       # ask for CSV format (spreadsheet-like)
})

# Check if it worked
print(f"Status code: {response.status_code}")  # 200 = success
print(f"Data size: {len(response.text)} characters\n")

# Turn the CSV text into a pandas DataFrame (a nice table)
df = pd.read_csv(StringIO(response.text))

# Show what we got
print(f"Total unconfirmed Kepler candidates: {len(df)}\n")
print("Here are the first 10:\n")
print(df.head(10).to_string(index=False))

# Explain the columns
print("\n--- What these columns mean ---")
print("kepid       = Kepler target star ID")
print("koi_disposition = Status (CANDIDATE = not yet confirmed)")
print("koi_period  = How many days the planet takes to orbit its star")
print("koi_prad    = Planet radius (in Earth radii — 1.0 = same size as Earth)")
print("koi_teq     = Equilibrium temperature (Kelvin)")
print("koi_insol   = Insolation flux (how much starlight it gets — 1.0 = same as Earth)")
print("koi_steff   = Host star temperature (Kelvin)")
