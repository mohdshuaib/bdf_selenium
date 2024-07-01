from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
from selenium.webdriver.common.keys import Keys
import pandas as pd

class WALBackupRLAccelerator(Accelerator):
    display_name = "Backup Downloader (RetailLink)"
    group_name = "Walmart Stores"
    start_url = "https://retaillink2.wal-mart.com/"
    input_display_names = {'invoices': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> TBD</p>
        <br>
        <p><strong>Vendor Code:</strong> WALM</p>
        <p><strong>Vendor Name:</strong> Walmart Stores</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://retaillink.login.wal-mart.com/">https://retaillink.login.wal-mart.com/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299388</p>
        <p><strong>SAP Account Name:</strong> WAL-MART STORES INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, invoices: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Starting Accelerator...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="uname"]')))
                username_input.clear()
                username_input.send_keys(username)
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="pwd"]')))
                password_input.clear()
                password_input.send_keys(password)
                submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="loginBtn"]')))
                submit.click()
                try:
                    varify_with_message_OTP = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Verify with Text Message"]')))
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
                varify_with_message_OTP.click()
                try:
                    otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                    await self.info('Success!, OTP is successfully Generated.')
                    await self.info('Enter verification code(s) - OTP/MFA/Captcha…')

                except TimeoutException:
                    await self.info('Failed!, OTP is Not Generated.')
                    return
                otp_input = await auth.otp()
                otp_input_field.clear()
                otp_input_field.send_keys(otp_input)
                submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
                submit_otp.click()
                await self.info('Please wait!, validating OTP.')
                await self.sleep(8)
                attempts = 1
                while "/mfa?" in self.driver.current_url:
                    await self.info(f'OTP, Attemp - {attempts}/5.')
                    if attempts >= 5:
                        await self.error(f'Failed to submit OTP after {attempts} attempts')
                        return
                    otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                    otp_input_field.clear()
                    for i in range(1, 20):
                        otp_input_field.send_keys(Keys.BACKSPACE)
                    otp_input = await auth.otp()
                    otp_input_field.send_keys(otp_input)
                    submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
                    submit_otp.click()
                    await self.sleep(8)
                    attempts += 1
                try:
                    WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get('https://retaillink2.wal-mart.com/apis/ChecksSearch.aspx')
                    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "MainContent_ddlVendor")])')))
                    await self.info("Great! We're logged in. Let's proceed.")
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
        await self.info("Please wait, we're processing the request...")
        await self.sleep(6)
        try:
            await self.info('Checking Session if Required OTP ?...')
            varify_with_message_OTP = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Verify with Text Message"]')))
            varify_with_message_OTP.click()
        except TimeoutException:
            await self.info('Recalling session, No need credentials')
        await self.sleep(6)
        attempts = 1
        while "/mfa?" in self.driver.current_url:
            await self.info(f'Need OTP, with  Attemp - {attempts}/5.')
            if attempts >= 5:
                await self.error(f'Failed to submit OTP after {attempts} attempts')
                return
            try:
                otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                await self.info('Success!, OTP is successfully Generated.')
            except TimeoutException:
                await self.info('Failed!, OTP is Not Generated.')
                return
            otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
            otp_input_field.clear()
            for i in range(1, 20):
                otp_input_field.send_keys(Keys.BACKSPACE)
            otp_input = await auth.otp()
            otp_input_field.send_keys(otp_input)
            submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
            submit_otp.click()
            await self.sleep(8)
            attempts += 1
        WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        await self.info('Searching the portal…')

        def remove_duplicates_and_blanks(lst):
            seen = set()
            result = []
            for item in lst:
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
            
        for invoice in remove_duplicates_and_blanks(invoices):
            if len(str(invoice)) > 4:
                await self.info(f'Processing: {invoice}')
                self.driver.get('https://retaillink2.wal-mart.com/apis/ClaimSearch.aspx')
                await self.sleep(4)
                drop_doown = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "MainContent_ddlVendor")])')))
                drop_doown.click()
                select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='051300 - BEIERSDORF INC (US)']")))
                select_vendor.click()
                invoice_field = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "MainContent_txtInvoiceNbr")])')))
                invoice_field.clear()
                invoice_field.send_keys(invoice)
                submit_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@name, "MainContent$btnSearch")])')))
                submit_invoice.click()
                try:
                    invoice_element = wait.until(EC.element_to_be_clickable((By.XPATH, f"//label[text() = '00000{invoice}']")))
                    invoice_element.click()
                except TimeoutException:
                    await self.info(f'Not Found: {invoice}')
                    continue
                print_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Print Preview"]')))
                print_button.click()
                await self.sleep(3)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                data_frame = pd.read_html(self.driver.page_source.encode('utf-8'))
                data_frame_full = pd.DataFrame()
                
                for i in range(0, len(data_frame)):
                    df = data_frame[i]
                    data_frame_full = pd.concat([data_frame_full, df], ignore_index=True)
                for i in data_frame_full.columns:
                    if len(data_frame_full[i]) == 0:
                        del data_frame_full[i]
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[-1])
                data_frame_full.to_csv(os.path.join(self.output_path, f'WALM_RL_Backup_Invoice_{invoice}.csv'), index=False)
                await self.info(f'Found: {invoice}')
        all_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
        if all_files:
            await self.info("Processing the data…")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"WALM-RL_Backup- {formatted_date}")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for down_file in all_files:
                    down_file_path = os.path.join(self.output_path, down_file)
                    zipf.write(down_file_path, arcname=down_file)
            await self.info("Success! Please click 'Download' to receive files.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        
    def is_logged_in(self) -> bool:
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="uname"]')))
            return False
        except Exception:
            return True
