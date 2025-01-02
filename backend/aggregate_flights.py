from dotenv import load_dotenv
from fastapi import FastAPI
from supabase import create_client, Client
from datetime import datetime
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

AIRLINE_TABLES = [
    "wizz_flights",
    "easyjet_flights",
    "ryanair_flights",
    "vueling_flights",
    "eurowings_flights",
    "pegasus_flights",
    "transavia_flights",
    "norwegian_flights",
    "jet2_flights",
]

BATCH_SIZE = 500
UUID_BATCH_SIZE = 500  # Batch size for UUID comparison to avoid 414 errors

# Fetch the latest date from the aggregated table
latest_date_query = supabase.table("all_flights_2024") \
    .select("flight_date") \
    .order("flight_date", desc=True) \
    .limit(1) \
    .execute()

latest_date = latest_date_query.data[0]['flight_date'] if latest_date_query.data else None
print(f"Latest date in all_flights_2024: {latest_date}")

# Loop through each airline table to aggregate new data
for airline_table in AIRLINE_TABLES:
    print(f"\nFetching new flights from {airline_table}...")

    total_inserted = 0
    offset = 0  # Initialize offset for pagination

    while True:
        # Fetch flights in batches using incremental offsets
        flights_query = supabase.table(airline_table) \
            .select("*") \
            .gt("flight_date", latest_date) \
            .range(offset, offset + BATCH_SIZE - 1) \
            .execute()

        flights = flights_query.data if flights_query.data else []

        if not flights:
            print(f"Finished aggregating {total_inserted} flights from {airline_table}")
            break

        # Batch UUIDs to avoid 414 URI Too Large errors
        flight_ids = [f["id"] for f in flights]
        existing_ids = set()

        # Fetch existing UUIDs in batches
        for i in range(0, len(flight_ids), UUID_BATCH_SIZE):
            batch = flight_ids[i:i + UUID_BATCH_SIZE]
            existing_ids_query = supabase.table("all_flights_2024") \
                .select("id") \
                .in_("id", batch) \
                .execute()

            existing_ids.update({f["id"] for f in existing_ids_query.data})

        # Filter out flights that already exist in the aggregated table
        new_flights = [
            flight for flight in flights
            if flight["id"] not in existing_ids
        ]

        if not new_flights:
            print(f"No new flights to aggregate from {airline_table}. Skipping...")
            offset += BATCH_SIZE  # Increment offset to continue checking next batch
            continue

        # Prepare data for insertion
        data = [
            {
                "id": flight["id"],
                "flight_number": flight["flight_number"],
                "flight_date": flight["flight_date"],
                "departure_airport": flight["departure_airport"],
                "arrival_airport": flight["arrival_airport"],
                "airline": flight["airline"],
                "departure_time": flight["departure_time"],
                "departure_delay": flight["departure_delay"],
                "arrival_delay": flight["arrival_delay"],
                "status": flight["status"],
                "inserted_at": datetime.now().isoformat()
            }
            for flight in new_flights
        ]

        if data:
            supabase.table("all_flights_2024").insert(data).execute()
            total_inserted += len(data)
            print(f"Inserted {len(data)} flights from {airline_table}")

        offset += BATCH_SIZE  # Increment offset for pagination

        # Continue fetching flights until no more are returned
        if len(flights) < BATCH_SIZE:
            break

print("Aggregation complete for all airline tables.")
