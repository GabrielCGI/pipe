import sys
import os


# --- Add path to your custom script ---
meshai_path = r"R:\pipeline\pipe\ai\meshai"
sys.path.append(meshai_path)

# --- Import and run your module ---
import meshai
meshai.run()