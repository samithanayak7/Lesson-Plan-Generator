import json
from step2.enrich import enrich_data 
from step1.preprocess import clean_text
from step1.parser import split_into_topics
from step1.extractor import extract_topics
from step1.json_writer import save_json


# Read syllabus
with open("syllabus.txt", "r", encoding="utf-8") as file:
    syllabus = file.read()

# Step 1.2
cleaned = clean_text(syllabus)

# Step 1.3
topics = split_into_topics(cleaned)

# Step 1.4 & 1.5
final_output = {}

for topic, subtopics in topics.items():

    final_output[topic] = {
        "Subtopics": extract_topics(subtopics)
    }

# Step 1.6
save_json(final_output, "syllabus.json")

print("\nDone!\n")

print(final_output)

# Read the JSON created in Step 1
with open("syllabus.json", "r", encoding="utf-8") as file:
    syllabus = json.load(file)

# Enrich the syllabus
enriched = enrich_data(syllabus)

# Save the enriched JSON
with open("enriched.json", "w", encoding="utf-8") as file:
    json.dump(enriched, file, indent=4)

print("Step 2 completed successfully!")