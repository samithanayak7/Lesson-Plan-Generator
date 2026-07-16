import json
from step2.enrich import enrich_data
from step1.preprocess import clean_text
from step1.parser import split_into_topics
from step1.extractor import extract_topics
from step1.json_writer import save_json


def generate_skeleton_json(syllabus_text: str) -> dict:
    """
    Runs Step 1 only (clean -> split -> extract) on raw syllabus text and
    returns the skeleton dict in memory (no file I/O). Fields like
    'lecture_hours' / 'difficulty' are still null at this point -- this is
    the shape json_filler.py's process_syllabus() expects as input.
    """
    cleaned = clean_text(syllabus_text)
    topics = split_into_topics(cleaned)

    final_output = {}
    for topic, subtopics in topics.items():
        final_output[topic] = {
            "Subtopics": extract_topics(subtopics)
        }

    return final_output


def generate_enriched_json(syllabus_text: str) -> dict:
    """
    Runs the full pipeline (clean -> split -> extract -> enrich) on raw
    syllabus text and returns the enriched dict in memory (no file I/O).
    """
    final_output = generate_skeleton_json(syllabus_text)
    enriched = enrich_data(final_output)
    return enriched


def main():
    """
    Standalone script behavior: reads syllabus.txt, runs the pipeline,
    and writes syllabus.json / enriched.json to disk, same as before.
    """
    with open("syllabus.txt", "r", encoding="utf-8") as file:
        syllabus = file.read()

    cleaned = clean_text(syllabus)
    topics = split_into_topics(cleaned)

    final_output = {}
    for topic, subtopics in topics.items():
        final_output[topic] = {
            "Subtopics": extract_topics(subtopics)
        }

    save_json(final_output, "syllabus.json")

    print("\nDone!\n")
    print(final_output)

    with open("syllabus.json", "r", encoding="utf-8") as file:
        syllabus_json = json.load(file)

    enriched = enrich_data(syllabus_json)

    with open("enriched.json", "w", encoding="utf-8") as file:
        json.dump(enriched, file, indent=4)

    print("Step 2 completed successfully!")


if __name__ == "__main__":
    main()
