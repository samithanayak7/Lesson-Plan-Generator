# json_writer.py

import json

def save_json(data, filename):
    """
    Saves dictionary into JSON file.
    """

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print("JSON saved successfully.")