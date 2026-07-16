import json
from google.genai import types

from json_filler import client, DEFAULT_UNIT_HOURS


# ---------------------------------------------------------
# Stage A: Ask Gemini WHICH topics to group (names only).
# Gemini is good at judging semantic/thematic similarity but
# unreliable at precise arithmetic, so we never ask it to sum
# or round hours itself -- that happens in Python (Stage B).
# ---------------------------------------------------------
def get_grouping_plan(unit_name: str, subtopics: list) -> dict:
    topic_summary = [
        {"name": t["name"], "lecture_hours": t.get("lecture_hours")}
        for t in subtopics
    ]

    prompt = f"""
    You are an expert academic curriculum engineer planning lecture sessions.

    UNIT: "{unit_name}"

    Below is a list of subtopics with their estimated lecture hours (decimal).
    Your job is to decide which subtopics should be MERGED into a single
    combined lecture session, and which should remain standalone.

    RULES:
    1. Only merge subtopics that are thematically/conceptually related
       (e.g. small related C type-declaration topics like bit fields, unions,
       and enums; or related I/O redirection topics). Never merge unrelated
       topics just to hit a round number.
    2. Prefer merging when individual topics have small decimal hours
       (roughly under 1 hour) -- these are natural candidates for combining
       into one teaching session.
    3. Major standalone concepts (e.g. Pointers, Recursion, Control
       Structures, Functions) should usually remain single, even if their
       hours are decimal -- they will be rounded individually, not merged.
    4. Every subtopic name below must appear in exactly ONE place in your
       output: either inside one group, or in "singles". No duplicates, none
       omitted.
    5. Do NOT calculate or output any hour totals yourself -- only decide
       the grouping.

    Subtopics:
    {json.dumps(topic_summary, indent=2)}

    Output ONLY valid JSON (no markdown, no commentary) in this exact shape:
    {{
      "groups": [["Topic A", "Topic B"], ["Topic C", "Topic D", "Topic E"]],
      "singles": ["Topic F", "Topic G"]
    }}
    """

    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents=[prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    return json.loads(response.text)


# ---------------------------------------------------------
# Stage B: Python does the actual merging math.
# ---------------------------------------------------------
def merge_topic_group(topics: list) -> dict:
    """Combine a list of subtopic dicts into one whole-hour session."""
    total_hours = sum(float(t.get("lecture_hours", 0)) for t in topics)
    rounded_hours = max(1, round(total_hours))

    names_in_group = [t["name"] for t in topics]
    combined_keywords = sorted({k for t in topics for k in t.get("keywords", [])})
    combined_prereqs = sorted({
        p for t in topics for p in t.get("prerequisites", [])
        if p not in names_in_group
    })
    combined_objective = " ".join(
        t.get("learning_objective", "").strip()
        for t in topics if t.get("learning_objective")
    )

    # Represent the merged session using the metadata of its hardest
    # (highest-difficulty) member, since that's usually the anchor topic.
    representative = max(topics, key=lambda t: t.get("difficulty", 0))

    return {
        "name": " & ".join(names_in_group),
        "difficulty": max(t.get("difficulty", 1) for t in topics),
        "lecture_hours": rounded_hours,
        "learning_objective": combined_objective,
        "prerequisites": combined_prereqs,
        "keywords": combined_keywords,
        "teaching_method": representative.get("teaching_method"),
        "assessment_type": representative.get("assessment_type"),
        "merged_topics": names_in_group,
    }


def round_single(topic: dict) -> dict:
    """Round a standalone topic's hours to the nearest whole number (min 1)."""
    t = dict(topic)
    t["lecture_hours"] = max(1, round(float(topic.get("lecture_hours", 0))))
    return t


def reconcile_to_target(subtopics: list, target_total: float) -> list:
    """
    After independent rounding, small drift (+/- a few hours) versus the
    unit's original target total is common. Nudge the largest sessions up
    or down by 1 hour at a time until the whole-number total matches.
    """
    target_total = round(target_total)
    current_total = sum(s["lecture_hours"] for s in subtopics)
    diff = target_total - current_total

    if diff == 0 or not subtopics:
        return subtopics

    # Adjust biggest sessions first so no single topic gets distorted much.
    ordered = sorted(subtopics, key=lambda s: -s["lecture_hours"])
    i = 0
    safety = 0
    while diff != 0 and safety < 1000:
        s = ordered[i % len(ordered)]
        if diff > 0:
            s["lecture_hours"] += 1
            diff -= 1
        elif s["lecture_hours"] > 1:
            s["lecture_hours"] -= 1
            diff += 1
        i += 1
        safety += 1

    return subtopics


# ---------------------------------------------------------
# Main entry point
# ---------------------------------------------------------
def group_similar_topics(syllabus_data: dict, unit_targets: dict = None) -> dict:
    """
    Takes a completed syllabus dict (e.g. completed_syllabus.json) and
    returns a new dict where similar small-decimal topics are merged into
    whole-hour sessions, and standalone topics are individually rounded.
    Per-unit totals are reconciled back to the original target hours.
    """
    unit_targets = unit_targets or {}
    grouped_output = {}

    for unit_name, unit_data in syllabus_data.items():
        subtopics = unit_data.get("Subtopics", [])
        if not subtopics:
            grouped_output[unit_name] = unit_data
            continue

        target_total = (
            unit_targets.get(unit_name)
            or unit_data.get("lecture_hours")
            or DEFAULT_UNIT_HOURS.get(unit_name)
        )

        print(f"Planning groupings for '{unit_name}'...")
        plan = get_grouping_plan(unit_name, subtopics)

        name_to_topic = {t["name"]: t for t in subtopics}
        used_names = set()
        new_subtopics = []

        for group in plan.get("groups", []):
            group_topics = [name_to_topic[n] for n in group if n in name_to_topic]
            if len(group_topics) < 2:
                # Not actually a group (Gemini gave a singleton) -- skip here,
                # it'll be picked up by the "leftover" pass below.
                continue
            new_subtopics.append(merge_topic_group(group_topics))
            used_names.update(t["name"] for t in group_topics)

        for single_name in plan.get("singles", []):
            if single_name in name_to_topic and single_name not in used_names:
                new_subtopics.append(round_single(name_to_topic[single_name]))
                used_names.add(single_name)

        # Safety net: anything Gemini forgot to place, keep as a rounded single.
        for name, topic in name_to_topic.items():
            if name not in used_names:
                new_subtopics.append(round_single(topic))
                used_names.add(name)

        if target_total:
            new_subtopics = reconcile_to_target(new_subtopics, target_total)

        grouped_output[unit_name] = {
            "difficulty": unit_data.get("difficulty"),
            "lecture_hours": sum(s["lecture_hours"] for s in new_subtopics),
            "Subtopics": new_subtopics,
        }

    return grouped_output


def group_syllabus_file(input_path: str, output_path: str, unit_targets: dict = None):
    """File-based convenience wrapper."""
    with open(input_path, 'r') as f:
        syllabus_data = json.load(f)

    grouped = group_similar_topics(syllabus_data, unit_targets)

    with open(output_path, 'w') as f:
        json.dump(grouped, f, indent=4)

    print(f"Saved grouped syllabus to '{output_path}'")
    return grouped


if __name__ == "__main__":
    group_syllabus_file(
        "completed_syllabus.json",
        "grouped_syllabus.json",
        unit_targets=DEFAULT_UNIT_HOURS,
    )
