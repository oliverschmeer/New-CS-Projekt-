import pandas as pd
from collections import Counter # class found and then explained to us by  ChatGpt

class Statistics:
    """
    Provides and prepares all the data for the 'show_statistics' method in the GUI class.
    """

    def __init__(self, csv_file_path="exercise_data.csv", workout_stats_file="workout_statistics.csv"):
        """
        Initializing the Statistics class for the page "Statistics" in our application.
        """
        self.csv_file_path = csv_file_path
        self.exercises = pd.read_csv(csv_file_path)

        # to ensure that the column Retrievals exists in the exercise csv
        # Retrievals saves the amount of times the exercise has already been called                         
        if "Retrievals" not in self.exercises.columns: 
            self.exercises["Retrievals"] = 0

        # Normalizing the Exercise Name to avoid any mismatching
        self.exercises["Exercise Name"] = self.exercises["Exercise Name"].str.strip().str.lower()
        
        # file to save the amount of exercises per week
        self.workout_stats_file = workout_stats_file

        # Reading workout_stats_file
        try:
            self.workout_stats = pd.read_csv(workout_stats_file)
        except FileNotFoundError: #  creates a dataframe if file doesn´t exist and then saves it to csv
            self.workout_stats = pd.DataFrame(columns=["Week", "Number of Exercises"])
            self.workout_stats.to_csv(workout_stats_file, index=False)

    ### Bar Chart ###
    # following are methods that are necessary for the bar chart
    def update_retrievals(self, exercise_name):
        """
        Updates the Retrievals for each exercise in the CSV file "exercise_data.csv"
        Here data for the bar chart is saved
        """
        # Normalizing the exercise_name
        normalized_name = exercise_name.strip().lower()

        # Return if no exercise with said name is found
        # to make sure that exercise exists before exercising next part of code
        if normalized_name not in self.exercises["Exercise Name"].values:
            print(f"Exercise '{exercise_name}' not found in the data set.")
            return
        
        # Retrievals counter raised +1 for every exercise called in the week plan
        # through normalizing it is ensured that right exercise is called
        self.exercises.loc[self.exercises["Exercise Name"] == normalized_name, "Retrievals"] += 1
        
    def save_to_csv(self):
        """
        Saves changes to the CSV file "exercise_data.csv"
        """
        self.exercises.to_csv(self.csv_file_path, index=False)



    def get_statistics(self, top_n=10):
        """
        Get the top 10 most retrieved exercises for the bar chart.
        Any other number could be inputed as a parameter but 10 is default and used in our code
        """
        return self.exercises.sort_values(by="Retrievals", ascending=False).head(top_n)
    
    ### Pie Chart ###
    # following are the methods that are necessary for the Pie chart
    def get_muscle_distribution(self, week_plan):
        """
        Calculate percentage of distribution of muscles targeted in the weekly plan.
        """
        #  initializing an instance of the Counter class imported from collections
        muscle_counts = Counter()

        # Iterating through the week plan to add +1 to the counter of each muscle group
        for day, exercises in week_plan.items():
            for exercise in exercises:
                muscle = exercise.get("muscle", "Unknown")
                muscle_counts[muscle] += 1

        # Calculating percentages for muscle group distribution
        # simple percentate calculation for each muscle group
        total_exercises = sum(muscle_counts.values())
        muscle_distribution = {muscle: (count / total_exercises) * 100 for muscle, count in muscle_counts.items()}

        return muscle_distribution

    ### Line Chart ###
    # following the methods necessary for the line chart
    def save_workout_stats(self, number_of_exercises):
        """
        Saving the number of exercises for the generated workout.
        """
        # New entry for a weekly plan added in the CSV
        #  either starts at one if empty or takes highest week number in csv and then this week plus one
        if self.workout_stats.empty:
            next_week = 1
        else:
            next_week = self.workout_stats["Week"].max() + 1

        # creates new week to save number of exercises for this week
        new_entry = {"Week": next_week, "Number of Exercises": number_of_exercises}

        # save this data to the csv again
        #  helf by Chatgpt to find right method to do that
        self.workout_stats = pd.concat([self.workout_stats, pd.DataFrame([new_entry])], ignore_index=True)
        self.workout_stats.to_csv(self.workout_stats_file, index=False)


    def load_workout_stats(self):
        """
        Load workout statistics from the CSV file "workout_statistics.csv"
        """
        return pd.read_csv(self.workout_stats_file)