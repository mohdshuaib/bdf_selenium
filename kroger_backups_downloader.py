from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator

class KrogerOSDBackupsAccelerator(Accelerator):
    display_name = 'OSD Backups Downloader'
    group_name = 'Kroger'
    input_display_names = {'invoice_numbers': 'InvoiceNUM'}
    start_url = "https://partnerpass.krogerapps.com/vendorsso/dashboard"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> The process to download OSD backups requires special treatment. Please ensure the Assignment #s entered follow the typical shortage format of "XXXXXXXXXX-C" or "-CM", ex: 9079123456-CM or 9079654321-C</p>
        <br>
        <p><strong>Vendor Code:</strong> KROG</p>
        <p><strong>Vendor Name:</strong> Kroger Company</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://partnerpass.krogerapps.com/">https://partnerpass.krogerapps.com/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from OKTA Verify App.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299335</p>
        <p><strong>SAP Account Name:</strong> KROGER CO</p><br>
    </div>"""
    vendor_info = ''

    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            await self.info('Starting Accelerator')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_element = "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[3]/div/div[2]/span/input"
                try:
                    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, username_element)))
                    username_input.clear()
                    username_input.send_keys(username)
                except TimeoutException:
                    self.log.debug('username element not found.')
                    return
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='form19']/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", next_button)
                except TimeoutException:
                    self.log.debug('next button not found.')
                try:
                    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                    password_input.clear()
                    password_input.send_keys(password)
                except TimeoutException:
                    self.log.debug('password input element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    verify_password = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", verify_password)
                except TimeoutException:
                    self.log.debug('verify password element not found')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    select_octa_push = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[1]/div[2]/div[2]/a")))
                    self.driver.execute_script("arguments[0].click();", select_octa_push)
                except TimeoutException:
                    self.log.debug('select octa push element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.info('Enter verification code(s) - OTP/MFA/Captcha…')
                try:
                    code = await auth.otp()
                    octa_code = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                    octa_code.send_keys(code)
                    verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", verify_button)
                    await self.info('Valid code entered.')
                except TimeoutException:
                    await self.info('Invalid code entered. Please try again.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                self.log.debug('Please wait, verifying the OTP code.')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
        except TimeoutException:
            self.log.debug('popup not found...')
        if '/vendorsso/dashboard' in self.driver.current_url:
            await self.info("Great! You've successfully logged in. Let's proceed...")
            self.driver.get("https://partnerpass.lavante.com/sim/supplierDashboard.lvp")
            self.log.debug('levante page is Loaded  please wait.')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            self.driver.get('https://partnerpass.lavante.com/sim/supplierInvoiceSearchResult.lvp#search')
            await self.info('Searching the portal…')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            
            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            for invoice_number in remove_duplicates_and_blanks(invoice_numbers):
                if len(str(invoice_number)) > 9:
                    actual_invoice = str(invoice_number)[:10]
                    try:
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="invoiceNumber"]')))
                    except TimeoutException:
                        self.log.debug('popup not found...')
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        fill_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/div[3]/div/div[1]/div/div[4]/div[1]/form/div/div[3]/div[2]/input')))
                        fill_invoice.clear()
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                        fill_invoice.send_keys(actual_invoice)
                    except TimeoutException:
                        fill_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/div[3]/div/div[1]/div/div[4]/div[1]/form/div/div[3]/div[2]/input')))
                        fill_invoice.clear()
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                        fill_invoice.send_keys(actual_invoice)
                    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="invoiceSearch"]')))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                    self.driver.execute_script("arguments[0].click();", search_button)
                    await self.info(f'Found: {invoice_number}')
                    try:
                        iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
                        self.driver.switch_to.frame(iframe_element)
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    except TimeoutException:
                        await self.info(f'Not Found: {invoice_number}')
                        continue
                    try:
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/div/div[4]/div/div/table/tbody/tr[1]/td[4]/a")))
                    except TimeoutException:
                        self.log.debug('export button not found...')
                    try:
                        click_on_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[@title='{actual_invoice}']")))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_invoice)
                        self.driver.execute_script("arguments[0].click();", click_on_invoice)
                    except TimeoutException:
                        await self.info(f'Not Found: {invoice_number}')
                        continue
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    more_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="button-action-bar"]/div[3]/button')))
                    self.driver.execute_script("arguments[0].click();", more_option)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    export_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                    except TimeoutException:
                        self.log.debug('export button not found...')
                    self.driver.execute_script("arguments[0].click();", export_button)
                    await self.sleep(3)
                    refresh_token = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                        refresh_token = True
                    except TimeoutException:
                        await self.info("Not Found:{}".format(invoice_number))
                        refresh_token = False
                    if not refresh_token:
                        await self.error("Not found:{}. Moving to next...".format(invoice_number))
                        continue
                    click_on_back = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/div[1]/div[1]/a")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_back)
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/div[1]/div[1]/a")))
                    try:
                        self.driver.execute_script("arguments[0].click();", click_on_back)
                    except TimeoutException:
                        self.log.debug('back button not found.')
                    click_on_clear = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_supplier_form"]/div/div[16]/input[1]')))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_clear)
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_supplier_form"]/div/div[16]/input[1]')))
                    try:
                        self.driver.execute_script("arguments[0].click();", click_on_clear)
                    except TimeoutException:
                        self.log.debug('back button not found.')
                    self.driver.switch_to.default_content()
                    self.log.debug("[+] Stage Download output")
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    for filename in os.listdir(self.output_path):
                        if filename.endswith('.pdf'):
                            new_filename = f'KROG_Backup_{invoice_number}.pdf'
                            original_file = os.path.join(self.output_path, filename)
                            new_file = os.path.join(self.output_path, new_filename)
                            if not os.path.exists(new_file):
                                os.rename(original_file, new_file)
                            else:
                                self.log.debug(f"File {new_filename} already exists. Skipping rename.")
            await self.info('processing.....')
            count_invoices = len(invoice_numbers)
            current_date = datetime.today().strftime('%Y%m%d')
            zip_filename = os.path.join(self.output_path, f"KROG_OSD_Backups_Downloader_{count_invoices}_{current_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if len(pdf_files) > 0:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
                return f'{zip_filename}.zip'
            else:
                await self.error('Invalid! Not found. Please try again with valid invoices.')
                return
        else:
            await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
            return

    def is_logged_in(self) -> bool:
        return "https://okta.supplier-prod.kroger.com/oauth2/" in self.driver.current_url
