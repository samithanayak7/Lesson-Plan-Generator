import os
import json
from google import genai
from google.genai import types

# Initialize the Gemini Client
client = genai.Client(api_key="ENTER_YOUR_API_KEY")

# ---------------------------------------------------------
# Default per-unit hour targets (used as fallback/prefill values;
# the Streamlit app lets these be overridden per unit).
# ---------------------------------------------------------
DEFAULT_UNIT_HOURS = {
    "Problem Solving Fundamentals": 12.0,
    "Counting, Sorting and Searching": 15.0,
    "Text Processing and UserDefined Types": 18.0,
    "File Handling and Portable Programming": 10.0
}


# ---------------------------------------------------------
# Step 1: Main Processing Function
# ---------------------------------------------------------
def process_syllabus(skeleton_json: dict, pdf_path: str, unit_limits: dict) -> dict:
    """
    Core pipeline: takes an in-memory skeleton dict (nulls not yet filled),
    a path to a PDF of lecture notes, and per-unit hour targets. Uploads
    the PDF to Gemini, asks it to fill the nulls, then scales lecture_hours
    per unit to match unit_limits. Returns the completed dict.
    """
    print(f"Uploading {pdf_path} to Gemini...")
    uploaded_pdf = client.files.upload(file=pdf_path)
    
    prompt = f"""
    You are an expert academic curriculum engineer.
    
    TASK:
    Analyze the attached PDF Lecture Notes and use it to populate all the missing metadata (null fields) for each topic and subtopic given in the Input Skeleton JSON.
    
    CRITICAL INSTRUCTIONS:
    1. 'difficulty': Assign a numerical score between 1 (easiest) and 10 (hardest) based on the conceptual depth in the PDF. Output this as an integer.
    2. 'lecture_hours': Assign an estimated raw duration in hours. These will act as relative weights.
    3. Maintain the exact topic and subtopic hierarchy as provided.
    4. Output ONLY a valid JSON object matching the exact structure of the skeleton below, with all nulls filled.
    
    --- START INPUT SKELETON JSON ---
    {json.dumps(skeleton_json, indent=2)}
    --- END INPUT SKELETON JSON ---
    """
    
    print("Sending payload to Gemini...")
    
    # Pass the prompt AND the uploaded PDF to the model
    # Note: Using gemini-2.0-flash as the standard stable endpoint. 
    response = client.models.generate_content(
        model='gemini-3.5-flash', 
        contents=[prompt, uploaded_pdf], 
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    
    # Parse the LLM's JSON response
    syllabus_data = json.loads(response.text)
    
    # ---------------------------------------------------------
    # Step 2: Scale the Lecture Hours mathematically
    # ---------------------------------------------------------
    print("Scaling lecture hours to fit unit limits...")
    for unit_name, unit_data in syllabus_data.items():
        if unit_name in unit_limits:
            target_hours = unit_limits[unit_name]
            subtopics = unit_data.get("Subtopics", [])
            
            # Find the total hours the LLM estimated for this unit
            current_sum = sum(float(sub.get("lecture_hours", 0)) for sub in subtopics)
            
            if current_sum > 0:
                # Scale each subtopic to fit exactly into the target_hours
                for sub in subtopics:
                    raw_hours = float(sub.get("lecture_hours", 0))
                    scaled_hours = (raw_hours / current_sum) * target_hours
                    # Round to 1 decimal place for cleaner schedules (e.g., 1.5 hours)
                    sub["lecture_hours"] = round(scaled_hours, 1)
                    
    return syllabus_data

def process_syllabus_from_pdf(json_input_path: str, pdf_path: str, unit_limits: dict) -> dict:
    """
    Thin wrapper preserving the original file-based interface: loads the
    skeleton JSON from disk, then calls process_syllabus().
    """
    with open(json_input_path, 'r') as f:
        skeleton_json = json.load(f)
    return process_syllabus(skeleton_json, pdf_path, unit_limits)


# ---------------------------------------------------------
# Step 3: Execution Block
# ---------------------------------------------------------
if __name__ == "__main__":
    input_file = "enriched.json"
    pdf_file = "Unit 1 C notes_merged.pdf"
    
    # Define the exact total hours allowed for each unit
    target_unit_hours = DEFAULT_UNIT_HOURS
    
    try:
        # Run the automation pipeline
        final_output = process_syllabus_from_pdf(input_file, pdf_file, target_unit_hours)
        
        output_file = "completed_syllabus.json"
        with open(output_file, 'w') as f:
            json.dump(final_output, f, indent=4)
            
        print(f"\nSuccess! Missing curriculum values filled and hours scaled. Saved to: '{output_file}'")
        
    except Exception as e:
        print(f"\nPipeline Execution Failed: {str(e)}")
