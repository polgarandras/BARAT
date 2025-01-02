import fetch_flights_wizz
import fetch_flights_ejet
import fetch_flights_ryan
import fetch_flights_vueling
import fetch_flights_eurowings
import fetch_flights_norwegian
import fetch_flights_transavia
import fetch_flights_jet2
import fetch_flights_pegasus
from datetime import datetime

# Orchestrator to fetch data for all airlines within a date range
def orchestrate_flights(start_date, end_date):
    print(f"\n--- Starting Data Fetching for All Airlines from {start_date} to {end_date} ---\n")

    # Wizz Air
    print("\nFetching Wizz Air flights...")
    fetch_flights_wizz.fetch_flights_for_period(start_date, end_date)

    # easyJet
    print("\nFetching easyJet flights...")
    fetch_flights_ejet.fetch_flights_for_period(start_date, end_date)

    # Ryanair
    print("\nFetching Ryanair flights...")
    fetch_flights_ryan.fetch_flights_for_period(start_date, end_date)

    # Vueling
    print("\nFetching Vueling flights...")
    fetch_flights_vueling.fetch_flights_for_period(start_date, end_date)

    # Eurowings
    print("\nFetching Eurowings flights...")
    fetch_flights_eurowings.fetch_flights_for_period(start_date, end_date)

    # Norwegian
    print("\nFetching Norwegian flights...")
    fetch_flights_norwegian.fetch_flights_for_period(start_date, end_date)

    # Transavia
    print("\nFetching Transavia flights...")
    fetch_flights_transavia.fetch_flights_for_period(start_date, end_date)

    # Jet2
    print("\nFetching Jet2 flights...")
    fetch_flights_jet2.fetch_flights_for_period(start_date, end_date)

    # Pegasus
    print("\nFetching Pegasus flights...")
    fetch_flights_pegasus.fetch_flights_for_period(start_date, end_date)

    print("\n--- Data Fetching Completed for All Airlines ---\n")

# Example Execution
if __name__ == "__main__":
    # Prompt user for start and end date
    start_date_input = input("Enter start date (YYYY-MM-DD): ")
    end_date_input = input("Enter end date (YYYY-MM-DD): ")

    # Convert to datetime objects
    start_date = datetime.strptime(start_date_input, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_input, '%Y-%m-%d')

    orchestrate_flights(start_date, end_date)
