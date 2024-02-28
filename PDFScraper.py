import os
import fitz  # PyMuPDF libbrary, counterintuitively pip install PyMuPDF
import requests

from dotenv import load_dotenv
load_dotenv()


#you need to put your openai api key into a .env file in the current working directory
API_KEY = os.environ["OPENAI_API_KEY"]

def find_pdf_files(directory_path):
    pdf_files = []
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            full_path = os.path.join(directory_path, filename)
            pdf_files.append(full_path)
            print(f"PDF file found: {full_path}")
    return pdf_files

def extract_text_from_pdf(pdf_path):
    """
    Opens a PDF file and extracts text from all of its pages.
    
    :param pdf_path: Path to the PDF file.
    :return: A single string containing the text of all pages concatenated.
    """
    try:
        # Open the PDF file
        doc = fitz.open(pdf_path)
        text = ''
        # Iterate through each page in the PDF
        for page in doc:
            # Extract text from the current page
            text += page.get_text()
        # Close the document
        doc.close()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def read_prompt():
    """
    Reads the universal prompt from 'prompts.txt' and returns it as a string.

    :return: The prompt string.
    """
    try:
        with open('prompts.txt', 'r') as file:
            prompt = file.read().strip()
        print("Prompt read successfully from 'prompts.txt'.")
        return prompt
    except Exception as e:
        print(f"Error reading the prompt: {e}")
        return None

def summarize_text_with_gpt4(text, prompt):
    """
    Sends the extracted text to the GPT-4 API for summarization.
    
    :param text: The extracted text from a PDF.
    :param prompt: The universal prompt for summarization.
    :return: The summarized text or None if an error occurs.
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4-turbo-preview",
        "messages": [{"role": "system", "content": prompt},
                     {"role": "user", "content": text}]
    }
    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response_json = response.json()
        summary = response_json['choices'][0]['message']['content']
        print("Text summarized successfully with GPT-4.")
        return summary
    except Exception as e:
        print(f"Error summarizing text with GPT-4: {e}, Response: {response.text}")
        return None

def compose_html_output(summaries_and_titles, errors):
    """
    Generates a single HTML document string with each PDF title followed by its summary.
    Errors are included in a designated 'Errors:' section at the end of the document.

    :param summaries_and_titles: A list of tuples (title, summary) for each PDF.
    :param errors: A list of error messages.
    :return: A string containing the composed HTML document.
    """
    html_output = "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>PDF Summaries</title></head><body>"
    
    for title, summary in summaries_and_titles:
        html_output += f"<section>{summary}</section>"
    
    if errors:
        html_output += "<section><h2>Errors:</h2><ul>"
        for error in errors:
            html_output += f"<li>{error}</li>"
        html_output += "</ul></section>"
    
    html_output += "</body></html>"
    return html_output

def main():
    print("PDFScraper initialized.")
    directory_path = "./fetched"  # Hardcoded directory path as per requirement
    summaries_and_titles = []
    errors = []
    try:
        pdf_files = find_pdf_files(directory_path)
        if pdf_files:
            print(f"Found {len(pdf_files)} PDF files.")
            prompt = read_prompt()
            if prompt is None:
                print("Failed to read prompt. Exiting.")
                return
            for pdf_file in pdf_files:
                try:
                    text = extract_text_from_pdf(pdf_file)
                    if text is not None:
                        summary = summarize_text_with_gpt4(text, prompt)
                        if summary is not None:
                            summaries_and_titles.append((os.path.basename(pdf_file), summary))
                        else:
                            errors.append(f"Failed to summarize PDF: {os.path.basename(pdf_file)}")
                    else:
                        errors.append(f"Failed to extract text from PDF: {os.path.basename(pdf_file)}")
                except Exception as e:
                    errors.append(f"Error processing PDF {os.path.basename(pdf_file)}: {e}")
            html_output = compose_html_output(summaries_and_titles, errors)
            with open("PDF_Summaries.html", "w") as html_file:
                html_file.write(html_output)
                print("Summaries and errors are written to PDF_Summaries.html")
        else:
            print("No PDF files found in the provided directory.")
    except Exception as e:
        print(f"An error occurred while scanning for PDF files: {e}")

if __name__ == "__main__":
    main()