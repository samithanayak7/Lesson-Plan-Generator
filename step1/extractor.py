def extract_topics(subtopic_line):

    subtopics = [x.strip() for x in subtopic_line.split(",")]

    subtopics = [x for x in subtopics if x]

    return subtopics