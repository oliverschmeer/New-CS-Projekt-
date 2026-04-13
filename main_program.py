import streamlit as st
from fa_gui import Graphical_User_Interface as fgui



def main_loop():
    # Configure page layout
    st.set_page_config(page_title="Weekly Fitness Calendar", layout="wide", initial_sidebar_state="collapsed")

    # show_week_plan()
    gui = fgui()
    gui.show_interface()
    


if __name__=='__main__':
    main_loop()
