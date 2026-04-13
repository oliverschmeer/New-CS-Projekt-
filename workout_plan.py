import streamlit as st
from api import API_Client
from datahandler import Data_Handler
from sklearn.neighbors import KNeighborsClassifier
from exercise_statistics import Statistics

class Workout_Plan:

    def __init__(self):
        self.preferences = {
            # here dictionary of preferences of the user is initialized
            "time_for_exercise" : None, 
            "exercise_days" : None, 
            "user_age": None,
            "user_weight" : None, 
            "user_experience" : None,
            "user_height" : None,
            "user_gender" : None
        } 
        
        self.client = API_Client() # create instance of the api search class
        self.dh = Data_Handler() # create instance of the Data handler class

        self.dh.load_prepare_data() # load all the csv files and prepare the data for ml
        self.train_knn_model()

        # initialize a dictionary used for storing the ratings for each exercise and values set to true at default
        # key is the exercise name and value is a boolean
        # True signifies that user likes exercise and it can be shown again
        # no exercises are rated as Bad by the user yet so they should be good by default
        # so that they can still be suggested to the user
        # added normalization to the name so that any discrepencies between api data and dataset
        if 'exercise_ratings' not in st.session_state:
            st.session_state.exercise_ratings = {name.strip().lower(): True for name in self.dh.exercise_mapping.values()}
        self.exercise_ratings = st.session_state.exercise_ratings
        
    
        self.week_plan = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": [],
        }

    def update_preferences(self, new_preference):
        '''
        Update user preferences for workout plans
        is called when input button for new preferences of user is pressed
        '''
        
        self.preferences.update(new_preference) # python function to update dictionaries with new values


    def calculate_needed_exercises(self):
        '''
        takes the time input from the user and looks at existing exercises 
        to find out how many exercises still have to be found
        '''
        minutes_per_exercise = 30 # have a standard time for each exercise to simplify distribution of exercises in week
        if self.preferences["time_for_exercise"] != 0.0: # to avoid the possibility of division by zero

            exercises_needed = (self.preferences["time_for_exercise"] * 60) / minutes_per_exercise
        
        else:
            exercises_needed = 0

        return int(exercises_needed)
    

    def manage_api_search(self):
        '''
        Fetch, enrich, and return the exact number of exercises required.
        Ensures exercises are enriched with API data.
        '''
        # Step 1: Get recommended exercises based on user preferences
        user_features = {
            "Age": self.preferences["user_age"],
            "Height (cm)": self.preferences["user_height"],  # Placeholder, could be added to preferences
            "Weight (kg)": self.preferences["user_weight"],
            "Fitness Level": self.preferences["user_experience"],
            "Gender": self.preferences["user_gender"]  
        }

        exercises_needed = self.calculate_needed_exercises()


        # Fetch the top exercises from Data_Handler with machine learning
        top_exercises = self.dh.get_top_exercises_for_user(user_features,st.session_state.exercise_ratings, number_top_exercises=exercises_needed)


        # Initialize an empty list for the enriched exercises
        enriched_exercises = []

        # Step 2: Fetch exercise details from the API
        for exercise_name in top_exercises:
            if len(enriched_exercises) >= exercises_needed:
                break  # Stop once we have enough exercises

            exercise_details = self.client.get_exercises_by_name(exercise_name)
            if exercise_details and exercise_details not in enriched_exercises:
                enriched_exercises.append(exercise_details)

        # returns the exercises with additional information 
        # trained muscle_group, type of exercise, needed equipment, instructions
        return enriched_exercises 


    def create_workout_plan(self):
        '''
        Distributes exercises across the selected days based on user preferences.
        Ensures all days of the week are shown, even if no exercises are planned on a specific day.
        '''

        # Step 1: Fetch enriched exercises from the API
        enriched_exercises = self.manage_api_search()
        if not enriched_exercises:
            print("No exercises available to create a workout plan.")
            return

        # Step 2: Initialize the workout plan with all days of the week
        self.week_plan = {day: [] for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}

        # Step 3: Get the days the user wants to train
        days_to_train = self.preferences.get('exercise_days', [])
        total_days = len(days_to_train)

        if total_days == 0:
            print("No training days specified. All days will remain empty.")
            return self.week_plan

        # Step 4: Distribute exercises across selected days
        exercises_needed = self.calculate_needed_exercises()
        exercises_per_day = exercises_needed // total_days
        remainder_exercises = exercises_needed % total_days
        exercises_index = 0

        for day in days_to_train:
            # Assign exercises to the current day
            for _ in range(exercises_per_day):
                if exercises_index < len(enriched_exercises):
                    self.week_plan[day].append(enriched_exercises[exercises_index])
                    exercises_index += 1

            # Assign remainder exercises
            if remainder_exercises > 0 and exercises_index < len(enriched_exercises):
                self.week_plan[day].append(enriched_exercises[exercises_index])
                exercises_index += 1
                remainder_exercises -= 1

        # Count number of exercises for Statistics
        total_exercises = sum(len(exercises) for exercises in self.week_plan.values())

        stats = Statistics()
        stats.save_workout_stats(total_exercises)

        # for debugging and testing
        # print("Workout plan created successfully!")
        return self.week_plan


    def train_knn_model(self):
        '''
        Trains the KNN model using the Data_Handler instance.
        '''
        
        X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test = self.dh.train_model()
        best_k = self.dh.tune_hyperparameters(X_train_scaled, y_train, X_val_scaled, y_val)
        self.dh.knn = KNeighborsClassifier(n_neighbors=best_k, weights="distance")
        self.dh.knn.fit(X_train_scaled, y_train)

    def get_exercise_recommendations(self, user_features):
        '''
        Get exercise recommendations for a user based on the trained KNN model.
        '''
        return self.dh.predict_all_exercises(user_features)
    
    def search_exercises(self, muscle_group, exercise_type, difficulty):
        '''
        Searches exercises csv uploaded in the data handler based on the given filters.
        Returns pd.DataFrame: Filtered exercises matching the criteria.
        used for the the search function 
        '''
        # Load exercise data
        exercises = self.dh.exercises  # Assuming this contains the exercise data loaded in Data_Handler

        # Apply filters to the data frame with the exercises, uploaded in data handler class
        filtered = exercises[
            (exercises['Muscle Group'] == muscle_group) &
            (exercises['Type'] == exercise_type) &
            (exercises['Difficulty'] == difficulty)
        ]

        # returns the exercises that correspond to the filters in the search function
        return filtered

       