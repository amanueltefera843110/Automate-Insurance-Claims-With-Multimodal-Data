import os
from dotenv import load_dotenv  # Add this import
import pathlib
from flask import Flask, request, render_template_string
import google.generativeai as genai
from fpdf import FPDF
import json
from flask import send_file, session, redirect, url_for
import io

# Load environment variables from .env file
load_dotenv()

UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure the Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize the model
model = genai.GenerativeModel('gemini-1.5-flash')

HTML_FORM = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>DocUnder PDF Section Extractor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: #f4f7fa;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: #222;
        }
        .container {
            max-width: 700px;
            margin: 40px auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 40px 32px 32px 32px;
        }
        h1 {
            text-align: center;
            color: #2a5298;
            margin-bottom: 16px;
            font-size: 2.2em;
            letter-spacing: 1px;
        }
        p {
            text-align: center;
            color: #555;
            margin-bottom: 32px;
        }
        form {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 18px;
            margin-bottom: 24px;
        }
        input[type="file"] {
            padding: 8px;
            border: 1px solid #b0c4de;
            border-radius: 6px;
            background: #f8fafc;
            font-size: 1em;
            width: 100%;
            max-width: 350px;
        }
        input[type="submit"] {
            background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
            color: #fff;
            border: none;
            border-radius: 6px;
            padding: 12px 32px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
            box-shadow: 0 2px 8px rgba(42,82,152,0.08);
        }
        input[type="submit"]:hover {
            background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        }
        .result-section {
            margin-top: 36px;
            background: #f8fafc;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 1px 6px rgba(42,82,152,0.06);
        }
        h2 {
            color: #1e3c72;
            margin-bottom: 16px;
            font-size: 1.3em;
            border-bottom: 1px solid #e0e7ef;
            padding-bottom: 8px;
        }
        pre {
            background: #23272e;
            color: #e6e6e6;
            border-radius: 6px;
            padding: 18px;
            font-size: 0.98em;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            margin: 0;
        }
        .download-btn {
            background: #2a5298;
            color: #fff;
            padding: 10px 28px;
            border: none;
            border-radius: 6px;
            font-size: 1em;
            cursor: pointer;
            transition: background 0.2s;
        }
        .download-btn:hover {
            background: #1e3c72;
        }
        .error {
            background: #fee;
            border: 1px solid #fcc;
            color: #c33;
            padding: 12px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            display: none;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        }
        .loading-content {
            text-align: center;
            color: white;
        }
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #2a5298;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .loading-text {
            font-size: 1.2em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .loading-subtext {
            font-size: 0.9em;
            opacity: 0.8;
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 0.4; }
        }
        .dots {
            display: inline-block;
        }
        .dots::after {
            content: '';
            animation: dots 1.5s steps(4, end) infinite;
        }
        @keyframes dots {
            0%, 20% { content: ''; }
            40% { content: '.'; }
            60% { content: '..'; }
            80%, 100% { content: '...'; }
        }
        @media (max-width: 600px) {
            .container {
                padding: 18px 4vw 18px 4vw;
            }
            h1 {
                font-size: 1.3em;
            }
            pre {
                font-size: 0.92em;
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>DocUnder PDF Section Extractor</h1>
        <p>Upload a PDF document to extract all sections and structured data.<br>
        <span style="font-size:0.95em;color:#888;">(Your file is processed securely and deleted after extraction.)</span></p>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".pdf" required>
            <input type="submit" value="Upload & Extract">
        </form>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        {% if result %}
        <form action="{{ url_for('download_pdf') }}" method="get" style="text-align:center;margin-top:18px;">
            <button type="submit" class="download-btn">Download as PDF</button>
        </form>
        <div class="result-section">
            <h2>Extracted Sections (JSON)</h2>
            <pre>{{ result }}</pre>
        </div>
        {% endif %}
    </div>
    
    <!-- Loading Overlay -->
    <div class="loading-overlay" id="loadingOverlay">
        <div class="loading-content">
            <div class="spinner"></div>
            <div class="loading-text">Processing Your Document</div>
            <div class="loading-subtext">
                Extracting sections and analyzing content<span class="dots"></span>
            </div>
        </div>
    </div>
    
    <script>
        // Show loading overlay when form is submitted
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.querySelector('form[method="post"]');
            const loadingOverlay = document.getElementById('loadingOverlay');
            
            form.addEventListener('submit', function(e) {
                const fileInput = document.querySelector('input[type="file"]');
                if (fileInput.files.length > 0) {
                    loadingOverlay.style.display = 'flex';
                    
                    // Add some dynamic text changes
                    const loadingTexts = [
                        "Processing Your Document",
                        "Analyzing PDF Structure",
                        "Extracting Sections",
                        "Organizing Content",
                        "Finalizing Results"
                    ];
                    
                    const subtexts = [
                        "Extracting sections and analyzing content",
                        "Identifying document structure",
                        "Processing text and metadata",
                        "Structuring extracted data",
                        "Almost done"
                    ];
                    
                    let textIndex = 0;
                    const textElement = document.querySelector('.loading-text');
                    const subtextElement = document.querySelector('.loading-subtext');
                    
                    const textInterval = setInterval(() => {
                        textIndex = (textIndex + 1) % loadingTexts.length;
                        textElement.textContent = loadingTexts[textIndex];
                        subtextElement.innerHTML = subtexts[textIndex] + '<span class="dots"></span>';
                    }, 3000);
                    
                    // Clear interval when page unloads or form submission completes
                    window.addEventListener('beforeunload', () => {
                        clearInterval(textInterval);
                    });
                }
            });
            
            // Hide loading overlay if there's an error or result on page load
            const hasError = document.querySelector('.error');
            const hasResult = document.querySelector('.result-section');
            if (hasError || hasResult) {
                loadingOverlay.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

app.secret_key = 'your_secret_key_change_this_in_production'  # Change this in production

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    result = None
    error = None
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                error = "No file selected"
                return render_template_string(HTML_FORM, result=result, error=error)
            
            file = request.files['file']
            if file.filename == '':
                error = "No file selected"
                return render_template_string(HTML_FORM, result=result, error=error)
            
            if file and file.filename.endswith('.pdf'):
                # Save the uploaded file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                
                # Process the PDF
                prompt = """
Please perform a comprehensive extraction and structural analysis of all major sections and data components from the provided PDF document.

EXTRACTION REQUIREMENTS:

1. DOCUMENT ANALYSIS:
   - Identify the document type and format
   - Detect the overall document structure and organization pattern
   - Recognize section headers, subsections, and hierarchical relationships
   - Identify any tables, lists, or structured data elements

2. SECTION IDENTIFICATION AND EXTRACTION:
   - Extract ALL major sections with their exact original titles/headers
   - Identify and extract subsections maintaining their hierarchical structure
   - Capture section metadata (numbering, formatting, position in document)
   - Extract any standalone elements that don't fit into major sections

3. CONTENT PRESERVATION STANDARDS:
   - Maintain EXACT original text without any modifications
   - Preserve all formatting elements
   - Retain original punctuation, capitalization, and spacing
   - Keep numerical data, dates, and measurements in their original format

OUTPUT FORMAT:
Return results as a JSON object with this structure:

{
  "document_metadata": {
    "document_type": "PDF",
    "total_sections": "Number of major sections identified",
    "extraction_timestamp": "Current timestamp"
  },
  "extracted_sections": {
    "section_1": {
      "title": "Exact original section title/header",
      "section_type": "header/paragraph/list/table/mixed",
      "hierarchy_level": 1,
      "content": {
        "raw_text": "Complete unmodified text content",
        "word_count": "Number of words in section"
      }
    }
  }
}

Please process the PDF document and return the structured JSON extraction.
"""
                
                try:
                    # Upload the file to Gemini and generate content
                    uploaded_file = genai.upload_file(filepath)
                    
                    response = model.generate_content([
                        uploaded_file,
                        prompt
                    ])
                    
                    result = response.text
                    
                    # Try to parse the JSON to validate it
                    try:
                        json.loads(result)
                        session['extracted_json'] = result  # Store for PDF download
                    except json.JSONDecodeError:
                        # If it's not valid JSON, still show the result but note the issue
                        session['extracted_json'] = result
                        error = "Note: The extracted content may not be in perfect JSON format."
                    
                    # Clean up the uploaded file from Gemini
                    try:
                        genai.delete_file(uploaded_file.name)
                    except:
                        pass  # File might already be deleted
                    
                except Exception as e:
                    error = f"Error processing with Gemini API: {str(e)}"
                
                # Clean up the local file
                try:
                    os.remove(filepath)
                except:
                    pass
                    
            else:
                error = "Please upload a PDF file"
                
        except Exception as e:
            error = f"An error occurred: {str(e)}"
    
    return render_template_string(HTML_FORM, result=result, error=error)

@app.route('/download_pdf')
def download_pdf():
    extracted_json = session.get('extracted_json')
    if not extracted_json:
        return redirect(url_for('upload_file'))
    
    try:
        # Try to parse as JSON
        try:
            # Clean the JSON string if it has markdown formatting
            clean_json = extracted_json.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json[7:]  # Remove ```json
            if clean_json.endswith('```'):
                clean_json = clean_json[:-3]  # Remove ```
            
            data = json.loads(clean_json)
            sections = data.get('extracted_sections', {})
        except json.JSONDecodeError:
            # If not valid JSON, create a simple structure
            sections = {"raw_content": {"title": "Extracted Content", "section_type": "text", "hierarchy_level": 1}}
            data = {"extracted_sections": sections}
        
        # Create PDF with better formatting
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'Extracted Document Sections', 0, 1, 'C')
                self.ln(10)
            
            def section_header(self, title):
                self.set_font('Arial', 'B', 12)
                self.cell(0, 8, title, 0, 1, 'L')
                self.ln(2)
            
            def section_content(self, content):
                self.set_font('Arial', '', 10)
                # Handle text encoding for special characters
                try:
                    content = content.encode('latin-1', 'replace').decode('latin-1')
                except:
                    content = str(content)
                
                # Split content into lines and add them
                lines = content.split('\n')
                for line in lines:
                    if len(line) > 80:  # Wrap long lines
                        words = line.split(' ')
                        current_line = ''
                        for word in words:
                            if len(current_line + word) < 80:
                                current_line += word + ' '
                            else:
                                if current_line:
                                    self.cell(0, 6, current_line.strip(), 0, 1, 'L')
                                current_line = word + ' '
                        if current_line:
                            self.cell(0, 6, current_line.strip(), 0, 1, 'L')
                    else:
                        self.cell(0, 6, line, 0, 1, 'L')
                self.ln(3)
        
        pdf = PDF()
        pdf.add_page()
        
        # Add document metadata if available
        if 'document_metadata' in data:
            metadata = data['document_metadata']
            pdf.section_header('Document Information')
            pdf.section_content(f"Document Type: {metadata.get('document_type', 'Unknown')}")
            pdf.section_content(f"Total Sections: {metadata.get('total_sections', 'Unknown')}")
            pdf.section_content(f"Extraction Date: {metadata.get('extraction_timestamp', 'Unknown')}")
            pdf.ln(5)
        
        # Add sections with full content
        for sec_key, sec_data in sections.items():
            if isinstance(sec_data, dict):
                title = sec_data.get('title', sec_key)
                section_type = sec_data.get('section_type', 'unknown')
                level = sec_data.get('hierarchy_level', '')
                
                # Add section header
                pdf.section_header(f"{title} (Type: {section_type}, Level: {level})")
                
                # Add section content
                if 'content' in sec_data and isinstance(sec_data['content'], dict):
                    raw_text = sec_data['content'].get('raw_text', '')
                    word_count = sec_data['content'].get('word_count', '')
                    
                    if raw_text:
                        pdf.section_content(raw_text)
                    if word_count:
                        pdf.section_content(f"Word Count: {word_count}")
                elif 'content' in sec_data:
                    pdf.section_content(str(sec_data['content']))
                
                pdf.ln(3)
                
                # Check if we need a new page
                if pdf.get_y() > 250:
                    pdf.add_page()
        
        # Create BytesIO buffer
        pdf_output = io.BytesIO()
        pdf_string = pdf.output(dest='S')
        if isinstance(pdf_string, str):
            pdf_output.write(pdf_string.encode('latin-1'))
        else:
            pdf_output.write(pdf_string)
        pdf_output.seek(0)
        
        return send_file(
            pdf_output, 
            as_attachment=True, 
            download_name="extracted_sections.pdf", 
            mimetype='application/pdf'
        )
        
    except Exception as e:
        # If PDF generation fails, redirect back with error
        return redirect(url_for('upload_file'))

if __name__ == '__main__':
    app.run(debug=True)