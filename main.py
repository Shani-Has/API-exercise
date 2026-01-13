#!/usr/bin/env python3
import requests
import time

class HomeworkClient:
    """
        HomeworkClient fetches weather data for a city using a short-lived token,
        handles pagination and network errors, and computes the average noon temperature.
    """
    MAX_ERROR = 5
    TOKEN_TIMEOUT = 55
    AUTHENTICATION_URL = "https://gw4favkunc.execute-api.il-central-1.amazonaws.com/auth"

    def __init__(self):
        """
            Initialize the client with empty token, city, and data storage.
        """
        self.token = None
        self.token_time = 0
        self.city = None
        self.req_id = None
        self.url = None
        self.all_items = []

    def get_token(self):
        """
            Request a new authentication token from AUTHENTICATION_URL
            and updates city, request ID, and data URL.
            Handles network errors by setting token to None if the
            request fails.
            """
        try:
            auth_response = requests.post(self.AUTHENTICATION_URL)
            auth_info = auth_response.json()
            self.token = auth_info['token']
            self.token_time = time.time()
            self.city = auth_info['dataset']
            self.req_id = auth_info['request_id']
            self.url = auth_info['data_url']
        except requests.exceptions.RequestException as e:
            print("Network Error while getting token.", e)
            self.token = None

    def validate_token(self):
        """
            Makes sure the current token is valid. If token is expired or missing, the function fetches a new one.
            """
        if self.token is None or (time.time() - self.token_time) >= self.TOKEN_TIMEOUT:
            self.get_token()

    def get_page(self, page_number, max_retries=3, delay=0.5):
        """
            Fetch a single page of weather data using the current token.
            Retries the request if it fails, up to max_retries times with a delay.
            Args:
                page_number (int): The page number to fetch.
                max_retries (int): Number of retry attempts if request fails.
                delay (float): Delay in seconds between retries.
            Returns:
                    tuple: (items, total_pages)
                        items (list): List of items in this page.
                        total_pages (int): Total number of pages in the dataset.
        """
        self.validate_token()
        page_params = {"request_id": self.req_id, "page": page_number}
        headers = {'Authorization': f'Bearer {self.token}'}

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(self.url, headers=headers, params=page_params)
                response.raise_for_status()
                data = response.json()
                return data.get('items', []), data.get('total_pages', 1)

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt} failed for page {page_number}: {e}")
                if attempt < max_retries:
                    time.sleep(delay)
                else:
                    print(f"Page {page_number} failed after {max_retries} attempts.")
                    return [], 1

    def run(self):
        """
            Run the client: fetch all pages, aggregate items, calculates the average temperature.
            Print the results.
       """
        current_page = 1
        total_pages = 1
        error_counter = 0

        self.get_token()

        while current_page <= total_pages:
            items, total_pages = self.get_page(current_page)
            if items:
                self.all_items.extend(items)
                current_page += 1
                error_counter = 0
            else:
                print(f"Failed to get page {current_page}")
                error_counter += 1
                current_page += 1

            if error_counter >= self.MAX_ERROR:
                print("Too many errors, stopping pagination")
                break

        if self.all_items:
            average_temp = sum(item['temperature_noon_c'] for item in self.all_items) / len(self.all_items)
            print(f"City: {self.city}")
            print(f"Average temperature: {average_temp:.3f}")
        else:
            print(f"City: {self.city}")
            print("No data received.")


if __name__ == "__main__":
    client = HomeworkClient()
    client.run()
