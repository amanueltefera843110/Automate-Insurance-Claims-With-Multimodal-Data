# DocUnder PDF Section Extractor

DocUnder is a web application that allows users to upload PDF documents and extract all major sections and structured data using Google Gemini AI. The extracted content is presented in a structured JSON format and can be downloaded as a formatted PDF.

## Features
- Secure PDF upload and processing
- Extraction of document structure, sections, and metadata
- Output in structured JSON and downloadable PDF
- All sensitive credentials managed via environment variables

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/docunder.git
   cd docunder
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` and fill in your actual API keys and configuration values:
     ```bash
     cp .env.example .env
     # Edit .env and set GEMINI_API_KEY, SECRET_KEY, etc.
     ```

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key
- `SECRET_KEY`: Flask secret key for session management
- `UPLOAD_FOLDER`: Directory for storing uploaded files (default: uploads/)

## Usage

1. **Start the application:**
   ```bash
   python app.py
   ```
2. **Open your browser and go to:**
   [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
3. **Upload a PDF and extract its sections!**

## Dependencies
- Python 3.7+
- Flask
- fpdf
- google-generativeai

See `requirements.txt` for the full list.

## Security Notes
- Never commit your `.env` file or API keys to version control.
- Uploaded files are deleted after processing for privacy.

## License
MIT License
# Automate-Insurance-Claims-With-Multimodal-Data
