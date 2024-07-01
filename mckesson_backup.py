from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import os
import zipfile
from accelerators import Accelerator
import pandas as pd

class McKessonOSDBackupAccelerator(Accelerator):
    display_name = 'OSD Backup'
    group_name = 'McKesson'
    start_url = "https://connect.McKesson.com/portal/site/smo/template.LOGIN/"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> OSD Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this accelerator fetches documents specifically for Shortages. Use McKesson’s Document Number’s which start with prefix Q, i.e. “Q9079269643”</p>
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
            data_downloaded = False
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
                try:
                    doc_type = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@title='Quantity DM']")))
                    doc_type.click()
                except TimeoutException:
                    self.log.debug("Document type 'Quantity DM' not found.")
                
                # Add a try-except block around table handling
                try:
                    table_data = pd.read_html(self.driver.page_source)[0]  # Assuming the table is the first one on the page
                    table_element = WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, '//*[@class="one"][@colspan="3"]'))).text
                except TimeoutException:
                    self.log.debug("Table element not found for document number: {}. Moving to next...".format(document_number))
                    await self.info("Data not found for document number: {}. Moving to next...".format(document_number))
                    continue
                # Skip the first 18 rows from the table_data
                table_data = table_data.iloc[18:]
                tab_mod = table_element.replace(' #', '')
                tab_mod = tab_mod.replace(' #', ': ')
                tab_mod = tab_mod.replace('DC#', 'DC')
                tab_mod = tab_mod.replace('#', ': ')
                tab_mod = tab_mod.replace('DC Name', ': DC_Name')
                tab_mod = tab_mod.replace('Debit Memo Amt', ': Debit_Memo_Amt')
                tab_mod = tab_mod.replace('DC ', ': DC: ')
                tab_mod = tab_mod.replace('PO ', ': PO : ')
                tab_mod = tab_mod.replace('Debit Memo Date', ': Debit_Memo_Date')
                tab_mod = tab_mod.replace('Invoice Date', ': Invoice_Date')
                tab_mod = tab_mod.replace('Deduct Date', ': Deduct_Date')
                tab_mod = tab_mod.replace('Text', ': Text')
                tab_mod = tab_mod.replace('\nPay Vendor', ': Pay Vendor: ')
                tab_mod = tab_mod.replace('\nDocument', ': Document : ')
                tab_mod = tab_mod.replace(': : :', ':')
                mode1 = tab_mod.split(': ')
                res_dict = {}
                for i in range(0, len(mode1), 2):
                    res_dict[mode1[i]] = mode1[i + 1]
                my_list = [res_dict]
                # Convert the list of dictionaries to a dataframe
                df = pd.DataFrame.from_dict(my_list)
                addon_columnlist = df.columns
                for col in addon_columnlist:
                    table_data[f'{col}'] = df[f'{col}'][0]
                table_data.to_csv(os.path.join(self.output_path, f'MCKE_OSD_Backup_{document_number}.csv'), index=False)
                if await self.wait_for_output(lambda files: any(file.startswith('MCKE_OSD_Backup_') and file.endswith('.csv') for file in files)):
                    await self.info(f'Found Invoice Num: {document_number}.')
                    data_downloaded = True
                else:
                    await self.info(f'Not Found Invoice Num: {document_number}.')
                if not data_downloaded:
                    await self.info(f'Not Found Invoice Num: {document_number}.')
                
                for _ in range(5):
                    try:
                        back_button = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@alt='Back']")))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", back_button)
                        self.driver.execute_script("arguments[0].click();", back_button)
                        self.log.debug("Back button clicked successfully.")
                        break
                    except StaleElementReferenceException:
                        self.log.debug("Attempt to click back button failed:")
                        continue
                    except Exception as e:
                        self.log.debug(f"Exception occurred while processing document number {document_number}: {e}")
                        await self.info(f"Exception occurred while processing document number {document_number}: {e}. Moving to next...")
                        continue
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        await self.info(f"Found Invoice Num: {document_number} ")
        count_invoices = len(document_numbers)
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"MCKE_OSD_Backup_{count_invoices}_{current_date}")
        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
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
    
    def is_logged_in(self) -> bool:
        return 'https://connect.McKesson.com/portal' not in self.driver.current_url
