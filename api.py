import requests # Import the requests library to handle HTTP requests

class API_Client:
    
    """
    A api that fetches exercises based on user characteristics.
    Searches for exercise passed by the machine learning model and adds instructions, the muscle group,
    type of exercise, and difficulty to the exercise information so that app can portray additional data to user
    """

    def __init__(self):
        # Initialize the class with an API key and optional filters for exercises.
        self.api_key = 'HO2NHkU1SicR4ZiYoXlheQ==il90Q0KOwcMhfNJ6' # Store the API key needed for authorization
        self.base_url = 'https://api.api-ninjas.com/v1/exercises' # The API endpoint for fetching exercises

        
    def get_exercises_by_name(self, exercise_name):
        """
        Fetch exercise data by name directly from the API.
        parameter is the exercise name that api searches for
        returns a dictionary containing the exercise data if found, otherwise None.
        """
        params = {'name': exercise_name}  # Add the exercise name as a query parameter
        
        try:
            # Send a GET request to the API with the name parameter
            response = requests.get(self.base_url, headers={'X-Api-Key': self.api_key}, params=params)
            response.raise_for_status()  # Raise an error for any unsuccessful HTTP responses
            
            exercises = response.json()  # Parse the JSON response
            
            if exercises:  # Check if the API returned any exercises
                return exercises[0]  # Return the first matching exercise (assuming exact match)
            else:
                print(f"No exercise found with the name: {exercise_name}")
                return None
        
        except requests.exceptions.RequestException as e:
            # Handle request errors gracefully
            print(f"Error fetching exercise by name: {e}")
            return None
