import os
import time
import base64
import argparse
import sys
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def print_banner():
    print("""
    ==========================================
    🚀 DRIVE-TO-PDF PRO: HIGH-FIDELITY CAPTURE
    ==========================================
    """)

def capture_high_fidelity_pdf(url, output_filename):
    print_banner()
    
    # 1. Setup Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Use a real user agent to look more human
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    pbar = tqdm(total=100, desc="Initializing Engine", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]')

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        pbar.update(20)
        pbar.set_description("Loading Document")

        # 2. Load the URL
        driver.get(url)
        
        # Wait for the document to actually render
        try:
            # We wait for a common element in the drive viewer
            WebDriverWait(driver, 20).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except TimeoutException:
            print("\n[!] Warning: Page load timed out. Attempting to proceed anyway...")

        pbar.update(30)
        pbar.set_description("Bypassing Security Overlays")
        time.sleep(3) # Extra time for complex rendering

        # 3. Inject the Unlocker Script
        unlock_script = """
        (function() {
            // Bypass Trusted Types if they exist
            if (window.trustedTypes && window.trustedTypes.createPolicy) {
                if (!window.trustedTypes.defaultPolicy) {
                    window.trustedTypes.createPolicy('default', {
                        createHTML: (string) => string,
                        createScriptURL: (string) => string,
                        createScript: (string) => string,
                    });
                }
            }

            // Remove the overlays that block selection/printing
            const selectors = [
                '.ndfHFb-c4SBA-ahS6Le', 
                '.ndfHFb-c4SBA-em79id', 
                '[class*="overlay"]', 
                '[class*="shield"]',
                '.ndfHFb-c4SBA-pIn97'
            ];
            selectors.forEach(s => {
                document.querySelectorAll(s).forEach(el => {
                    if (el.parentNode) el.parentNode.removeChild(el);
                });
            });
            
            // Force fonts and visibility using textContent (Safe from TrustedHTML)
            const style = document.createElement('style');
            style.textContent = `
                * { user-select: text !important; -webkit-user-select: text !important; } 
                @media print { 
                    body { visibility: visible !important; } 
                    .ndfHFb-c4SBA-au08id { display: block !important; }
                }
            `;
            document.head.appendChild(style);
            
            document.designMode = 'on';
            return "Unlocked";
        })();
        """
        driver.execute_script(unlock_script)
        pbar.update(20)
        pbar.set_description("Generating PDF Stream")

        # 4. CDP Print-to-PDF Command (The Master Key)
        # We use large margins or no margins to keep formatting perfect
        print_params = {
            "printBackground": True,
            "displayHeaderFooter": False,
            "preferCSSPageSize": True,
            "generateDocumentOutline": True
        }
        
        result = driver.execute_cdp_cmd("Page.printToPDF", print_params)
        pbar.update(20)
        pbar.set_description("Finalizing File")

        # 5. Write to File
        with open(output_filename, "wb") as f:
            f.write(base64.b64decode(result['data']))
        
        pbar.update(10)
        pbar.close()
        
        print(f"\n✅ SUCCESS: Document saved as '{output_filename}'")
        print(f"📂 Location: {os.path.abspath(output_filename)}")

    except Exception as e:
        pbar.close()
        print(f"\n❌ ERROR: {str(e)}")
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drive-to-PDF Pro: High-Fidelity Capture")
    parser.add_argument("url", help="The restricted Google Drive URL")
    parser.add_argument("-o", "--output", help="Output filename", default="Captured_Document.pdf")
    
    args = parser.parse_args()
    
    capture_high_fidelity_pdf(args.url, args.output)
