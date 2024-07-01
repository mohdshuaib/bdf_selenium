from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import zipfile
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from datetime import datetime
class CoyoteAccelerator(Accelerator):
    display_name = "POD Backup Downloader"
    group_name = "Coyote Logistics"
    start_url = "https://go.coyote.com/"
    input_display_names = {'product_numbers': 'Enter PRO Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> POD Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Please note the PRO# should only include the values expected, for example, SAP may include "PRO123456 SL34567". Instead, only input 123456, because that is how this portal works.</p>
        <br>
        <p><strong>Vendor Code:</strong> COYO</p>
        <p><strong>Vendor Name:</strong> Coyote Logistics</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://connect.coyote.com/#">https://connect.coyote.com/#</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 6900000094</p>
        <p><strong>SAP Account Name:</strong> COYOTE LOGISTICS</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, product_numbers: list[str]) -> str:
        if len(product_numbers) < 20:
            wait = WebDriverWait(self.driver, 30)
            await self.info('Starting Accelerator...')
            async with self.authenticator() as auth:
                current_date = datetime.now()
                formatted_date = current_date.strftime("%m%d%Y")
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
                    username_element.clear()
                    username_element.send_keys(username)
    
                    password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]')))
                    password_element.clear()
                    password_element.send_keys(password)
    
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                    try:
                        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[text() = "Accept Cookies"]'))).click()
                    except TimeoutException:
                        self.log.debug('cookies already accepted')
                    try:
                        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[text() = "My Shipments"]')))
                        await self.info("Great! We're logged in. Let's proceed.")
                    except TimeoutException:
                        await self.error('Login failed. Please try again.')
                        return
            await self.info("Please wait, we're processing the request...")
            WebDriverWait(self.driver, 30).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.info('Searching the portal…')
            try:
                WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[text() = "My Shipments"]')))
            except TimeoutException:
                await self.error('404 Page Not Found, please try again...')
                return
            
            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            
            for invoice_number in remove_duplicates_and_blanks(product_numbers):
                if len(str(invoice_number)) > 3:
                    await self.info(f'Processing:{invoice_number}')
                    self.driver.get("https://go.coyote.com/")
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    self.driver.get(f"https://go.coyote.com/load-details#{invoice_number}/documents")
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        delivery_receipt = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text()="Proof of Delivery"][@class="text-link hook--document text-left"]')))
                    except TimeoutException:
                        await self.info(f"Not Found:{invoice_number}")
                        continue
                    delivery_receipt.click()
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    await self.wait_for_output(lambda files: any('.tmp' not in file and '.crdownload' not in file for file in files))
                    # Need time sleep due to files are push by browser in time
                    await self.sleep(6)
                    for file in os.listdir(self.output_path):
                        if 'COYO_POD' in file and str(file).endswith('.pdf'):
                            pass
                        else:
                            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f'COYO_POD Backup_PRO_{invoice_number}.pdf'))
                            await self.info(f'Found #: {invoice_number}')
            
            zip_filename = os.path.join(self.output_path, f"COYO_Backups_{formatted_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if pdf_files:
                await self.info("Processing the data…")
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        else:
            await self.error('PRONum limit exceeds count 20.')

    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
            return False
        except Exception:
            return True
