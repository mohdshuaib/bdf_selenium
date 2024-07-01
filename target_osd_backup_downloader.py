from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import os
import zipfile
from accelerators import Accelerator

class TargetOSDAccelerator(Accelerator):
    display_name = 'Target OSD Backup downloader'
    group_name = 'Target'
    start_url = 'https://partnersonline.com'
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the common format for each reference numbers includes:
</p>
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

    async def run(self, document_numbers: list[str]) -> str:
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
            self.driver.get("https://apreports.partnersonline.com/")
            credit_debit = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/div[5]/div/nav/a")))
            credit_debit.click()
            vendor_dop_down = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/section/div/div/form/div/div[1]/div/div[1]/div/span/select")))
            vendor_dop_down.send_keys(Keys.END)
            for document_number in list(set(document_numbers)):
                if len(str(document_number)) > 7:
                    await self.info('f"trying for downloading:{document_number}')
                    input_document = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/section/div/div/form/div/div[1]/div/div[2]/div/input")))
                    input_document.send_keys(document_number)
                    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/section/div/div/form/div/div[1]/div/div[4]/button")))
                    submit_button.click()
                    export_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/section/div/div/form/div/div[4]/div/div/button")))
                    export_button.click()
                    export_inPdf = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div/section/div/div/form/div/div[4]/div/div/ul/li[2]/button")))
                    export_inPdf.click()
                    await self.info('f"waiting for downloading:{document_number}')
                    await self.wait_for_output(lambda files: 'Report.pdf' in files)
                    for filename in os.listdir(self.output_path):
                        if filename.startswith('Report'):
                            await self.info('trying to rename the file..')
                            os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'TARG_OSD_Backup_{document_number}file_{filename}'))
                        await self.info(f"TARG_OSD_Backup_ data is being Processed: {document_number}")
            count_invoices = len(document_numbers)
            current_date = datetime.today().strftime('%Y%m%d')
            zip_filename = os.path.join(self.output_path, f"TARG_OSD_Backup_{count_invoices}_{current_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if len(pdf_files) > 0:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Invalid! Not found. Please try again with valid invoices.')
                return

    def is_logged_in(self) -> bool:
        return 'logonservices.oauth.iam.partnersonline.com' not in self.driver.current_url
