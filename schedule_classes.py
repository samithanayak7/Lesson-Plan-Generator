"""
Class Scheduler
================
Reads a syllabus JSON (units -> Subtopics -> [{name, lecture_hours, ...}])
and produces a course-plan JSON that assigns topics to classes.

HARD CONSTRAINT (must always hold):
    number_of_classes_for_a_unit == round(sum of lecture_hours of all
    topics in that unit)

Approach: "timeline slicing"
-----------------------------
1. Lay all of a unit's topics end-to-end on one timeline, in their
   given order, where each topic occupies a segment equal to its
   lecture_hours.
2. Cut that timeline into exactly `num_classes` EQUAL-LENGTH segments
   (class_length = total_hours / num_classes, which is ~1 hour).
3. A topic is listed in every class-segment it meaningfully overlaps.

Why this satisfies the constraint no matter what:
 - The number of classes is fixed by construction (step 2), not by how
   many topics exist. So even a unit with only 10 topics needing 15
   classes still gets exactly 15 classes -- some topics (the longer
   ones) naturally span 2+ consecutive classes, which also happens to
   mirror how real lesson plans work (a meaty topic like "Pointers"
   legitimately carries over into a second lecture).
 - Conversely a unit with many short topics will have several of them
   packed into a single class.
 - Per-class hours will be close to 1 (±~0.2 hrs) since class_length is
   the unit's own average; only the FIRST/LAST class of a topic-heavy
   overlap has any looseness, and negligible overlap slivers are
   filtered out (min_overlap) so no class is listed with a topic it
   barely touched.
"""

import json
import sys


def timeline_partition(items, key_func, num_classes, min_overlap=0.05):
    """
    Same timeline-slicing idea as before (guarantees exactly
    `num_classes` classes), but each topic is now listed in only ONE
    class: whichever class-segment it overlaps the MOST. So if
    "Variables" spends 0.2 hrs of class-time in class 3 and 0.4 hrs in
    class 4, it is only named in class 4 -- the class where it actually
    needs the most teaching time. It still contributes its full
    lecture_hours to the timeline math (so the class-count constraint
    is untouched); it just isn't *labelled* in every class it merely
    grazes.
    """
    hours = [key_func(it) for it in items]
    total = sum(hours)
    n = len(items)
    k = max(1, num_classes)
    class_len = total / k

    starts, cum = [], 0.0
    for h in hours:
        starts.append(cum)
        cum += h
    ends = [s + h for s, h in zip(starts, hours)]

    # overlap[idx][i] = how many hours topic `idx` spends inside class i
    overlap = [[0.0] * k for _ in range(n)]
    for idx in range(n):
        for i in range(k):
            c_start, c_end = i * class_len, (i + 1) * class_len
            ov = min(ends[idx], c_end) - max(starts[idx], c_start)
            if ov > min_overlap:
                overlap[idx][i] = ov

    classes = [[] for _ in range(k)]

    # Step 1: assign each topic to the single class where it spends the
    # most time (its "primary" class).
    assigned_class_for_topic = []
    for idx in range(n):
        row = overlap[idx]
        best_i = max(range(k), key=lambda i: row[i])
        assigned_class_for_topic.append(best_i)
        classes[best_i].append(items[idx])

    # Step 2: a class could end up with nothing assigned to it (its
    # overlapping topics all had their bigger share elsewhere). Backfill
    # such empty classes with whichever topic overlaps it most, even if
    # that topic's primary class is different -- better to show the
    # topic that was actually being taught than to leave a class blank.
    for i in range(k):
        if classes[i]:
            continue
        candidates = [idx for idx in range(n) if overlap[idx][i] > 0]
        if candidates:
            best_idx = max(candidates, key=lambda idx: overlap[idx][i])
        else:
            c_start, c_end = i * class_len, (i + 1) * class_len
            mid = (c_start + c_end) / 2
            best_idx = min(range(n), key=lambda idx: abs((starts[idx] + ends[idx]) / 2 - mid))
        classes[i].append(items[best_idx])

    return classes


def schedule_from_data(data, sheet_name="course_plan"):
    """
    Core entry point: takes the syllabus dict already in memory
    (same shape as completed_syllabus.json --
     {unit_name: {"Subtopics": [{"name", "lecture_hours", ...}, ...]}, ...})
    and returns (output, report):
      - output: the course-plan dict, ready to json.dump or st.json
      - report: a list of per-unit stats (total_hours, num_classes) useful
        for a sanity-check / summary table in a UI
    No file I/O happens here, so this is safe to call directly from a
    Streamlit app on data that only exists in session_state.
    """
    output = {"sheet_name": sheet_name}
    report = []

    for unit_idx, (unit_name, unit_data) in enumerate(data.items(), start=1):
        subtopics = unit_data["Subtopics"]
        total_hours = sum(t["lecture_hours"] for t in subtopics)
        num_classes = max(1, round(total_hours))

        groups = timeline_partition(subtopics, lambda t: t["lecture_hours"], num_classes)

        unit_dict = {}
        for class_idx, group in enumerate(groups, start=1):
            # de-dup while preserving order, in case fallback logic ever repeats a topic
            seen = set()
            names = []
            for t in group:
                if t["name"] not in seen:
                    names.append(t["name"])
                    seen.add(t["name"])
            unit_dict[f"class_{class_idx}"] = names

        output[f"unit_{unit_idx}"] = [unit_dict]

        report.append({
            "unit": unit_name,
            "total_hours": round(total_hours, 2),
            "num_classes": len(groups),
        })

    return output, report


def build_course_plan(input_path, output_path, sheet_name="course_plan"):
    """File-based wrapper around schedule_from_data (used by the CLI)."""
    with open(input_path, "r") as f:
        data = json.load(f)

    output, report = schedule_from_data(data, sheet_name=sheet_name)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    return report


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/completed_syllabus.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "/mnt/user-data/outputs/course_plan.json"

    report = build_course_plan(in_path, out_path)

    print(f"Course plan written to: {out_path}\n")
    for r in report:
        print(f"Unit: {r['unit']}")
        print(f"  total lecture hours : {r['total_hours']}")
        print(f"  classes scheduled   : {r['num_classes']}  (== round(total_hours)) OK" if
              r['num_classes'] == max(1, round(r['total_hours'])) else "  MISMATCH")
        print()
