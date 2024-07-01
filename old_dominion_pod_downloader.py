from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import zipfile
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime
class OldDominationAccelerator(Accelerator):
    display_name = "POD Backup Downloader"
    group_name = "Old Dominion Freight"
    start_url = "https://www.odfl.com/"
    input_display_names = {'product_numbers': 'Enter PRO Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> POD Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Please note the PRO# should only include the values expected, for example, SAP may include "PRO123456 SL34567". Instead, only input 123456, because that is how this portal works.</p>
        <br>
        <p><strong>Vendor Code:</strong> ODFL</p>
        <p><strong>Vendor Name:</strong> Old Dominion Freight</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://www.odfl.com/ODFL4meDashboard/index.faces">https://www.odfl.com/ODFL4meDashboard/index.faces</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 6900000068</p>
        <p><strong>SAP Account Name:</strong> OLD DOMINION FREIGHT LINE</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, product_numbers: list[str]) -> str:
        await self.info('Starting Accelerator...')
        if len(product_numbers) < 20:
            wait = WebDriverWait(self.driver, 30)
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    need_login = False
                    try:
                        username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
                        need_login = True
                    except TimeoutException:
                        need_login = False
                    if not need_login:
                        try:
                            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="logIn"][@tabindex="0"]')))
                            login_button.click()
                            await self.sleep(5)
                            need_login = True
                        except TimeoutException:
                            self.log.debug('login button not found...')
                    if need_login:
                        await self.info('Attempting to login…')
                        username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
                        username, password = await auth.userpass()
                        username_element.clear()
                        username_element.send_keys(username)
                        password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]')))
                        password_element.clear()
                        password_element.send_keys(password)
                        submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                        submit_login.click()
                        try:
                            wait.until(EC.element_to_be_clickable((By.XPATH, f'//label[text() = "{username}"]')))
                            await self.info("Great! We're logged in. Let's proceed.")
                        except TimeoutException:
                            await self.error('Login failed. Please try again.')
                            return
            await self.info("Please wait, we're processing the request...")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
            except TimeoutException:
                self.log.debug("No Need to Click on cokies Button")
            try:
                WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Close"][@class="_pendo-close-guide"]'))).click()
            except TimeoutException:
                self.log.debug("No Need to Close popup")
            await self.info('Searching the portal…')

            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            
            self.driver.get('https://www.odfl.com/us/en/tools/shipping-documents.html?proNumber=&docType=Delivery%20Receipt')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.sleep(5)

            for invoice_number in remove_duplicates_and_blanks(product_numbers):
                invoice_number = str(invoice_number).strip()
                await self.info(f'Processing:{invoice_number}')
                enter_pro = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@placeholder="Enter a Pro Number"]')))
                enter_pro.clear()
                enter_pro.send_keys(invoice_number)
                for _ in range(5):
                    try:
                        supplier = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, "//*[text()='View'][@type='button']"))
                        )
                        try:
                            supplier.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", supplier)
                        break
                    except StaleElementReferenceException:
                        continue
                await self.sleep(5)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    delivery_receipt = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="messageDisplay__section--description"]')))
                    if 'No Result found' in delivery_receipt.text:
                        await self.info(f"Not Found: {invoice_number}")
                        continue
                except TimeoutException:
                    self.log.info(f"Found: {invoice_number}")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')

                if not os.path.isfile(os.path.join(self.output_path, 'download.pdf')):
                    self.log.debug("Checking PDF Download ...")
                    self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.ID, 'pdfID'))))
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="open-button"]'))).click()
                await self.sleep(2)
                if not os.path.isfile(os.path.join(self.output_path, 'download.pdf')):
                    self.log.debug("Checking PDF Download ...")
                    self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.ID, 'pdfID'))))
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="open-button"]'))).click()
                os.rename(os.path.join(self.output_path, 'download.pdf'), os.path.join(self.output_path, f'ODFL_POD Backup_PRO_{invoice_number}.pdf'))
                await self.info(f"Found #: {invoice_number}")
                self.driver.switch_to.default_content()
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"ODFL_POD Backups_{formatted_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            await self.info("Processing...")
            if pdf_files:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        else:
            await self.error("PRONum limit exceeds count 20.")
            return
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        login_tocken = True
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="logIn"][@tabindex="0"]')))
            login_button.click()
            login_tocken = False
        except TimeoutException:
            self.log.debug("Running...")
        if 'odflb2c.b2clogin.com' not in self.driver.current_url:
            login_tocken = False
        return login_tocken
