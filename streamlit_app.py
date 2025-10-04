# Streamlit Cloud entry point
# This file is used for Streamlit Cloud deployment
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from app import main

if __name__ == "__main__":
    main()
