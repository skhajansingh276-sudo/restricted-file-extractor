import requests
from bs4 import BeautifulSoup
import argparse
import re
import os
import sys

def transform_url(url):
    """
    Transforms a Google Drive or Google Docs URL to an accessible format.
    """
    # Pattern for Google Docs
    doc_match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
    if doc_match:
        doc_id = doc_match.group(1)
        return f"https://docs.google.com/document/d/{doc_id}/mobilebasic", doc_id, "doc"
    
    # Pattern for General Drive Files (PDF, TXT, etc)
    file_match = re.search(r"/file/d/([a-zA-Z0-9-_]+)", url)
    if file_match:
        file_id = file_match.group(1)
        # Direct download link can often bypass the "view only" UI restriction
        return f"https://drive.google.com/uc?export=download&id={file_id}", file_id, "file"
    
    raise ValueError("Invalid URL. Could not find a Document or File ID.")

def extract_text(url, url_type):
    """
    Fetches the content and extracts text based on file type.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"[*] Fetching: {url}")
    response = requests.get(url, headers=headers, stream=True)
    
    if response.status_code != 200:
        print(f"[!] Failed to fetch. Status code: {response.status_code}")
        return None

    if url_type == "doc":
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find('div', id='contents') or soup.find('body')
        if not content_div:
            return None
        return content_div.get_text(separator='\n').strip()
    
    elif url_type == "file":
        # For general files, we return the raw content (best for text files)
        # If it's a PDF, this will return binary, but we'll try to decode it
        try:
            return response.content.decode('utf-8', errors='ignore')
        except:
            return "[!] File appears to be binary (like a PDF or Image). The script currently extracts text from Docs and Text files."

def main():
    parser = argparse.ArgumentParser(description="Google Drive Read-Only Unlocker - Extract text from restricted Docs/Files.")
    parser.add_argument("url", help="The URL of the restricted Google Doc or File")
    parser.add_argument("-o", "--output", help="Output filename (optional)")
    
    args = parser.parse_args()
    
    try:
        target_url, item_id, url_type = transform_url(args.url)
        text = extract_text(target_url, url_type)
        
        if text:
            output_file = args.output if args.output else f"unlocked_{item_id}.txt"
            
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
            
            print(f"[+] Success! Content saved to: {output_file}")
            if len(text) > 100:
                print(f"[+] Preview: {text[:100]}...")
            else:
                print(f"[+] Content: {text}")
        else:
            print("[!] Extraction failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
