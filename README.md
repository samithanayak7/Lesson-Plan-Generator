# Syllabus Hours Extractor

A Streamlit app that takes a syllabus text file and a lecture-notes PDF,
uses Gemini to fill in per-topic difficulty and lecture hours, scales
those hours to match your target hours per unit, and displays the
result as a table.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set your Gemini API key as an environment variable (or `.env` file):
   ```
   GEMINI_API_KEY=your_key_here
   ```
   Get a key at https://aistudio.google.com/apikey.

   Don't have an env var set? The app also has a sidebar field where you
   can paste your key directly.

## Running the app

```
streamlit run syllabus_hours_app.py
```

Then, in the browser tab that opens:

1. Upload your syllabus `.txt` file and the matching lecture-notes `.pdf`.
2. Set the target hours for each detected unit (pre-filled with sensible
   defaults).
3. Click **Extract Syllabus**.

## How it works

```
syllabus.txt  --[ main.py: generate_skeleton_json ]-->  skeleton (topics, nulls)
                                                              |
notes.pdf     ------------------------------------------------
                                                              v
                                    [ json_filler.py: process_syllabus ]
                                    (sends skeleton + PDF to Gemini,
                                     fills difficulty/lecture_hours,
                                     scales hours to unit targets)
                                                              |
                                                              v
                                            completed_syllabus.json
                                                              |
                                                              v
                                    displayed as a table in Streamlit
                                    (+ CSV / JSON download buttons)
```

## Files

- `syllabus_hours_app.py` — Streamlit UI: file uploads, unit hour inputs,
  table display, downloads.
- `main.py` — Step 1 pipeline (clean → split → extract) that turns raw
  syllabus text into a topic skeleton.
- `json_filler.py` — Sends the skeleton + PDF to Gemini, fills in missing
  fields, and scales `lecture_hours` per unit to match your targets.
- `step1/`, `step2/` — Supporting modules used by `main.py`.

## Notes

- Never commit your `.env` file or API key to git.
- The app writes the uploaded PDF to a temporary file only for the
  duration of the Gemini call; it's deleted afterward.
