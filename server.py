from flask import Flask, request, send_file, jsonify, send_from_directory, abort
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import os
import tempfile
import logging
from escpos.printer import Network

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the directory to serve files from
SERVE_DIRECTORY = '/'

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
            page = browser.new_page(viewport={"width": 576, "height": 500})
            page.goto("file://" + os.path.abspath(temp_file_html.name))

            # Inject custom CSS from default-styles.css
            css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default-styles.css')
            if os.path.exists(css_path):
                with open(css_path, 'r') as css_file:
                    custom_css = css_file.read()
                page.add_style_tag(content=custom_css)
                logging.info(f"Injected custom CSS from {css_path}")
            else:
                logging.warning(f"default-styles.css not found at {css_path}")

            logging.info(f"Loaded page with title: {page.title()}")

            page.screenshot(path=temp_file_img.name, full_page=True)
            browser.close()

        preview_only_param = request.args.get('preview_only', 'false').lower() == 'true'
        
        if not preview_only_param:
            printer = Network("192.168.1.22") # TODO: make configurable
            printer.image(os.path.abspath(temp_file_img.name))
            printer.print_and_feed(5)
            printer.close()

        # Send the image file back as a response
        return send_file(temp_file_img.name, mimetype='image/png')

    except Exception as e:
        logging.exception("Error while converting and printing")
        return jsonify({'error': str(e)}), 500

    finally:
        if os.path.exists(temp_file_html.name):
            os.remove(temp_file_html.name)
        if os.path.exists(temp_file_img.name):
            os.remove(temp_file_img.name)

# Add a new route to serve index.html on GET /
@app.route('/', methods=['GET'])
def serve_index():
    try:
        return send_from_directory(SERVE_DIRECTORY, 'index.html')
    except FileNotFoundError:
        abort(404)

@app.route('/<path:filename>', methods=['GET'])
def serve_files(filename):
    try:
        return send_from_directory(SERVE_DIRECTORY, filename)
    except FileNotFoundError:
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7777)
