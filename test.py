import json
from google import genai
from google.genai import types
import pathlib

# Initialize the Gemini client
client = genai.Client(api_key="AIzaSyD_iaP7Q1-8blcRIAgUVRM3sdX4VZhaLp4")

# Path to your PDF file
filepath = pathlib.Path("/Users/amanueltefera/docunder/referral_package.pdf")

# Prompt for the model
prompt = (
    "Please extract all the major sections from this resume. "
    "Each section should have a title and the full text. Format it as JSON."
)

# Send the PDF and prompt to Gemini
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=[
        types.Part.from_bytes(
            data=filepath.read_bytes(),
            mime_type="application/pdf",
        ),
        prompt
    ]
)

print(response.text)
