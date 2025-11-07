import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    
    # Set the path to the app using forward slashes
    app_path = "src/wheel_simulator/ui/app.py"
    sys.argv = ["streamlit", "run", app_path]
    sys.exit(stcli.main())
