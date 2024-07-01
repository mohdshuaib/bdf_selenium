from datetime import date, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import os
import zipfile
from accelerators import Accelerator
import pandas as pd

class McKessonPromoBackupAccelerator(Accelerator):
    display_name = 'Promotion Backup'
    group_name = 'McKesson'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    start_url = "https://connect.McKesson.com/portal/site/smo/template.LOGIN/"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Unsaleable Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this accelerator fetches Promotions data which is valuable to Beiersdorf, but does not directly impact the current workflows. Beiersdorf partners with a broker to manage Promotion deductions at this time. Use McKesson’s Document Number’s which contain the value “BEI”, i.e. “3343LBEIAL”</p>
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
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 50)
        async with self.authenticator() as auth:
            await self.info('Starting Accelerator')
            to_month, to_day, to_year = to_date.strftime("%m %d %Y").split()
            from_month, from_day, from_year = from_date.strftime("%m %d %Y").split()
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
        try:
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
        except TimeoutException:
            self.log.debug('save button not found..')
        try:
            save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            self.driver.execute_script("arguments[0].click();", save_button)
        except TimeoutException:
            self.log.debug('save button not found...')
        self.driver.execute_script("popup('promoinvoices')")
        dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[1]/td/div[4]/a[1]/div")))
        dropdown.click()
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        select_from_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='begDateMonth']")))
        select_from_month.send_keys(from_month)
        select_from_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='begDateDay']")))
        select_from_day.send_keys(from_day)
        select_from_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='begDateYear']")))
        select_from_year.send_keys(from_year)
        select_to_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='endDateMonth']")))
        select_to_month.send_keys(to_month)
        select_to_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='endDateDay']")))
        select_to_day.send_keys(to_day)
        select_to_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='endDateYear']")))
        select_to_year.send_keys(to_year)
        click_retrieve_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@alt='Retrieve']")))
        click_retrieve_button.click()
        await self.info(f'Found: {from_date} To {to_date} :')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        download_button_found = False
        try:
            for _ in range(5):
                try:
                    download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                    self.driver.execute_script("arguments[0].click();", download_button)
                    download_button_found = True
                    break
                except StaleElementReferenceException:
                    continue
        except TimeoutException:
            await self.info(f'Data not found with this {from_date} To {to_date} date range.')

        if download_button_found:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.wait_for_output(lambda files: any(file.startswith("invoices") for file in files))
            await self.info('Please Wait File is Downloading..')
        else:
            await self.info('Data not found with this date range.')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        for filename in os.listdir(self.output_path):
            if filename.startswith('invoices'):
                os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'MCKE_Promo_Backup_{from_date}_to_{to_date}_file_{filename}'))
                file_data = pd.read_csv(os.path.join(self.output_path, f'MCKE_Promo_Backup_{from_date}_to_{to_date}_file_{filename}'), sep='\t', lineterminator='\r')
                file_data = file_data.drop('Unnamed: 11', axis=1)
                file_data.to_excel(os.path.join(self.output_path, f'MCKE_Promo_Backup_{from_date}_to_{to_date}_file_Invoice.xlsx'), index=False)
                os.remove(os.path.join(self.output_path, f'MCKE_Promo_Backup_{from_date}_to_{to_date}_file_{filename}'))
            await self.info("McKesson Promo Backup data is being Processed")
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"MCKE_Promo_Backup{current_date}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xlsx')]
        if len(xl_files) == 1:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid Date Range.')
            return
    
    def is_logged_in(self) -> bool:
        return 'https://connect.McKesson.com/portal' not in self.driver.current_url
