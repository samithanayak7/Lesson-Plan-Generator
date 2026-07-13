def split_into_topics(text):
    """
    Splits the syllabus into Topic -> Subtopics.
    Assumes every odd line is a topic
    and every even line contains its subtopics.
    """

    lines = [line.strip() for line in text.split("\n") if line.strip()]

    topics = {}

    i = 0

    while i < len(lines) - 1:

        topic = lines[i]

        subtopics = lines[i + 1]

        topics[topic] = subtopics

        i += 2

    return topics