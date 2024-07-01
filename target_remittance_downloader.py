from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator

class TargetRemittanceAccelerator(Accelerator):
    display_name = 'Target Remittance Downloader'
    group_name = 'Target'
    start_url = 'https://partnersonline.com'
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> TARG</p>
        <p><strong>Vendor Name:</strong> Target Stores</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://www.partnersonline.com">https://www.partnersonline.com</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299373</p>
        <p><strong>SAP Account Name:</strong> TARGET STORES INC</p><br>
    </div>"""
    vendor_info = ''

    async def run(self) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Logging in...')
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div/div[1]/div/input")))
                username_input.send_keys(username)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.info('username inserted...')
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div/div[2]/div/input")))
                password_input.send_keys(password)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.info('Password inserted...')
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="submit-button"]/p')))
                login_button.click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    sms_Button = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@id'root']/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div/button[1]/span[1]/div/div/div[2]")))
                except TimeoutException:
                    self.log.debug("sms button not found..")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    sms_Button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id'root']/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div/button[1]/span[1]/div/div/div[2]")))
                    sms_Button.click()
                except TimeoutException:
                    self.log.debug("sms button not found..")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                otp = await auth.otp()
                otp_send = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div/div[2]/div/input")))
                otp_send.send_keys(otp)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div/form/div/div[2]/div/div/div")))
                login_button.click()
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info('Great! You’ve successfully logged into the targeted portal.')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')

            try:
                trust_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[1]/div[2]/div/div/form/div/div[1]/div/div/div/div[2]/div[3]/button[1]/span[1]")))
                trust_button.click()
            except TimeoutException:
                self.log.debug('Trust popup button not found..')
            app_reports = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/header/div/div[2]/a[2]")))
            app_reports.click()
            await self.info('click on app report...')
            try:
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[6]/div/div/div/div/div/div[2]/div/div/div[2]/div/div/ul/div[1]/div[1]/div/a/span/h3")))
            except TimeoutException:
                self.log.debug('accoun paybale element not found.')
            self.driver.get("https://greenfield.partnersonline.com/dashboard/12921")
            try:
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable(("By.XPATH, /html/body/div[1]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[1]/div/div/div[1]/div[2]/div[1]/div/div[3]")))
            except TimeoutException:
                self.log.debug('accoun paybale element not found.')
            self.driver.get("https://greenfield.partnersonline.com/card/598925/")
            await self.info("loading greenfield url...")
            Payment_Date = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div/div/div/div/div/div[3]/div/div/div[1]/div/div/div[1]/div[2]/div[1]/div/div[3]")))
            Payment_Date.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            three_dot = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div[2]/div/div/div/div/div/header/div/div/div[2]/div/div/button[2]/span")))
            three_dot.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            drop_down = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/ul/nav[1]/div/div[2]/span")))
            drop_down.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            export_csv = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[3]/ul/nav[1]/div[2]/div/div/ul/a/div/div/span")))
            export_csv.click()
            await self.wait_for_output(lambda files: 'Payment Information Details.csv' in files)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            for filename in os.listdir(self.output_path):
                if filename.startswith('Payment Information Details'):
                    os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'Target_Remittance_file_{filename}'))
            await self.info("this Target_Remittance data is being Processed")
            current_date = datetime.today().strftime('%Y%m%d')
            zip_filename = os.path.join(self.output_path, f"Target_Remittance{current_date}")
            xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
            if len(xl_files) == 1:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for xl_file in xl_files:
                        xl_file_path = os.path.join(self.output_path, xl_file)
                        zipf.write(xl_file_path, arcname=xl_file)
                await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Invalid! Not found. Please try again.')
                return

    def is_logged_in(self) -> bool:
        return 'logonservices.oauth.iam.partnersonline.com' not in self.driver.current_url