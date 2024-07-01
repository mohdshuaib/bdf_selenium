from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator

class McKessonPricingBackupAccelerator(Accelerator):
    display_name = 'Pricing & Others Backup'
    group_name = 'McKesson'
    start_url = "https://connect.McKesson.com/portal/site/smo/template.LOGIN/"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Pricing Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this accelerator fetches documents using McKesson’s reference Document Number’s which start with prefixes “CC”, “LDC”, and “XP”, i.e. “CC220341948”, “LDC012111523”, “XP35692749”</p>
        <br>
        <p><strong>Vendor Code:</strong> MCKE</p>
        <p><strong>Vendor Name:</strong> McKesson Corp.</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://connect.mckesson.com/portal/site/smo/template.LOGIN/">https://connect.mckesson.com/portal/site/smo/template.LOGIN/</a></p>
        <p><strong>OTP Verification:</strong> Yes. OTP code sent to Email.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299320</p>
        <p><strong>SAP Account Name:</strong> MCKESSON CORP</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, document_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 50)
        async with self.authenticator() as auth:
            self.driver.maximize_window()
            try:
                WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
            except TimeoutException:
                self.log.debug('cookies button not found')
            try:
                cookies_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
                cookies_button.click()
            except TimeoutException:
                self.log.debug("TimeoutException while clicking cookies button")
            username_element = "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[1]/div[2]/span/input"
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            username_input = wait.until(EC.element_to_be_clickable((By.XPATH, username_element)))
            await self.info('Attempting to login…')
            username, password = await auth.userpass()
            username_input.send_keys(username)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            next_button.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[2]/div[2]/span/input")))
            password_input.send_keys(password)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            login_button.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                send_code_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                send_code_button.click()
            except TimeoutException:
                await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                return
            await self.info('Enter verification code(s) - OTP/MFA/Captcha…')
            try:
                WebDriverWait(self.driver, 40).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
                code = await auth.otp()
                otp_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
                otp_input.send_keys(code)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                verify_button.click()
                await self.info('Valid code entered.')
            except TimeoutException:
                await self.info('Invalid code entered. Please try again.')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            if not self.is_logged_in():
                await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                return
            await self.info("Great! We're logged in. Let's proceed.")
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 45).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/table/tbody/tr/td[3]/a")))
        except TimeoutException:
            self.log.debug('accound management button not founded..')
        self.driver.get('https://connect.mckesson.com/content/applications/supplier-management')
        await self.info('Searching the portal…')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, '//*[@title="applicationPage"]')))
        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[7]/td/div/table/tbody/tr/td/table[2]/tbody/tr/td/input")))
        checkbox.click()
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
        try:
            save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            self.driver.execute_script("arguments[0].click();", save_button)
        except TimeoutException:
            self.log.debug('save button not found...')
        self.log.debug('click on save button..')
        self.driver.execute_script("popup('payments')")
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[1]/td/div[2]/a[1]/div")))
        dropdown.click()

        def remove_duplicates_and_blanks(lst):
            seen = set()
            result = []
            for item in lst:
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        
        for document_number in remove_duplicates_and_blanks(document_numbers):
            if len(str(document_number)) > 4:
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                refrence_num = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@name='invoiceNo']")))
                refrence_num.clear()
                refrence_num.send_keys(document_number)
                self.log.debug(f'Entere the document number {document_number}')
                click_retrieve_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Retrieve']")))
                click_retrieve_button.click()
                self.log.debug('filled all required feild click retrieve button, waiting download button..')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                    self.driver.execute_script("arguments[0].click();", download_button)
                    refresh_token = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                        refresh_token = True
                    except TimeoutException:
                        await self.info("Not Found Invoice Num: {}".format(document_number))
                        refresh_token = False
                    if not refresh_token:
                        await self.info("Not Found Invoice Num: {}. Moving to next...".format(document_number))
                        continue
                except TimeoutException:
                    await self.info("Not Found Invoice Num: {}".format(document_number))
                    await self.info("Not Found Invoice Num: {}. Moving to next...".format(document_number))
                    continue
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.wait_for_output(lambda files: 'invoices.xls' in files)
                self.log.debug("[+] Stage Download output")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                for filename in os.listdir(self.output_path):
                    if filename.startswith('invoices'):
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'MCKE_Pricing_Others_Backup_{document_number}_file_{filename}'))
                await self.info(f"Found Invoice Num: {document_number}")
        count_invoices = len(document_numbers)
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"MCKE_Pricing_Others_Backup_{count_invoices}_{current_date}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xls')]
        if len(xl_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid invoices.')
            return
    
    def is_logged_in(self) -> bool:
        return 'https://connect.McKesson.com/portal' not in self.driver.current_url
