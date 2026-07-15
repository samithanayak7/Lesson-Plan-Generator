# import os
# import json
# from typing import List, Optional, Dict
# from pydantic import BaseModel, Field
# from google import genai
# from google.genai import types

# # Initialize the Gemini Client
# # The SDK automatically looks for the GEMINI_API_KEY environment variable
# client = genai.Client()

# # ---------------------------------------------------------
# # Step 1: Define the Strict Target Output Schema using Pydantic
# # ---------------------------------------------------------
# class Subtopic(BaseModel):
#     name: str
#     difficulty: str = Field(description="Difficulty level: Beginner, Intermediate, or Advanced")
#     lecture_hours: float = Field(description="Estimated time to cover this subtopic in hours (decimal allowed format)")
#     learning_objective: str = Field(description="A concise statement of what the student will achieve")
#     prerequisites: List[str] = Field(default_factory=list, description="List of direct prerequisite concepts required")
#     keywords: List[str] = Field(default_factory=list, description="Core programming terms or concepts associated")
#     teaching_method: str = Field(description="Recommended approach, e.g., Interactive Lecture, Live Coding, Lab Demonstration")
#     assessment_type: str = Field(description="E.g., Code Evaluation, Quiz, Debugging Assignment, Viva Voce")

# class TopicSyllabus(BaseModel):
#     Subtopics: List[Subtopic]

# # Type mapping for the full nested system structure
# SyllabusMapping = Dict[str, TopicSyllabus]


# # ---------------------------------------------------------
# # Step 2: Main Processing Function
# # ---------------------------------------------------------
# def fill_syllabus_metadata(json_input_path: str, reference_notes_text: str) -> str:
#     # Load your template skeleton
#     with open(json_input_path, 'r') as f:
#         skeleton_json = json.load(f)
    
#     # Construct a descriptive, instruction-driven systemic prompt
#     prompt = f"""
#     You are an expert academic curriculum engineer specializing in Computer Science and C programming pedagogy.
    
#     TASK:
#     Analyze the provided Reference Lecture Notes/Slides text and use it to populate all the missing metadata (null fields) for each topic and subtopic given in the Input Skeleton JSON.
    
#     CRITICAL INSTRUCTIONS:
#     1. Base the 'difficulty', 'lecture_hours', and 'learning_objective' directly on the depth, length, and complexity of content present in the Reference Notes.
#     2. Maintain the exact topic and subtopic hierarchy as provided.
#     3. Ensure no empty or null string values remain. Extract explicit, meaningful keywords and prerequisites.
    
#     --- START REFERENCE NOTES ---
#     {reference_notes_text}
#     --- END REFERENCE NOTES ---
    
#     --- START INPUT SKELETON JSON ---
#     {json.dumps(skeleton_json, indent=2)}
#     --- END INPUT SKELETON JSON ---
#     """
    
#     print("Sending blueprint payload to Gemini Flash...")
    
#     # Call the API utilizing gemini-2.5-flash (fast, highly optimized for structured tasks)
#     response = client.models.generate_content(
#         model='gemini-2.5-flash',
#         contents=prompt,
#         config=types.GenerateContentConfig(
#             # Enforce strict output schema structure matching our Pydantic target
#             response_mime_type="application/json",
#             response_schema=SyllabusMapping,
#             temperature=0.2, # Low temperature for programmatic consistency
#         ),
#     )
    
#     return response.text

# # ---------------------------------------------------------
# # Step 3: Execution block
# # ---------------------------------------------------------
# if __name__ == "__main__":
#     # Save your provided skeleton JSON locally as 'input_skeleton.json'
#     # Save your extracted notes/slides content into a text variable or local text file
#     sample_notes_text = """
#     PES UNIVERSITY
#     Problem Solving With C - UE25CS151B
#     Unit Name: Problem Solving Fundamentals
#     Topic: Introduction to C and C Features
#     Course objectives: ... [Your full notes payload text string goes here] ...
#     """
    
#     # Dummy creation of file for testing purposes
#     input_file = "input_skeleton.json"
    
#     try:
#         # Run the automation pipeline
#         completed_json_str = fill_syllabus_metadata(input_file, sample_notes_text)
        
