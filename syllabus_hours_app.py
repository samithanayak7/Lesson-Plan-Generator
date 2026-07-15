import streamlit as st
import pandas as pd
import tempfile
import os
import json

from main import generate_skeleton_json
from json_filler import process_syllabus, DEFAULT_UNIT_HOURS

# ----------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------

st.set_page_config(
    page_title="Syllabus Hours Extractor",
    page_icon="📘",
    layout="wide"
)

st.title("📘 Syllabus Hours Extractor")
st.write(
    "Upload a syllabus .txt file and the matching lecture-notes PDF. "
    "The app builds a topic skeleton from the text, sends it plus the PDF "
    "to Gemini to fill in difficulty/hours, scales the hours to your "
    "per-unit targets, and displays the result."
)

# ----------------------------------------------------
# FILE UPLOAD
# ----------------------------------------------------

col_txt, col_pdf = st.columns(2)

with col_txt:
    txt_file = st.file_uploader("Choose a syllabus TXT file", type=["txt"])

with col_pdf:
    pdf_file = st.file_uploader("Choose the lecture-notes PDF", type=["pdf"])

# ----------------------------------------------------
# HELPER: Parse the enriched JSON into sections
# ----------------------------------------------------

DEFAULT_HOURS_PER_TOPIC = 1


def parse_json_sections(data):
    """
    Expects a JSON object shaped like:

    {
        "Unit Name": {
            "Subtopics": [
                {
                    "name": "Topic Name",
                    "lecture_hours": 2,   # or null
                    ... other metadata fields ...
                },
                ...
            ]
        },
        ...
    }

    Returns a list of {"heading": unit_name, "topics": [(topic_name, hours), ...]}
    Falls back to DEFAULT_HOURS_PER_TOPIC whenever lecture_hours is missing/null.
    """
    sections = []

    for unit_name, unit_data in data.items():
        subtopics = unit_data.get("Subtopics", []) if isinstance(unit_data, dict) else []

        topics = []
        for st_item in subtopics:
            name = (st_item.get("name") or "").strip()
            if not name:
                continue

            hours = st_item.get("lecture_hours")
            if hours is None:
                hours = DEFAULT_HOURS_PER_TOPIC

            topics.append((name, hours))

        sections.append({"heading": unit_name, "topics": topics})

    return sections


# ----------------------------------------------------
# HELPER: Build a topic-hours table + per-unit totals
# ----------------------------------------------------

def build_hours_table(sections):
    """
    Builds a flat table with one row per topic (using each topic's
    allocated hours), plus a summary table with total hours per unit
    (section heading).

    Returns (topic_df, unit_totals_df).
    """
    rows = []
    for section in sections:
        for topic, hours in section["topics"]:
            rows.append({
                "Unit": section["heading"],
                "Topic": topic,
                "Hours": hours
            })

    topic_df = pd.DataFrame(rows, columns=["Unit", "Topic", "Hours"])

    if topic_df.empty:
        unit_totals_df = pd.DataFrame(columns=["Unit", "Total Hours"])
    else:
        unit_totals_df = (
            topic_df.groupby("Unit", sort=False)["Hours"]
            .sum()
            .reset_index()
            .rename(columns={"Hours": "Total Hours"})
        )

    return topic_df, unit_totals_df


# ----------------------------------------------------
# PROCESS FILES
# ----------------------------------------------------

if txt_file is not None and pdf_file is not None:

    st.success("✅ Files Uploaded Successfully")

    st.write("### File Details")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Syllabus:**", txt_file.name, f"({round(txt_file.size / 1024, 2)} KB)")

    with col2:
        st.write("**Lecture notes:**", pdf_file.name, f"({round(pdf_file.size / 1024, 2)} KB)")

    st.divider()

    # Build the skeleton (Step 1 only) as soon as the txt is available, so
    # we know the unit names and can show hour-target inputs for them.
    try:
        txt_bytes = txt_file.getvalue()
        syllabus_text = txt_bytes.decode("utf-8")
        skeleton = generate_skeleton_json(syllabus_text)
        st.session_state["skeleton"] = skeleton
    except UnicodeDecodeError as e:
        st.error(f"❌ Could not read TXT file: {e}")
        skeleton = None

    if "skeleton" in st.session_state and st.session_state["skeleton"]:
        skeleton = st.session_state["skeleton"]
        unit_names = list(skeleton.keys())

        st.write("### 🎯 Target hours per unit")
        st.caption("Gemini estimates raw hours per topic; these targets are used to scale each unit's topics to add up exactly.")

        unit_limits = {}
        cols = st.columns(min(len(unit_names), 4) or 1)
        for i, unit_name in enumerate(unit_names):
            with cols[i % len(cols)]:
                unit_limits[unit_name] = st.number_input(
                    unit_name,
                    min_value=0.0,
                    value=12.0,
                    step=0.5,
                    key=f"limit_{unit_name}"
                )

        if st.button("📖 Extract Syllabus"):
            tmp_pdf_path = None
            try:
                # json_filler uploads the PDF by path, so write it to a
                # temp file first.
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(pdf_file.getvalue())
                    tmp_pdf_path = tmp_pdf.name

                with st.spinner("Sending skeleton + PDF to Gemini and scaling hours..."):
                    data = process_syllabus(skeleton, tmp_pdf_path, unit_limits)

                sections = parse_json_sections(data)

                # Store in session_state so later reruns (e.g. downloading a
                # file) don't force the user to re-extract.
                st.session_state["sections"] = sections
                st.session_state["full_json"] = data
            except Exception as e:
                st.error(f"❌ Pipeline failed: {e}")
            finally:
                if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                    os.remove(tmp_pdf_path)

    # ----------------------------------------
    # Display extracted syllabus (persists across reruns)
    # ----------------------------------------

    if "sections" in st.session_state:

        sections = st.session_state["sections"]

        # ----------------------------------------
        # Hours table + total hours per unit
        # ----------------------------------------

        st.header("⏱️ Time Allocation")

        topic_hours_df, unit_totals_df = build_hours_table(sections)

        if topic_hours_df.empty:
            st.info("No topics were found to allocate hours to.")
        else:
            col_a, col_b = st.columns([2, 1])

            with col_a:
                st.subheader("Topic-by-topic hours")
                st.dataframe(
                    topic_hours_df,
                    use_container_width=True,
                    hide_index=True
                )

            with col_b:
                st.subheader("Total hours per unit")
                st.dataframe(
                    unit_totals_df,
                    use_container_width=True,
                    hide_index=True
                )
                st.markdown(f"**Grand total: {int(topic_hours_df['Hours'].sum())} hrs**")

            hours_csv = topic_hours_df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Hours Table (CSV)",
                data=hours_csv,
                file_name="topic_hours.csv",
                mime="text/csv"
            )

        st.success("🎉 Syllabus Extracted Successfully")

        if "full_json" in st.session_state:
            with st.expander("🔍 View raw JSON"):
                st.json(st.session_state["full_json"])

            st.download_button(
                label="⬇️ Download Full JSON",
                data=json.dumps(st.session_state["full_json"], indent=4),
                file_name="completed_syllabus.json",
                mime="application/json"
            )
