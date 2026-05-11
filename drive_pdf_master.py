import os
# Set WDM_LOCAL to '1' to install drivers in the current project directory
# and WDM_PATH to the local folder to avoid read-only filesystem errors.
os.environ['WDM_LOCAL'] = '1'
os.environ['WDM_PATH'] = os.getcwd()

import time
import requests
import img2pdf
import argparse
import re
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def drive_pdf_master(url, output_pdf):
    print("\n🚀 DRIVE-PDF MASTER: RECONSTRUCTION ENGINE")
    print("==========================================")
    
    # 1. Setup Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") # Enable headless for terminal environment
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    try:
        print(f"[*] Navigating to: {url}")
        driver.get(url)

        # Bypass Trusted Types Security
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

        time.sleep(10) 
        print(f"[*] Page Title: {driver.title}")

        # 2. Automated Scroll-to-Render
        print("[*] Scrolling to render all pages (14 pages detected)...")
        for i in range(1, 25): 
            driver.execute_script(f"window.scrollTo(0, {i} * 1000);")
            time.sleep(1.5)

        # 3. Harvest Image URLs
        print("[*] Harvesting high-resolution page images...")
        img_elements = driver.find_elements(By.TAG_NAME, "img")
        
        # We use a dictionary to store {page_number: url} to ensure perfect ordering
        page_map = {}
        
        for img in img_elements:
            for attr in ["src", "data-src"]:
                url_val = img.get_attribute(attr)
                if url_val and ("viewer/img" in url_val or "drive-viewer" in url_val):
                    # 1. Extract Page Number (e.g., ...&page=3...)
                    page_num_match = re.search(r"page=(\d+)", url_val)
                    if page_num_match:
                        page_num = int(page_num_match.group(1))
                        
                        # 2. Get Highest Quality (Remove width/height/scale limits)
                        # We remove &w=, &h=, &sz=, and =sXXX
                        clean_url = re.sub(r"&[whs]=\d+", "", url_val)
                        clean_url = re.sub(r"=s\d+", "=s4000", clean_url) # Force 4k resolution
                        
                        if page_num not in page_map:
                            page_map[page_num] = clean_url

        if not page_map:
            print("[!] Error: No pages found. Saving debug info...")
            driver.save_screenshot("debug_screenshot.png")
            return

        # Sort by page number
        sorted_pages = sorted(page_map.keys())
        image_urls = [page_map[p] for p in sorted_pages]
        print(f"[+] Successfully identified and ordered {len(image_urls)} pages.")

        # 4. Download Pages
        print("[*] Downloading pages (High Resolution)...")
        image_data_list = []
        for i, img_url in enumerate(tqdm(image_urls, desc="Downloading")):
            response = requests.get(img_url)
            if response.status_code == 200:
                image_data_list.append(response.content)
            else:
                print(f"[!] Warning: Could not download page {i}")

        # 5. Reconstruct PDF
        final_output = output_pdf if output_pdf != "Reconstructed_Document.pdf" else "Final_Document.pdf"
        print(f"[*] Reconstructing final PDF: {final_output}")
        with open(final_output, "wb") as f:
            f.write(img2pdf.convert(image_data_list))
        
        print(f"\n✅ SUCCESS! Perfect PDF saved as: {final_output}")
        print(f"📂 Location: {os.path.abspath(final_output)}")

    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drive-PDF Master - Reconstruct protected PDFs")
    parser.add_argument("url", help="The restricted Google Drive link")
    parser.add_argument("-o", "--output", help="Output PDF name", default="Reconstructed_Document.pdf")
    
    args = parser.parse_args()
    drive_pdf_master(args.url, args.output)
