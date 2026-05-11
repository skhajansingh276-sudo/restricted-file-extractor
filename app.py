import os
import time
import re
import requests
import img2pdf
import threading
import uuid
from flask import Flask, render_template, request, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

app = Flask(__name__)

# Cloud-friendly Configuration
# Vercel and other cloud providers only allow writing to /tmp
OUTPUT_FOLDER = "/tmp" if os.name != 'nt' else "outputs"
if not os.path.exists(OUTPUT_FOLDER) and os.name == 'nt':
    os.makedirs(OUTPUT_FOLDER)

# Global status tracker
jobs = {}

def drive_pdf_extractor(url, job_id):
    jobs[job_id] = {"status": "Starting Engine...", "progress": 10}
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    # Cloud environments often don't have Chrome in standard paths
    # This might still fail on Vercel without a custom Buildpack
    os.environ['WDM_LOCAL'] = '1'
    os.environ['WDM_PATH'] = OUTPUT_FOLDER

    driver = None
    try:
        jobs[job_id]["status"] = "Connecting to Google Drive..."
        jobs[job_id]["progress"] = 20
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)

        driver.execute_script("""
            if (window.trustedTypes && window.trustedTypes.createPolicy) {
                if (!window.trustedTypes.defaultPolicy) {
                    window.trustedTypes.createPolicy('default', {
                        createHTML: (string) => string,
                        createScriptURL: (string) => string,
                        createScript: (string) => string,
                    });
                }
            }
        """)

        time.sleep(5)
        jobs[job_id]["status"] = "Rendering document pages..."
        jobs[job_id]["progress"] = 40

        for i in range(1, 15): 
            driver.execute_script(f"window.scrollTo(0, {i} * 1200);")
            time.sleep(1)
            jobs[job_id]["progress"] = 40 + (i * 2)

        jobs[job_id]["status"] = "Harvesting high-res assets..."
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        
        page_map = {}
        for img in img_elements:
            for attr in ["src", "data-src"]:
                url_val = img.get_attribute(attr)
                if url_val and ("viewer/img" in url_val or "drive-viewer" in url_val):
                    page_num_match = re.search(r"page=(\d+)", url_val)
                    if page_num_match:
                        page_num = int(page_num_match.group(1))
                        clean_url = re.sub(r"&[whs]=\d+", "", url_val)
                        clean_url = re.sub(r"=s\d+", "=s4000", clean_url) 
                        if page_num not in page_map:
                            page_map[page_num] = clean_url

        if not page_map:
            jobs[job_id]["status"] = "Error: No pages found. Check link permissions."
            return

        sorted_pages = sorted(page_map.keys())
        image_urls = [page_map[p] for p in sorted_pages]
        
        jobs[job_id]["status"] = f"Downloading {len(image_urls)} pages..."
        image_data_list = []
        for i, img_url in enumerate(image_urls):
            response = requests.get(img_url)
            if response.status_code == 200:
                image_data_list.append(response.content)
            jobs[job_id]["progress"] = 70 + int((i / len(image_urls)) * 20)

        jobs[job_id]["status"] = "Reconstructing PDF..."
        output_path = os.path.join(OUTPUT_FOLDER, f"document_{job_id}.pdf")
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_data_list))
        
        jobs[job_id]["status"] = "Completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["file"] = f"document_{job_id}.pdf"

    except Exception as e:
        jobs[job_id]["status"] = f"Error: {str(e)}"
    finally:
        if driver:
            driver.quit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400
    
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "Queued", "progress": 0}
    
    thread = threading.Thread(target=drive_pdf_extractor, args=(url, job_id))
    thread.start()
    
    return jsonify({"job_id": job_id})

@app.route('/status/<job_id>')
def status(job_id):
    return jsonify(jobs.get(job_id, {"error": "Job not found"}))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    # Local run on port 5000, cloud uses environment port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