#         # Format and save output
#         final_output = json.loads(completed_json_str)
#         output_file = "completed_syllabus.json"
        
#         with open(output_file, 'w') as f:
#             json.dump(final_output, f, indent=4)
            
#         print(f"\n Success! Missing curriculum values filled. Saved array output to: '{output_file}'")
        
#     except Exception as e:
#         print(f"\nPipeline Execution Failed: {str(e)}")

# import os
# import json
# from typing import List, Dict
# from pydantic import BaseModel, Field
# from google import genai
# from google.genai import types

# from dotenv import load_dotenv
# # import os

# load_dotenv()

# # Initialize the Gemini Client
# client = genai.Client()

# print(os.getenv("GEMINI_API_KEY"))

# # ---------------------------------------------------------
# # Step 1: Define the Strict Target Output Schema
# # ---------------------------------------------------------
# class Subtopic(BaseModel):
#     name: str
#     difficulty: str = Field(description="Difficulty level: Beginner, Intermediate, or Advanced")
#     lecture_hours: float = Field(description="Estimated time to cover this subtopic in hours")
#     learning_objective: str = Field(description="A concise statement of what the student will achieve")
#     prerequisites: List[str] = Field(default_factory=list, description="List of direct prerequisite concepts required")
#     keywords: List[str] = Field(default_factory=list, description="Core programming terms or concepts associated")
#     teaching_method: str = Field(description="Recommended approach, e.g., Interactive Lecture, Live Coding, Lab Demonstration")
#     assessment_type: str = Field(description="E.g., Code Evaluation, Quiz, Debugging Assignment, Viva Voce")

# class TopicSyllabus(BaseModel):
#     Subtopics: List[Subtopic]

# SyllabusMapping = Dict[str, TopicSyllabus]

# # ---------------------------------------------------------
# # Step 2: Main Processing Function (Now with PDF Upload)
# # ---------------------------------------------------------
# def process_syllabus_from_pdf(json_input_path: str, pdf_path: str) -> str:
#     # Load your template skeleton
#     with open(json_input_path, 'r') as f:
#         skeleton_json = json.load(f)
        
#     print(f"Uploading {pdf_path} to Gemini...")
#     # Upload the PDF directly using the File API
#     uploaded_pdf = client.files.upload(file=pdf_path)
    
#     prompt = f"""
#     You are an expert academic curriculum engineer.
    
#     TASK:
#     Analyze the attached PDF Lecture Notes and use it to populate all the missing metadata (null fields) for each topic and subtopic given in the Input Skeleton JSON.
    
#     CRITICAL INSTRUCTIONS:
#     1. Base the 'difficulty', 'lecture_hours', and 'learning_objective' directly on the depth and complexity of the content in the PDF.
#     2. Maintain the exact topic and subtopic hierarchy as provided.
    
#     --- START INPUT SKELETON JSON ---
#     {json.dumps(skeleton_json, indent=2)}
#     --- END INPUT SKELETON JSON ---
#     """
    
#     print("Sending payload to Gemini Flash...")
    
#     # Pass the prompt AND the uploaded PDF to the model
#     response = client.models.generate_content(
#         model='gemini-2.5-flash',
#         contents=[prompt, uploaded_pdf], 
#         config=types.GenerateContentConfig(
#             response_mime_type="application/json",
#             response_schema=SyllabusMapping,
#             temperature=0.2,
#         ),
#     )
    
#     return response.text

# # ---------------------------------------------------------
# # Step 3: Execution Block
# # ---------------------------------------------------------
# if __name__ == "__main__":
#     # Define your file names
#     input_file = "enriched_jasonfile.json"
#     pdf_file = "Unit 1 C notes_merged.pdf"
    
#     try:
#         # Run the automation pipeline
#         completed_json_str = process_syllabus_from_pdf(input_file, pdf_file)
        
#         # Format and save output
#         final_output = json.loads(completed_json_str)
#         output_file = "completed_syllabus.json"
        
#         with open(output_file, 'w') as f:
#             json.dump(final_output, f, indent=4)
            
#         print(f"\nSuccess! Missing curriculum values filled. Saved to: '{output_file}'")
        
