from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.common.exceptions import TimeoutException
import pandas as pd
from selenium.webdriver import ActionChains
import os
import zipfile
from accelerators import Accelerator
from datetime import datetime
class CVSBackupAccelerator(Accelerator):
    display_name = "All Backup Downloader (ImageSilo)"
    group_name = "CVS Health"
    start_url = "https://login.imagesilo.com/Home/Index"
    input_display_names = {'invoice_numbers': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this accelerator accesses the Image Silo portal, for Remittance data use the accelerator for CVS AP Vendor.</p>
        <br>
        <p><strong>Vendor Code:</strong> CVSH</p>
        <p><strong>Vendor Name:</strong> CVS Health</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://login.imagesilo.com/Home/Index">https://login.imagesilo.com/Home/Index</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299360</p>
        <p><strong>SAP Account Name:</strong> CVS CORP</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Starting Accelerator...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                entity_id = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="txtEntityID"]')))
                entity_id.clear()
                entity_id.send_keys('6755')
                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="userName"]')))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="password"]')))
                password_element.clear()
                password_element.send_keys(password)

                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btnSubmitLogin"]')))
                submit_login.click()
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() ='WAREHOUSE/TELEPHONE/FEEDERS10']")))
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
                if not self.is_logged_in():
                    await self.error('Login failed. Please try again.')
                    return
                await self.info("Great! We're logged in. Let's proceed.")
        await self.info("Please wait, we're processing the request...")
        warehouse = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() ='WAREHOUSE/TELEPHONE/FEEDERS10']")))
        warehouse.click()
        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        
        def remove_duplicates_and_blanks(lst):
            seen = set()
            result = []
            for item in lst:
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
            
        for invoice_number in remove_duplicates_and_blanks(invoice_numbers):
            if len(invoice_number) > 5:
                await self.info(f'Processing:{invoice_number}')
                invoice_number = invoice_number.strip()
                invoice_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="INVOICE NUMBER"]')))
                invoice_input.clear()
                invoice_input.send_keys(invoice_number)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"][@value="Search"]'))).click()
                WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if '0' == wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/div/div/div[2]/div[4]/ul/li[2]/span'))).text:
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="projectListsBreadCrumbItem"]//*[text()="Search"]'))).click()
                    await self.info(f"Not Found:{invoice_number}")
                    continue
                else:
                    source = wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[text() = "{invoice_number}"]')))
                    action = ActionChains(self.driver)
                    action.double_click(source).perform()
                    try:
                        WebDriverWait(self.driver, 7).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Sales Invoice PDF']")))
                    except TimeoutException:
                        self.log.info('not available advanced filter')
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    element_text = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="divViewer"]'))).text
                    text_lines = element_text.split('\n')
                    df = pd.DataFrame({f'CVSH - IS Backups Downloader {date.today()}': text_lines})
                    df.to_csv(os.path.join(self.output_path, f"CVS-IS_Backup_Assign-{invoice_number}.csv"), index=False)
                    df.to_csv(os.path.join(self.output_path, f"CVS-IS_Backup_Assign-{invoice_number}.txt"), index=False)
                    await self.wait_for_output(lambda files: any(f"CVS-IS_Backup_Assign-{invoice_number}.csv" in file for file in files))
                    await self.wait_for_output(lambda files: any(f"CVS-IS_Backup_Assign-{invoice_number}.txt" in file for file in files))
                    await self.info(f"Found #:{invoice_number}")
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="projectListsBreadCrumbItem"]//*[text()="Search"]'))).click()
        txt_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv') or file.endswith('.txt')]
        if txt_files:
            await self.info("Processing the data…")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"CVSH - IS Backups Downloader {formatted_date}")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for txt_file in txt_files:
                    txt_file_path = os.path.join(self.output_path, txt_file)
                    zipf.write(txt_file_path, arcname=txt_file)
            self.info("Success! Please click 'Download' to receive files.")
            return f'{zip_filename}.zip'
        await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
        return
       
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="userName"]')))
            return False
        except Exception:
            return True
