import pandas as pd
import requests
import logging
import os
# Configure logging for error handling and tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class SportradarExtractor:
    def __init__(self, api_key: str):
        """
        Initializes the extractor with the Sportradar API key.
        """
        self.api_key = api_key
        self.headers = {"accept": "application/json"}
        # Base URL for Sportradar Tennis API vs v3trial

        self.base_url = "https://api.sportradar.com/tennis/trial/v3/en"
    def _make_request(self, endpoint: str) -> dict:
        """
        Helper method to make API requests with error handling.
        """
        url = f"{self.base_url}/{endpoint}.json?api_key={self.api_key}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occured: {http_err} -URL: {url}")
        except Exception as err:
            logging.error(f"An error occured: {err}")
        return {}
    def extract_competitions(self) -> dict:
        """
        Extracts competition and category data from the endpoint.
        
        """    
        logging.info("Fetching competition data...")
        return self._make_request("competitions")
    def extract_complexes(self) -> dict:
        """
        Extracts sports complexes and venue data from the endpoint.
        
        """
        logging.info("Fetching complexes data...")
        return self._make_request("complexes")
    def extract_doubles_rankings(self) -> dict:
        """
        Extracts doubles competitor rankings data from the endpoint.
    
        """
        logging.info("Fetching doubles competitor rankings data...")
        return self._make_request("double_competitors_rankings") # Adjust endpoint as per specific trial documentation path
    def save_to_excel(self, data: dict, filename: str, key_name: str):
        """
        Helper method to convert a specific dictinory key from JSON into a Pandas DataFrame
        and export it to an Excel file.
        """
        if not data or key_name not in data:
            logging.warning(f"No valid data found foe key '{key_name}' to save. Available keys: {list(data.keys()) if data else 'None'}") 
            return
        # Convert the list of dictionaries under the target key into a DataFrame
        df = pd.DataFrame(data[key_name])
        # Save to Excel
        df.to_excel(filename, index=False)
        logging.info(f"Successfully saved data to {filename}")
        print(f"File saved: {filename}")

    def save_rankings_to_excel(
        self, data: dict, filename: str, key_name: str = "rankings"
    ):
        """
        Flattens the nested rankings response (one row per competitor, not
        one row per tour) and saves it to Excel. This avoids Excel's
        32,767-character cell limit, which truncates the raw nested JSON.
        """
        if not data or key_name not in data:
            logging.warning(
                f"No valid data found for key '{key_name}' to save. "
                f"Available keys: {list(data.keys()) if data else 'None'}"
            )
            return

        flat_rows = []
        for tour in data[key_name]:
            for entry in tour.get("competitor_rankings", []):
                competitor = entry.get("competitor", {})
                flat_rows.append(
                    {
                        "tour": tour.get("name"),
                        "gender": tour.get("gender"),
                        "year": tour.get("year"),
                        "week": tour.get("week"),
                        "rank": entry.get("rank"),
                        "movement": entry.get("movement"),
                        "points": entry.get("points"),
                        "competitions_played": entry.get("competitions_played"),
                        "competitor_id": competitor.get("id"),
                        "name": competitor.get("name"),
                        "country": competitor.get("country"),
                        "country_code": competitor.get("country_code"),
                        "abbreviation": competitor.get("abbreviation"),
                    }
                )

        df = pd.DataFrame(flat_rows)
        df.to_excel(filename, index=False)
        logging.info(
            f"Successfully saved {len(df)} ranking rows to {filename}"
        )
        print(f"File saved: {filename} ({len(df)} rows)")
    
# --- Example Usage ---
if __name__ == "__main__":
        API_KEY = os.environ.get("SPORTRADAR_API_KEY")
        if not API_KEY:
            raise SystemExit(
                "Set the SPORTRADAR_API_KEY encironment variable before running this script."

            )
        extractor = SportradarExtractor(api_key=API_KEY)
        # Test extraction
        competitions_data = extractor.extract_competitions()
        print("Competitions Data Fetched Successfully!")
        extractor.save_to_excel(competitions_data, "competitions.xlsx", "competitions")
        complexes_data = extractor.extract_complexes()
        print("Complexes Data Fetched Successfully!")
        extractor.save_to_excel(complexes_data, "complexes.xlsx", "complexes")

        rankings_data = extractor.extract_doubles_rankings()
        print("Rankings Data Fetched Successfully")
        extractor.save_rankings_to_excel(rankings_data, "double_competitors_rankings.xlsx")


    