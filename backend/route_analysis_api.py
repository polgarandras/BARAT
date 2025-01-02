from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from supabase import create_client, Client
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fetch unique departure and arrival airports
@app.get("/available-routes")
async def get_airports():
    try:
        query = supabase.table("all_flights_2024").select("departure_airport", "arrival_airport").execute()
        airports = query.data if query and hasattr(query, 'data') else []

        # Filter out None values to avoid the error during sorting
        unique_departures = sorted({airport['departure_airport'] for airport in airports if airport['departure_airport']})
        unique_arrivals = sorted({airport['arrival_airport'] for airport in airports if airport['arrival_airport']})

        return {
            "departure_airports": unique_departures,
            "arrival_airports": unique_arrivals
        }
    except Exception as e:
        print(f"Error fetching airports: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch airports. Error: {str(e)}")


@app.get("/route-analysis")
def route_analysis(
    departure_airport: str,
    arrival_airport: str,
    start_date: datetime,
    end_date: datetime,
):
    try:
        delta = end_date - start_date
        prev_start_date = start_date - delta - timedelta(days=1)
        prev_end_date = end_date - delta - timedelta(days=1)

        def fetch_flights(start, end):
            query = (
                supabase.table("all_flights_2024")
                .select(
                    "flight_number, flight_date, departure_airport, arrival_airport, departure_time, departure_delay, arrival_delay, airline"
                )
                .eq("departure_airport", departure_airport)
                .eq("arrival_airport", arrival_airport)
                .gte("flight_date", start.strftime("%Y-%m-%d"))
                .lte("flight_date", end.strftime("%Y-%m-%d"))
                .execute()
            )
            return query.data if query and hasattr(query, 'data') else []

        current_flights = fetch_flights(start_date, end_date)
        previous_flights = fetch_flights(prev_start_date, prev_end_date)

        if not current_flights:
            # Return empty metrics if no flights are found
            return {
                "current_period": {
                    "total_flights": 0,
                    "route_coverage": {},
                    "average_departure_delay": 0,
                    "average_arrival_delay": 0,
                    "peak_departure_times": []
                },
                "previous_period": {
                    "total_flights": 0,
                    "route_coverage": {},
                    "average_departure_delay": 0,
                    "average_arrival_delay": 0,
                    "peak_departure_times": []
                },
                "summary": "No flights found for the selected period."
            }

        def calculate_metrics(flights):
            total_flights = len(flights)
            airline_counts = {}
            delays = []
            peak_hours = {}

            for flight in flights:
                airline = flight["airline"]
                airline_counts[airline] = airline_counts.get(airline, 0) + 1
                delays.append((flight["departure_delay"], flight["arrival_delay"]))

                try:
                    departure_hour = datetime.strptime(flight["departure_time"], "%H:%M:%S").hour
                    peak_hours[departure_hour] = peak_hours.get(departure_hour, 0) + 1
                except ValueError as ve:
                    print(f"Invalid time format for flight {flight['flight_number']}: {flight['departure_time']}")
                    continue

            avg_departure_delay = round(sum(d[0] for d in delays if d[0]) / len(delays), 2) if delays else 0
            avg_arrival_delay = round(sum(d[1] for d in delays if d[1]) / len(delays), 2) if delays else 0
            route_coverage = {airline: f"{(count / total_flights) * 100:.2f}%" for airline, count in airline_counts.items()}
            peak_times = sorted(peak_hours.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                "total_flights": total_flights,
                "route_coverage": route_coverage,
                "average_departure_delay": avg_departure_delay,
                "average_arrival_delay": avg_arrival_delay,
                "peak_departure_times": [f"{hour}:00 - {hour + 1}:00" for hour, _ in peak_times],
            }

        current_metrics = calculate_metrics(current_flights)
        previous_metrics = calculate_metrics(previous_flights)

        def generate_summary(current_metrics, previous_metrics):
            prompt = f"""
            Please analyze the flight route performance metrics for the current and previous periods. 
            Structure the response in a formal, report-style format with the following sections: 

            1. **Total Flights and Route Coverage** – Include a brief comparison of total flights and coverage. 
            2. **Average Departure Delay** – Provide a summary of departure delay changes between periods. 
            3. **Average Arrival Delay** – Summarize any changes in arrival delays. 
            4. **Peak Departure Times** – Highlight key peak times and compare any changes.

            Return the analysis with each section clearly separated by a new paragraph. 
            Avoid using bullet points or numbered lists. 
            Ensure smooth transitions between sections for better readability.

            Current Period: {current_metrics}
            Previous Period: {previous_metrics}
            """
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an aviation route analysis assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500
                )
                # Correct way to access the content
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI API Error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"AI summary generation failed. Error: {str(e)}")

        summary = generate_summary(current_metrics, previous_metrics)

        return {
            "current_period": current_metrics,
            "previous_period": previous_metrics,
            "summary": summary,
        }

    except Exception as e:
        print(f"Unexpected Error in /route-analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error. Check server logs for more details.")
