import streamlit as st
from workout_plan import Workout_Plan
from PIL import Image
import matplotlib.pyplot as plt
from exercise_statistics import Statistics
import pandas as pd


class Graphical_User_Interface:

    def __init__(self):

        # Initialize session state variables 
        if 'training_duration' not in st.session_state:
            st.session_state.training_duration = 0
        if 'training_days' not in st.session_state:
            st.session_state.training_days = []
        if 'age_of_user' not in st.session_state:
            st.session_state.age_of_user = 0
        if 'weight_of_user' not in st.session_state:
            st.session_state.weight_of_user = 0
        if 'experience_of_user' not in st.session_state:
            st.session_state.experience_of_user = 0
        if 'height_of_user' not in st.session_state:
            st.session_state.height_of_user = 0
        if 'gender_of_user' not in st.session_state:
            st.session_state.gender_of_user = 0
        if 'current_view' not in st.session_state: # to manage which screen is shown
            st.session_state.current_view = "start"  # Default view is start
        

        if 'show_plan' not in st.session_state:
            st.session_state.show_plan = False  # By default, don't show the plan
        
        # Persist workout_plan in session state
        if 'workout_plan' not in st.session_state:
            st.session_state.workout_plan = Workout_Plan()

        # Assign the persisted workout_plan to the local reference
        self.workout_plan = st.session_state.workout_plan

        self.logo = Image.open(r"logo.png")

    def show_interface(self):
        '''
        function to display the correct view based on current_view in session state
        '''
        # Only show the sidebar navigation if not in the Start view
        # in the start view the sidebar shouldnt be shown
        if st.session_state.current_view != "start":
            st.sidebar.title("Navigation")
            st.session_state.current_view = st.sidebar.radio(
                "Choose a section:",
                options=["Workout Plan", "Statistics", "Search Exercises"]
            )

        # Render the appropriate view
        # view is decided by the current_view session state variable that is changed when specific buttons are pressed
        # or when user uses navigation to switch view
        if st.session_state.current_view == "start":
            self.show_start_view()
        elif st.session_state.current_view == "Workout Plan":
            self.show_workout_plan()
        elif st.session_state.current_view == "Statistics":
            self.show_statistics()
        elif st.session_state.current_view == "Search Exercises":
            self.show_search()


    def show_start_view(self):
        '''
        function that shows the screen that is shown when starting the app
        includes a short description of the app, the logo and user inputs
        '''
        col1, col2 = st.columns([3,1]) # create two columns with one being three times bigger then the other
        
        with col1:
            # the description of the Appp
            st.header("🏋️‍♂️Fitness4You – Welcome to Your Fintess Journey", divider="red")
            st.subheader(f"Have you wanted to start working out but weren’t sure which exercises to try?")
            st.subheader(f"Or are you tired of repeating the same exercises every week and unsure what else to do?") 
            st.subheader(f"No matter your experience level, our Fitness4You app creates personalized workout plans " 
                         f"tailored to your preferences — so you can stay motivated and never feel stuck in your fitness journey!")
            
            # Add multiple blank lines
            for _ in range(2):  # Adds 2 blank lines
                st.write("")

            st.write(f"✏️ To generate a personalized workout plan, you need to"
                     f"input following data")
            
            # generate 3 columns for the three sliders
            colum1, colum2, colum3 = st.columns(3)
            
            ### get the information of the user, which is used for machine learning to predict 
            ### exercises that fit to the user

            with colum1:
                # input slider for the age of the user
                age_of_user = st.slider("Age (years)", min_value=18, max_value=100, value=30, step=1)
                st.session_state.age_of_user = age_of_user  # Update session state directly
            
            with colum2:
                # input slider for the weight of the user 
                weight_of_user = st.slider("Weight (kg)", min_value=40, max_value=200, value=70, step=2)
                st.session_state.weight_of_user = weight_of_user  # Update session state directly

            with colum3:
                # input slider for the height of the user
                height_of_user = st.slider("Height (cm)", min_value=120, max_value=200, value=170, step=1)
                st.session_state.height_of_user = height_of_user  # Update session state directly

            c1, c2 = st.columns(2) # create two columns for the selectboxes

            with c1:
                # Collect user input for sport level    
                experience_of_user = st.selectbox("Experience", options=["Beginner", "Intermediate", "Advanced"])
                st.session_state.experience_of_user = experience_of_user  # Update session state directly
            
            with c2:
                # collect user input for gender
                gender_of_user = st.selectbox("Gender", options=["Male", "Female"])
                st.session_state.gender_of_user = gender_of_user  # Update session state directly

        with col2:
            # show the logo of the APP
            st.image(
                self.logo,
                use_column_width=True
            )

            # Button to start the App
            if st.button("Start Now", key="start_button", help="Double Click", use_container_width=True):

                # gets the user inout when it is submitted
                preferences = {
                    "user_age": st.session_state.get('age_of_user'),
                    "user_weight": st.session_state.get('weight_of_user'),
                    "user_experience": st.session_state.get('experience_of_user'),
                    "user_height": st.session_state.get('height_of_user'),
                    "user_gender": st.session_state.get('gender_of_user'),
                    }

                # passes the user input to the workout plan class which then uses it for the ml model
                self.workout_plan.update_preferences(preferences)

                # switch to the calender view of the app
                st.session_state.current_view = "Calendar"

    def show_workout_plan(self):
        '''
        Function to display the workout plan in the calendar view.
        '''
        st.header("📆 Your Personalized Workout Plan", divider="red")
        self.show_user_input()  # Displays input boxes for user preferences

        if st.button("Confirm Selections"):
            self.input_selection_button()

            # updates the amount of times the exercises in the week plan were called to have an accurate number for retrievals
            stats = Statistics()
            for day, exercises in self.workout_plan.week_plan.items():
                for exercise in exercises:
                    stats.update_retrievals(exercise["name"])

            stats.save_to_csv() # then save these changes to the csv

        self.show_calender()  # Displays the calendar view


    def input_selection_button(self):
        
        # initialize a new week plan when the "confirm selection button" is pressed
        # before distributing exercises the week plan is created as an empty dictionary with only keys and then empty lists
        self.workout_plan.week_plan = {day: [] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}

        # function is called that distributes exercises to appropriate days based on user input
        self.workout_plan.create_workout_plan()
        st.session_state.show_plan = True  # Set show_plan to True so that workout plan is shown to user

        st.session_state.workout_plan = self.workout_plan  # Store the plan in session state

    
    def show_calender(self): 
        '''
        to show the workout plan on streamlit
        '''


        if st.session_state.get('show_plan'):  # Only show the workout plan if show_plan is True

            st.write("☑️ Please add ratings to exercises after completing them!")
            # Add multiple blank lines
            for _ in range(5):  # Adds 5 blank lines
                st.write("")

            # Create columns for each day of the week
            columns = st.columns(7)  # Creates seven equal-width columns

            self.workout_plan.week_plan = st.session_state.workout_plan.week_plan
            
            # Loop through the days of the week by index
            days = list(self.workout_plan.week_plan.keys())  # Extract the days into a list
            for i in range(len(days)):
                day = days[i]  # Get the day name (e.g., "Monday")
                col = columns[i]  # Access the corresponding column using the index

                with col:
                    col.subheader(day)  # Display the day name

                    # Get exercises for the day
                    exercises = self.workout_plan.week_plan[day]
                    if exercises:
                        # Loop through each exercise for the day and whow information about this exercise
                        for exercise in exercises:
                            with col.expander(exercise["name"], expanded=False):
                                st.write(f"**Type:** {exercise['type']}")
                                st.write(f"**Muscle Group:** {exercise['muscle']}")
                                st.write(f"**Equipment:** {exercise['equipment']}")
                                st.write(f"**Difficulty:** {exercise['difficulty']}")

                                # Add rating slider
                                rating = st.radio(
                                    "Rate this exercise:",
                                    options=["Good 👍", "Bad 👎"],
                                    key=f"{day}_{exercise['name']}_rating"
                                )

                                # Convert "Good" to True and "Bad" to False, and store in the dictionary in the workout plan class
                                # passed to the session state variable
                                # add normalized names so that any discrepencies between the api search and our dataset is delt with
                                normalized_name = exercise['name'].strip().lower()
                                st.session_state.exercise_ratings[normalized_name] = (rating == "Good 👍")


                                # Use st.toggle for instructions
                                toggle_state = st.toggle("Show Instructions", key=f"{day}_{exercise['name']}_toggle")
                                if toggle_state:
                                    st.write(f"**Instructions:** {exercise['instructions']}")

                    else:
                        # Placeholder if no exercises are planned
                        col.write("No exercises planned.")
        
        else:
            st.info("Select your inputs and press the 'Confirm Selections' button.")

    def show_user_input(self):
        '''
        to show the Input boxes for the user
        '''

        # Input form above the calendar
        st.header("Exercise Selection")
        col1, col2 = st.columns(2)

        # Collect user input for training duration
        with col1:
            training_duration = st.slider("Training Duration (hours per week)", min_value=0.0, max_value=20.0, value=5.0, step=0.5)
            st.session_state.training_duration = training_duration  # Update session state directly
        
        
        # Collect user input for training days
        with col2:    
            training_days = st.multiselect("Training days", options=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=["Monday", "Wednesday", "Friday"])
            st.session_state.training_days = training_days  # Update session state directly

        # Add confirmation button to save the preferences
        # if st.button("Confirm Selections"):
        preferences = {
            "time_for_exercise": st.session_state.get('training_duration'),
            "exercise_days": st.session_state.get('training_days')
            }
        
        self.workout_plan.update_preferences(preferences)
    

    def show_statistics(self):
        '''sidebar opens window that shows statistics'''
        st.header("📉 Statistics", divider="red")

        stats = Statistics()

        ### Bar Chart ###
        st.subheader("Most Retrieved Exercises")
        st.write("Here are the all-time most retrieved exercises:")
        top_exercises = stats.get_statistics() # gets the information from the statistic class about the top exercises

        if top_exercises.empty:
            st.warning("No data available for statistics.")
        else:
            # Dynamic background color and font color
            # so that statistics are shown dependend on background and font
            # this adaption coded with CHATGPT
            theme = st.get_option("theme.base")
            if theme == "dark":
                background_color = "#0E1117"  # Streamlit dark mode background
                text_color = "white"
                bar_color = "#66b3ff"  # Adjust for better contrast
            else:
                background_color = "white"
                text_color = "black"
                bar_color = "#1f77b4"


            # Plotting the Bar Chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(top_exercises["Exercise Name"], top_exercises["Retrievals"], color=bar_color)
            #ax.set_title("Most Retrieved Exercises", fontsize=16, color=text_color)

            #  labeling the axis of the chart
            ax.set_xlabel("Exercise", fontsize=12, color=text_color)
            ax.set_ylabel("Retrieval Count", fontsize=12, color=text_color)
            ax.set_xticklabels(top_exercises["Exercise Name"], rotation=45, ha="right", fontsize=10, color=text_color)

            fig.patch.set_facecolor(background_color)  # Set the outer figure background
            ax.set_facecolor(background_color)  

            # Layout
            plt.tight_layout()
            st.pyplot(fig)

        # Adding space between Graphics
        st.write("")
        st.write("")

        ### Pie Chart ###
        st.subheader("Muscle Group Distribution")
        st.write("For current Workout")
        week_plan = self.workout_plan.week_plan
        if not any(week_plan.values()):
            st.warning("Statistic not available. Generate a workout plan first.")
        else:
        
            # calls function to calculate muscle distribution
            muscle_distribution = stats.get_muscle_distribution(week_plan)

            # called if muscle distribution not empty
            if muscle_distribution:
                labels = list(muscle_distribution.keys()) # keys are saved
                sizes = list(muscle_distribution.values()) #  values of dict are saved


        # Creating the pie chart
            fig, ax = plt.subplots(figsize=(8, 6))
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct='%1.1f%%', startangle=90, textprops=dict(color=text_color)
            )

            # Equal aspect ratio ensures the pie chart is circular.
            ax.axis('equal')

            # Adjust text
            for text in texts:
                text.set_color(text_color)

            # Plotting the chart
            st.pyplot(fig)

        # Adding space between graphics
        st.write("")
        st.write("")

        ### Line Chart ###
        st.subheader("Workout History")
        st.write("Number of Exercises for the last 10 weekly Workout Plans")

        #  calls function that loads the data from the csv that shows the exercises per week
        workout_data = stats.load_workout_stats() 

        if not workout_data.empty:
            #  only show the last 10 week so workout data shortend
            workout_data = workout_data.tail(10)

            # plot the line chart
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(workout_data["Week"], workout_data["Number of Exercises"], marker="o")
            ax.set_xlabel("Week")
            ax.set_ylabel("Number of Exercises")
            #ax.set_title("Number of Exercises Per Workout")
            plt.xticks(workout_data["Week"])
            st.pyplot(fig)
        else:
            st.info("No workout history available.")
        

    def show_search(self):
        '''
        Function to search exercises based on muscle group, type, and difficulty
        '''

        # Input form for search parameters
        st.header("🔭 Search Exercises", divider="red")
        col1, col2, col3 = st.columns(3) # create columns to show inputs next to each other

        # creates the three selectboces for the inputs in the corresponding columns
        with col1:
            selected_muscle_group = st.selectbox("Select Muscle Group", 
                                                options=self.workout_plan.dh.exercises['Muscle Group'].unique())
        with col2:
            selected_type = st.selectbox("Select Exercise Type", 
                                        options=self.workout_plan.dh.exercises['Type'].unique())
        with col3:
            selected_difficulty = st.selectbox("Select Difficulty", 
                                            options=self.workout_plan.dh.exercises['Difficulty'].unique())

        # Search button
        if st.button("Search"): # searches the exercises if button is pressed
            # Filter exercises based on user input
            filtered_exercises = self.workout_plan.search_exercises(
                # passed filters to the search exercise function in workout plan class
                muscle_group=selected_muscle_group,
                exercise_type=selected_type,
                difficulty=selected_difficulty
            )

            # Display results from the search
            # should display every exercise that fits the search filters
            if not filtered_exercises.empty:
                st.subheader("Search Results")
                for idx, row in filtered_exercises.iterrows(): # lopping through all the exercises and then display the information for this exercise
                    with st.expander(row['Exercise Name'], expanded=False):
                        st.write(f"**Type:** {row['Type']}")
                        st.write(f"**Muscle Group:** {row['Muscle Group']}")
                        st.write(f"**Difficulty:** {row['Difficulty']}")
                        
            else:
                # shows a warning if for given filters no exercises existed in the data set
                st.warning("No exercises found matching your criteria.")
#hello
#hello2
