# preprocess.py

import re

def clean_text(text):
    """
    Cleans the syllabus text by:
    - Removing extra spaces
    - Removing tabs
    - Removing multiple blank lines
    - Removing unwanted bullets
    """

    # Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove bullets if present
    text = text.replace("•", "")
    text = text.replace("-", "")

    # Remove extra spaces
    text = re.sub(r' +', ' ', text)

    # Remove multiple blank lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    return text.strip()