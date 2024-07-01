from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from accelerators import Accelerator
from datetime import datetime
import zipfile
import os


class CAndSBackupsAccelerator(Accelerator):
    display_name = 'Promotion Backups'
    group_name = 'C&S Wholesale Grocers'
    input_display_names = {'invoice_numbers': 'InvoiceNum'}
    start_url = r"https://websso.cswg.com/oam/server/obrareq.cgi?encquery%3DS3YmdXVDxozZJNsQ1kaD8B392xA2nxCvfyc%2FtcT%2FQDNtSHNThYBzZyOsekisHxh1TtAoTq5T%2Fqkkj1punHwCLvO1Vc9t1dLOxf18uM6KK2Xx4caNl0119iwgVNDT%2BrSt1mXxDH03RGaRnq1jLcgELO8W4gx%2BvQIIId5b1LUiRdc2PHPPtXfjXnRwoL6a5ucEfTSfJEUiC1qhZOAo2R3%2BzHR4D%2BCUcyvRgAD1rOa1dUauMR1fuJQc3aLXrp3hRR9nfgHrG3knZG0CkaXm1cLF9vdO%2BfZKuq408LrxsRc10lA%3D%20agentid%3Dvendorportal.cswg.com%20ver%3D1%20crmethod%3D2"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this operation only allows values in the format of:
- CLA00112233
- CLA11223344
- CLA22334455</p>
        <br>
        <p><strong>Vendor Code:</strong> CSWG</p>
        <p><strong>Vendor Name:</strong> C&S Wholesale Grocers</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://vendorportal.cswg.com">https://vendorportal.cswg.com</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299379</p>
        <p><strong>SAP Account Name:</strong> C & S WHOLESALE GROC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            await self.info('Running…')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="username"]')))
                username_input.clear()
                username_input.send_keys(username)
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="password"]')))
                password_input.clear()
                password_input.send_keys(password)
                submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_button.click()
                try:
                    acknowledge_popup_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pgl12"]')))
                    acknowledge_popup_button.click()
                except Exception:
                    self.log.debug("acknowledge_popup_button not found")
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! We're logged in. Let's proceed.")
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        self.driver.get('https://vendorportal.cswg.com/vip/faces/pages_tools/BillbackReport/OracleBillbackReport')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        tocken_frame = False

        def remove_duplicates_and_blanks(lst):
            seen = set()
            result = []
            for item in lst:
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        for invoice_number in remove_duplicates_and_blanks(invoice_numbers):
            if not invoice_number.startswith("CLA"):
                await self.error(f"Reference # must begin with 'CLA'. Skipping invoice: {invoice_number}")
                continue
            if tocken_frame:
                self.driver.switch_to.default_content()
            if len(str(invoice_number)) > 5:
                actual_invoice = invoice_number[:-3]
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                # self.driver.switch_to.default_content()
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '(//*[contains(@name, "biExecBinding1_iframe")])')))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                tocken_frame = True
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                enter_voucher = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[1]/td/div/table/tbody/tr/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[3]/table/tbody/tr/td/table/tbody/tr[2]/td/span/span/div/div[1]/input")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", enter_voucher)
                enter_voucher.clear()
                enter_voucher.send_keys(actual_invoice)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                for _ in range(5):
                    try:
                        apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[1]/td/div/table/tbody/tr/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[3]/td/input')))
                        apply_button.click()
                        break
                    except StaleElementReferenceException:
                        continue
                export_button_xpath = '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td[5]/a'
                export_button_visible = EC.visibility_of_element_located((By.XPATH, export_button_xpath))
                try:
                    wait.until(export_button_visible)
                except TimeoutException:
                    self.log.debug(f"Trying to find the export button for Invoice: {invoice_number}")
                    continue
                try:
                    export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    export_button.click()
                except StaleElementReferenceException:
                    await self.info(f"Not Found InvoiceNum: {invoice_number}")
                    try:
                        # Try to find and click the element again
                        export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                        wait.until(lambda driver: export_button.is_displayed() and export_button.is_enabled())
                        export_button.click()
                    except (StaleElementReferenceException, TimeoutException):
                        self.log.debug(f"Failed to click export button for InvoiceNum: {invoice_number}")
                        continue
                try:
                    click_excel = wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Excel 2007+')]")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_excel)
                    self.driver.execute_script("arguments[0].click();", click_excel)
                except TimeoutException:
                    self.log.debug('click excel not found, please try again')
                    continue
                await self.wait_for_output(lambda files: any(file.startswith("Vendor Billback Report") for file in files))
                try:
                    click_ok = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.masterToolbarTextButton.button[name="OK"]')))
                    click_ok.click()
                except TimeoutException:
                    self.log.debug("click_ok button not found ...")
                    continue
                self.driver.switch_to.default_content()
            for filename in os.listdir(self.output_path):
                if filename.startswith('Vendor Billback Report'):
                    try:
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'CSWG_Backup_AssignNum_{invoice_number}_file_{filename}'))
                    except TimeoutException:
                        self.log.debug("TimeoutException while renaming file or maybe file is not found")
            await self.info(f"Found Invoice Num: {invoice_number}")
        await self.info('Processing...')
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"CSWG_Backup Downloader_{current_date}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xlsx')]
        if len(xl_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid check creation date.')
            return
        
    def is_logged_in(self) -> bool:
        return 'https://websso.cswg.com/oam' not in self.driver.current_url
