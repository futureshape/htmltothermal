from playwright.sync_api import sync_playwright
import os, tempfile, logging
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/print', methods=['POST'])
def print_html():
    try:
        html_content = request.data.decode('utf-8')
        
        temp_file_html = tempfile.NamedTemporaryFile(delete=False, suffix='.html')
        temp_file_html.close()
        with open(temp_file_html.name, 'w') as f:
            f.write(html_content)
        logging.info(f"Written HTML into: {temp_file_html.name}")

        temp_file_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        temp_file_img.close()
        logging.info(f"Created image file: {temp_file_img.name}")
 
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 384, "height": 500})
            page.goto("file://" + os.path.abspath(temp_file_html.name))

            logging.info(f"Loaded page with title: {page.title()}")

            page.screenshot(path=temp_file_img.name, full_page=True)
            browser.close()

        preview_only_param = request.args.get('preview_only', 'false').lower() == 'true'
        
        if not preview_only_param:
            os.system(f"cd Cat-Printer; python3 printer.py -e 0.7 -q 1 -c image {os.path.abspath(temp_file_img.name)}")

        # Send the image file back as a response
        return send_file(temp_file_img.name, mimetype='image/png')

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(temp_file_html.name):
            os.remove(temp_file_html.name)
        if os.path.exists(temp_file_img.name):
            os.remove(temp_file_img.name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)