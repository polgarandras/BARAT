import requests
import uuid
from datetime import timedelta
from database import supabase

API_KEY = "06d26a2b5ab73393271a798ea814c458"
BASE_URL = "http://api.aviationstack.com/v1/flights"

# Fetch Ryanair flights for a specific date
def fetch_ryanair_flights(date):
    results = []
    offset = 0
    limit = 100

    while True:
        params = {
            'access_key': API_KEY,
            'limit': limit,
            'offset': offset,
            'flight_date': date,
            'airline_iata': 'FR'  # Ryanair IATA Code
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if 'data' in data:
            results.extend(data['data'])
            offset += limit
            print(f"Fetched {len(data['data'])} Ryanair flights for {date}, offset now {offset}")
            
            if len(data['data']) < limit:
                break
        else:
            print(f"Error fetching Ryanair data for {date}: {data.get('error', 'Unknown error')}")
            break
    
    return results

# Insert Ryanair flights into Supabase table
def insert_into_supabase(data):
    for flight in data:
        if 'flight' not in flight or 'number' not in flight['flight']:
            print(f"Skipping Ryanair flight due to missing flight number on {flight['flight_date']}")
            continue

        flight_number = flight['flight']['number']
        flight_date = flight['flight_date']

        flight_uuid = str(uuid.uuid4())
        departure_delay = flight['departure'].get('delay', 0)
        arrival_delay = flight['arrival'].get('delay', 0)
       
        departure_time = flight['departure'].get('scheduled', '00:00')
        departure_time = departure_time.split('T')[-1] if 'T' in departure_time else departure_time
        
        response = supabase.table("ryanair_flights").insert({
            "id": flight_uuid,
            "flight_date": flight_date,
            "flight_number": flight_number,
            "departure_airport": flight['departure']['airport'],
            "arrival_airport": flight['arrival']['airport'],
            "airline": flight['airline']['name'],
            "departure_time": departure_time,
            "departure_delay": departure_delay,
            "arrival_delay": arrival_delay,
            "status": flight.get('flight_status', 'unknown')
        }).execute()

        if not response.data:
            print(f"Failed to insert Ryanair flight {flight_number} on {flight_date} at {departure_time}")

# Fetch data for a specified period (Function orchestrator expects)
def fetch_flights_for_period(start_date, end_date):
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"\nFetching Ryanair flights for {date_str}...")

        flights = fetch_ryanair_flights(date_str)

        if flights:
            insert_into_supabase(flights)
            print(f"Completed {len(flights)} Ryanair records for {date_str}\n")
        else:
            print(f"No Ryanair data for {date_str}\n")
        
        current_date += timedelta(days=1)
