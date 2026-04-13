import pandas as pd
import numpy as np

'''
found GroupShuffleSplit with chatgpt -> used instead of train_test_split
because exercises need to stay grouped together and distributed equally
to train, validation, test
ChatGPT also helped in implementing GroupSHuffleSplit to prepare ML data
'''
from sklearn.model_selection import GroupShuffleSplit 

from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import LabelEncoder

# Used for scaling the data so that data has equal weight in prediction
from sklearn.preprocessing import StandardScaler

from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
import matplotlib.pyplot as plt

class Data_Handler:

    def __init__(self):
        # Initialize the three variables to save the path to the csv files
        self.exercise_path = r'exercise_data.csv'
        self.users_path = r'users_data.csv'
        self.ratings_path = r'exercise_ratings_data.csv'

        # Placeholder for the final cleaned data
        self.final_cleaned_data = None

        # Placeholder for the KNN model
        self.knn = None

        # Placeholder for the dummy that is used for evaluating the ml model
        self.dummy = None

        # Placeholder for the scaler that scales the data 
        self.scaler = None

        # implement instances of imported LabelEncoder class to transform data into numerical data
        self.fitness_level_encoder = LabelEncoder()
        self.gender_encoder = LabelEncoder()

        # initializing dictionary used for mapping Exercise ID to Exercise Name
        # so that code can pass exercise name to api, and api can find data to these exercises
        self.exercise_mapping = {}

    
    def load_prepare_data(self):
        # load datasets
        self.exercises = pd.read_csv(self.exercise_path)
        self.users = pd.read_csv(self.users_path)
        self.ratings = pd.read_csv(self.ratings_path)

        # Create Exercise ID to Name mapping
        self.exercise_mapping = dict(zip(self.exercises['Exercise ID'], self.exercises['Exercise Name']))

        # Merge datasets
        merged_data = self.ratings.merge(self.exercises, on='Exercise ID', how='inner')
        self.final_merged_data = merged_data.merge(self.users, on='User ID', how='inner')

        # Drop unnecessary columns -> could also be left out but made debugging with print easier
        self.final_cleaned_data = self.final_merged_data.drop(columns=['Type', 'Difficulty', 'Muscle Group'])

        # Encode categorical features 
        # since in original data set gender and fitness level is not numerical data and knn needs numerical data
        self.final_cleaned_data['Fitness Level Encoded'] = self.fitness_level_encoder.fit_transform(
            self.final_cleaned_data['Fitness Level'])
        self.final_cleaned_data['Gender Encoded'] = self.gender_encoder.fit_transform(
            self.final_cleaned_data['Gender'])
        
    def train_model(self):
        '''
        Split the data into training, validation, and testing sets,
        ensuring a balanced distribution of Exercise IDs across the splits.
        To do that, we used the GroupShuffleSplit from sklearn instead of train_test_split
        '''
        # Define features and labels
        X = self.final_cleaned_data[['Exercise ID', 'Age', 'Height (cm)', 'Weight (kg)',
                                     'Fitness Level Encoded', 'Gender Encoded']]
        y = self.final_cleaned_data['Rating']
        groups = self.final_cleaned_data['Exercise ID']  # Use Exercise ID for grouping the exercises


        # Step 1: Split into 80% training and 20% validation and testing
        # 20% validation and testing split again later to ensure a 80, 10, 10 % split
        # ChatGPT helped in implementing data preparation with GroupShuffleSplit
        gss = GroupShuffleSplit(n_splits=1, train_size=0.8, random_state=42)
        train_idx, temp_idx = next(gss.split(X, y, groups=groups))

        X_train, X_temp = X.iloc[train_idx], X.iloc[temp_idx]
        y_train, y_temp = y.iloc[train_idx], y.iloc[temp_idx]
        temp_groups = groups.iloc[temp_idx]

        # Step 2: Split temporary set into 10% validation and 10% testing
        gss_temp = GroupShuffleSplit(n_splits=1, train_size=0.5, random_state=42)
        val_idx, test_idx = next(gss_temp.split(X_temp, y_temp, groups=temp_groups))

        X_val, X_test = X_temp.iloc[val_idx], X_temp.iloc[test_idx]
        y_val, y_test = y_temp.iloc[val_idx], y_temp.iloc[test_idx]

        # Apply StandardScaler to the features
        # so that each data point is weighted equally
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)  # Fit and transform on training data
        X_val_scaled = self.scaler.transform(X_val)          # Transform validation data
        X_test_scaled = self.scaler.transform(X_test)        # Transform test data

        # Train Dummy Classifier with the training set
        # used for evaluation of ml model
        # use of most_frequent strategy to compare with trained model
        self.dummy = DummyClassifier(strategy="most_frequent")
        self.dummy.fit(X_train, y_train)

        # return the data, split into training, validation and testing data
        return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test

    def tune_hyperparameters(self, X_train, y_train, X_val, y_val):
        '''
        Using the validation data this function aims to find the best number 
        of neighbors for the KNN model, to achieve the most accurate results
        '''
        best_k = None
        best_accuracy = 0

        # this function was created with the help of ChatGpt
        '''
        it compares k values and its accuracy and then chooses the k value
        that had the highest accuracy when predicting the result
        '''
        for k in range(1, 21):  # Try k values from 1 to 20 with a for loop
            knn = KNeighborsClassifier(n_neighbors=k, weights='distance')
            knn.fit(X_train, y_train) # train the model

            # compare the prediction with actual data and then choose the k value with best results
            val_predictions = knn.predict(X_val) 
            val_accuracy = np.mean(val_predictions == y_val)

            if val_accuracy > best_accuracy: # check if accuracy is higher then current best value
                best_k = k
                best_accuracy = val_accuracy

        # used for debugging
        # print(f"Best k: {best_k} with Validation Accuracy: {best_accuracy:.2%}")
        return best_k


    def get_exercise_name(self, exercise_id):
        # Return the name of the exercise for the given ID
        return self.exercise_mapping.get(exercise_id, "Unknown Exercise")


    def evaluate_model(self, X_test, y_test, exercise_id):
        '''
        different methods to analyze a model implemented into one function 
        that can be called to show the accuracy of the trained model
        - since model predicts rating for each exercise, one has to determine for which
        exercise one wants to analyze the accuracy
        '''

        # Filter test data for the specific Exercise ID
        # Only consider rows in X_test and y_test corresponding to the given Exercise ID
        X_test_exercise = X_test[X_test['Exercise ID'] == exercise_id]
        y_test_exercise = y_test[X_test['Exercise ID'] == exercise_id]

        # for debugging to show the exercise name
        exercise_name = self.get_exercise_name(exercise_id)

         # Check if there is any test data for the given exercise
        if not X_test_exercise.empty:

            # Predict ratings for the exercise using the knn model
            knn_predictions = self.knn.predict(X_test_exercise)
            
            # Calculate the accuracy of the knn model for the exercise
            knn_accuracy = self.knn.score(X_test_exercise, y_test_exercise)

            # Predict ratings for the exercise using the Dummy Classifier
            dummy_predictions = self.dummy.predict(X_test_exercise)
            
            # Calculate the accuracy of the Dummy Classifier for the specific exercise
            dummy_accuracy = self.dummy.score(X_test_exercise, y_test_exercise)

            # Generate and display the confusion matrix for the knn model
            ConfusionMatrixDisplay.from_predictions(
                y_true=y_test_exercise,           # actual ratings
                y_pred=knn_predictions,           # Predicted ratings by trained knn model
                display_labels=self.knn.classes_, # Class labels for the confusion matrix
                normalize='pred'                  # Normalize by predicted values so that one can see distribution
            )
            plt.title(f"Confusion Matrix for Exercise: {exercise_name}")
            plt.show() # plot the ConfusionMatrix

            # Generate the classification report for the KNN model
            knn_classification_report = classification_report(y_test_exercise, knn_predictions)

            # Return all evaluation metrics and results in a dictionary
            return {
                'Exercise Name': exercise_name,                     # Name of the exercise
                'KNN Predictions': knn_predictions,                 # Predictions by the knn model
                'Actual Ratings': y_test_exercise.values,           # True ratings from the test set
                'KNN Accuracy': knn_accuracy,                       # Accuracy of the knn model
                'Dummy Accuracy': dummy_accuracy,                   # Accuracy of the Dummy Classifier
                'Classification Report': knn_classification_report, # Classification report for knn
            }
        else:
        # If no test data exists for the exercise
            return f"No test data available for Exercise ID {exercise_id} ({exercise_name})."
        

    def predict_rating(self, new_user):
        '''
        Predict the rating for a specific exercise for a new user based on the knn model
        used for debugging and testing since for programm we needed the rating for all exercises
        '''
        # Encode Fitness Level and Gender into numerical values since inputed as beginner, intermediate, advanced
        # has to be transformed to 0 and 1
        new_user['Fitness Level Encoded'] = self.fitness_level_encoder.transform([new_user['Fitness Level']])[0]
        new_user['Gender Encoded'] = self.gender_encoder.transform([new_user['Gender']])[0]

        # Create a DataFrame for the new user's data so that it can be passed as parameter for predict function
        new_user_df = pd.DataFrame([{
            'Exercise ID': new_user['Exercise ID'],                      # ID of the exercise
            'Age': new_user['Age'],                                      # User's age
            'Height (cm)': new_user['Height (cm)'],                      # User's height
            'Weight (kg)': new_user['Weight (kg)'],                      # User's weight
            'Fitness Level Encoded': new_user['Fitness Level Encoded'],  # Encoded fitness level
            'Gender Encoded': new_user['Gender Encoded']                 # Encoded gender
        }])

        # Predict and return the rating for the specified exercise
        return self.knn.predict(new_user_df)[0]
    
    def predict_all_exercises(self, new_user):
        '''
        Predict ratings for all exercises for a given user.
        Returns a dictionary mapping exercise names to predicted ratings
        '''
        # Encode Fitness Level and Gender into numerical values
        new_user['Fitness Level Encoded'] = self.fitness_level_encoder.transform([new_user['Fitness Level']])[0]
        new_user['Gender Encoded'] = self.gender_encoder.transform([new_user['Gender']])[0]
        
        # Step 1: Prepare DataFrame for prediction
        # Create a list of all exercise IDs
        exercise_ids = list(self.exercise_mapping.keys())

        # Construct a DataFrame where each row corresponds to an exercise and includes the user's attributes
        user_df = pd.DataFrame([{
            'Exercise ID': exercise_id,                                     # The ID of the exercise
            'Age': new_user['Age'],                                         # User's age
            'Height (cm)': new_user['Height (cm)'],                         # User's height in centimeters
            'Weight (kg)': new_user['Weight (kg)'],                         # User's weight in kilograms
            'Fitness Level Encoded': new_user['Fitness Level Encoded'],     # Encoded fitness level
            'Gender Encoded': new_user['Gender Encoded']                    # Encoded gender
        } for exercise_id in exercise_ids])

        # Step 2: Scale the user data
        # Use the scaler to transform the data for prediction
        user_df_scaled = self.scaler.transform(user_df)

        # Step 3: Predict ratings for all exercises
        # Use the trained KNN model to predict the rating for each exercise based on the users attributes
        predicted_ratings = self.knn.predict(user_df_scaled)

        # Step 3: Map predictions to exercise names
        # Create a dictionary where the keys are exercise names and the values are the predicted ratings
        predictions_dict = {
            self.get_exercise_name(exercise_id): rating
            for exercise_id, rating in zip(exercise_ids, predicted_ratings)
        }

        # Step 5: Return the dictionary of predictions
        # later used to compare all the ratings and to pich exercises with highest predicted rating for user
        return predictions_dict
    
    def get_top_exercises_for_user(self, user_data, current_exercise_ratings, number_top_exercises=10):
        '''
        Predict and rank exercises for a user, returning the top N exercise names.
        returns a list of the names of the top N exercises, ranked from best to worst.
        needs to be in a list so that api can find additional data about the exercises
        '''

        # Step 1: Predict ratings for all exercises
        # Use the predict_all_exercises_for_user method to get predicted ratings for all exercises
        # for the given user's attributes.
        all_exercise_ratings = self.predict_all_exercises(user_data)

        # Step 2: Filter out exercises not rated as Good
        # if the user hasn´t rated exercises as bad or good yet, all exercises are included
        # since default rating for exercises is good
        # added normalization to the name so that any discrepencies between api data and dataset
        good_exercises = {name: rating for name, rating in all_exercise_ratings.items()
                          if current_exercise_ratings.get(name.strip().lower(), False)}

        # Step 2: Sort exercises that are not rated as bad by predicted rating
        # Convert the dictionary of exercise names and ratings into a list of tuples
        # Sort the list in descending order of ratings (highest-rated exercises first).
        sorted_exercises = sorted(good_exercises.items(), key=lambda x: x[1], reverse=True)

        # Step 3: Extract the top N exercise names
        # Take the first `top_n` items from the sorted list and extract only the exercise names.
        top_exercises = [exercise[0] for exercise in sorted_exercises[:number_top_exercises]]

        # Step 4: Return the top N exercise names as a list
        return top_exercises