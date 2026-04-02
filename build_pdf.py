from playwright.sync_api import sync_playwright
import markdown
import os

def create_pdf():
    # Read the markdown report
    with open('RAM_SENTINEL_OPERATIONAL_ANALYSIS.md', 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Convert MD to HTML
    html_content = markdown.markdown(text)

    # Add professional styling for the PDF
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            padding: 40px; 
            color: #1a1a24; 
        }}
        h1 {{ 
            color: #1a1a24; 
            border-bottom: 2px solid #00f2ff; 
            padding-bottom: 10px; 
            font-size: 28px;
        }}
        h2 {{ 
            color: #7000ff; 
            margin-top: 35px; 
            font-size: 22px;
        }}
        strong {{ 
            color: #0b0c15; 
        }}
        hr {{ 
            border: 0; 
            height: 1px; 
            background: #e0e0e0; 
            margin: 25px 0; 
        }}
        p {{
            font-size: 14px;
        }}
        code {{
            background-color: #f4f4f5;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: Consolas, monospace;
            font-size: 13px;
            color: #cc0052;
        }}
    </style>
    </head>
    <body>
    {html_content}
    </body>
    </html>
    """

    # Write temporary HTML file
    temp_html = 'temp_operational.html'
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(full_html)

    # Use Playwright to render the HTML into a perfect PDF
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Open local HTML file
        file_uri = f"file:///{os.path.abspath(temp_html).replace(chr(92), '/')}"
        page.goto(file_uri)
        
        # Print to PDF
        pdf_path = "RAM_SENTINEL_OPERATIONAL_ANALYSIS.pdf"
        page.pdf(path=pdf_path, format="A4", print_background=True, margin={"top": "2cm", "bottom": "2cm", "left": "2cm", "right": "2cm"})
        browser.close()
        
    print(f"Successfully generated: {pdf_path}")
    
    # Cleanup temp file
    if os.path.exists(temp_html):
        os.remove(temp_html)

if __name__ == '__main__':
    create_pdf()