#     except Exception as e:
#         print(f"\nPipeline Execution Failed: {str(e)}")

# import os
# import json
# from google import genai
# from google.genai import types

# # Initialize the Gemini Client
# client = genai.Client()

# # ---------------------------------------------------------
# # Main Processing Function
# # ---------------------------------------------------------
# def process_syllabus_from_pdf(json_input_path: str, pdf_path: str) -> str:
#     # Load your template skeleton
#     with open(json_input_path, 'r') as f:
#         skeleton_json = json.load(f)
        
#     print(f"Uploading {pdf_path} to Gemini...")
#     # Upload the PDF directly using the File API
#     uploaded_pdf = client.files.upload(file=pdf_path)
    
#     prompt = f"""
#     You are an expert academic curriculum engineer.
    
#     TASK:
#     Analyze the attached PDF Lecture Notes and use it to populate all the missing metadata (null fields) for each topic and subtopic given in the Input Skeleton JSON.
    
#     CRITICAL INSTRUCTIONS:
#     1. Base the 'difficulty', 'lecture_hours', and 'learning_objective' directly on the depth and complexity of the content in the PDF.
#     2. Maintain the exact topic and subtopic hierarchy as provided.
#     3. Output ONLY a valid JSON object matching the exact structure of the skeleton below, with all nulls filled.
    
#     --- START INPUT SKELETON JSON ---
#     {json.dumps(skeleton_json, indent=2)}
#     --- END INPUT SKELETON JSON ---
#     """
    
#     print("Sending payload to Gemini Flash...")
    
#     # Pass the prompt AND the uploaded PDF to the model
#     response = client.models.generate_content(
#         model='gemini-3.5-flash',
#         contents=[prompt, uploaded_pdf], 
#         config=types.GenerateContentConfig(
#             # We strictly enforce JSON output, and it will natively follow the skeleton in the prompt
#             response_mime_type="application/json",
#             temperature=0.2,
#         ),
#     )
    
#     return response.text

# # ---------------------------------------------------------
# # Execution Block
# # ---------------------------------------------------------
# if __name__ == "__main__":
#     # Define your file names
#     input_file = "enriched_jasonfile.json"
#     pdf_file = "Unit 1 C notes_merged.pdf"
    
#     try:
#         # Run the automation pipeline
#         completed_json_str = process_syllabus_from_pdf(input_file, pdf_file)
        
#         # Format and save output
#         final_output = json.loads(completed_json_str)
#         output_file = "completed_syllabus.json"
        
#         with open(output_file, 'w') as f:
#             json.dump(final_output, f, indent=4)
            
#         print(f"\nSuccess! Missing curriculum values filled. Saved to: '{output_file}'")
        
#     except Exception as e:
#         print(f"\nPipeline Execution Failed: {str(e)}")

import os
import json
from google import genai
from google.genai import types

# Initialize the Gemini Client
client = genai.Client()

# ---------------------------------------------------------
# Step 1: Main Processing Function
# ---------------------------------------------------------
def process_syllabus_from_pdf(json_input_path: str, pdf_path: str, unit_limits: dict) -> dict:
    # Load your template skeleton
    with open(json_input_path, 'r') as f:
        skeleton_json = json.load(f)
        
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

# ---------------------------------------------------------
# Step 3: Execution Block
# ---------------------------------------------------------
if __name__ == "__main__":
    input_file = "enriched_jasonfile.json"
    pdf_file = "Unit 1 C notes_merged.pdf"
    
    # Define the exact total hours allowed for each unit
    target_unit_hours = {
        "Problem Solving Fundamentals": 12.0,
        "Counting, Sorting and Searching": 15.0,
        "Text Processing and UserDefined Types": 18.0,
        "File Handling and Portable Programming": 10.0
    }
    
    try:
        # Run the automation pipeline
        final_output = process_syllabus_from_pdf(input_file, pdf_file, target_unit_hours)
        
        output_file = "completed_syllabus.json"
        with open(output_file, 'w') as f:
            json.dump(final_output, f, indent=4)
            
        print(f"\nSuccess! Missing curriculum values filled and hours scaled. Saved to: '{output_file}'")
        
    except Exception as e:
        print(f"\nPipeline Execution Failed: {str(e)}")