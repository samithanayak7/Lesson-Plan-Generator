# step2/enrich.py

def enrich_data(data):
    """
    Takes the extracted syllabus dictionary and
    adds placeholder fields for each subtopic.

    Parameters:
        data (dict): Dictionary generated in Step 1.

    Returns:
        dict: Enriched syllabus dictionary.
    """

    enriched = {}

    # Loop through each main topic
    for topic, details in data.items():

        enriched_subtopics = []

        # Loop through every subtopic
        for subtopic in details["Subtopics"]:

            enriched_subtopics.append({

                "name": subtopic,

                "difficulty": None,

                "lecture_hours": None,

                "learning_objective": None,

                "prerequisites": [],

                "keywords": [],

                "teaching_method": None,

                "assessment_type": None

            })

        enriched[topic] = {
            "Subtopics": enriched_subtopics
        }

    return enriched