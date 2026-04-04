import os
import re
from pathlib import Path
import json


def find_blueprints(log_directory):
    # Standard location is usually C:\Program Files\Roberts Space Industries\Star Citizen\LIVE\logs
    log_path = Path(log_directory)
    
    if not log_path.exists():
        print(f"Error: The directory {log_directory} does not exist.")
        return

    # Regex to capture the name between "Blueprint: " and the "[" 
    # Adjusting for the specific format: "Received Blueprint: Name: [Number] to queue"
    blueprint_pattern = re.compile(r"Received Blueprint:\s*(.*):\s*.*to queue.*")
    name_pattern = re.compile(r".*User Login Success - Handle\[(.*)\] - Time.*")
    found_blueprints = set()
    user_name = "unknown"
    print(f"Searching logs in: {log_path}...")

    # Iterate through all .log files in the directory
    for log_file in log_path.rglob("Game*.log"):
        try:
            print(f"Processing log file: {log_file.name}")
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    match = blueprint_pattern.search(line)
                    namematch = name_pattern.search(line)
                    if namematch:
                        user_name = namematch.group(1).strip()
                    if match:
                        # Extract the blueprint name from the first capturing group
                        blueprint_name = match.group(1).strip()
                        found_blueprints.add(blueprint_name)
        except Exception as e:
            print(f"Could not read {log_file.name}: {e}")

    # Display results
    # print the username of the player who received the blueprint
    print(f"\nPlayer: {user_name}")
    if found_blueprints:
        print(f"\nSuccess! Found {len(found_blueprints)} unique blueprints:")
        output_data = {
            "player": user_name,
            "blueprints": sorted(list(found_blueprints))
        }
    else:
        print("\nNo blueprints found in the current log files.")

    print(output_data)
if __name__ == "__main__":
    # Update this path to your Star Citizen log folder
    # Note: Use forward slashes or double backslashes for Windows paths
    SC_LOG_DIR = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"
    
    find_blueprints(SC_LOG_DIR)



