import os
import time
import re
import requests
import img2pdf
import threading
import uuid
from flask import Flask, render_template, request, send_file, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)

# Cloud-friendly Configuration
OUTPUT_FOLDER = "/tmp" 
BROWSERLESS_KEY = os.environ.get("BROWSERLESS_KEY")

jobs = {}

def drive_pdf_extractor(url, job_id):
    jobs[job_id] = {"status": "Starting Cloud Engine...", "progress": 10}
    
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    
    driver = None
    try:
        # If we have a Browserless key, use the remote browser (Vercel way)
        if BROWSERLESS_KEY:
            jobs[job_id]["status"] = "Connecting to Remote Browser..."
            browserless_url = f"https://chrome.browserless.io/webdriver?token={BROWSERLESS_KEY}"
            driver = webdriver.Remote(command_executor=browserless_url, options=chrome_options)
        else:
            # Local/Render way (will fail on Vercel without key)
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get(url)
        jobs[job_id]["progress"] = 20
        
        # Inject Trusted Types bypass
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
        jobs[job_id]["status"] = "Scrolling and rendering..."
        
        # Optimized scrolling for cloud
        for i in range(1, 12): 
            driver.execute_script(f"window.scrollTo(0, {i} * 1200);")
            time.sleep(1)
            jobs[job_id]["progress"] = 20 + (i * 3)

        img_elements = driver.find_elements(By.TAG_NAME, "img")
        page_map = {}
        for img in img_elements:
            url_val = img.get_attribute("src") or img.get_attribute("data-src")
            if url_val and ("viewer/img" in url_val or "drive-viewer" in url_val):
                page_match = re.search(r"page=(\d+)", url_val)
                if page_match:
                    p = int(page_match.group(1))
                    clean = re.sub(r"&[whs]=\d+", "", url_val)
                    clean = re.sub(r"=s\d+", "=s4000", clean)
                    if p not in page_map: page_map[p] = clean

        if not page_map:
            jobs[job_id]["status"] = "Error: Drive link protected or invalid."
            return

        image_data_list = []
        sorted_p = sorted(page_map.keys())
        jobs[job_id]["status"] = f"Downloading {len(sorted_p)} pages..."
        
        for i, p in enumerate(sorted_p):
            resp = requests.get(page_map[p])
            if resp.status_code == 200:
                image_data_list.append(resp.content)
            jobs[job_id]["progress"] = 60 + int((i/len(sorted_p))*30)

        output_path = os.path.join(OUTPUT_FOLDER, f"document_{job_id}.pdf")
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_data_list))
        
        jobs[job_id]["status"] = "Completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["file"] = f"document_{job_id}.pdf"

    except Exception as e:
        jobs[job_id]["status"] = f"Error: {str(e)}"
    finally:
        if driver: driver.quit()

@app.route('/')
def index(): return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract():
    url = request.form.get('url')
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "Queued", "progress": 0}
    threading.Thread(target=drive_pdf_extractor, args=(url, job_id)).start()
    return jsonify({"job_id": job_id})

@app.route('/status/<job_id>')
def status(job_id): return jsonify(jobs.get(job_id, {"error": "Not found"}))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(OUTPUT_FOLDER, filename), as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
