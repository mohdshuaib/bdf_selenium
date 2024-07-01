from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from datetime import date, datetime
import zipfile
import os
import pandas as pd
import numpy as np

class McKessonRemittanceAccelerator(Accelerator):
    display_name = 'Remittance Downloader'
    group_name = 'McKesson'
    start_url = "https://connect.mckesson.com/portal/site/smo/template.LOGIN/"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> MCKE</p>
        <p><strong>Vendor Name:</strong> McKesson Corp.</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://connect.mckesson.com/portal/site/smo/template.LOGIN/">https://connect.mckesson.com/portal/site/smo/template.LOGIN/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299320</p>
        <p><strong>SAP Account Name:</strong> MCKESSON CORP</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 45)
        delta = to_date - from_date
        if delta.days <= 365:
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
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
            try:
                save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
                self.driver.execute_script("arguments[0].click();", save_button)
            except TimeoutException:
                self.log.debug('save button not found...')
            self.driver.execute_script("popup('payments')")
            dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[1]/td/div[2]/a[2]/div")))
            dropdown.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            select_begin_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[1]")))
            select_begin_month.send_keys(from_month)
            select_begin_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[2]")))
            select_begin_day.send_keys(from_day)
            select_begin_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[3]")))
            select_begin_year.send_keys(from_year)
            select_last_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[1]")))
            select_last_month.send_keys(to_month)
            select_last_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[2]")))
            select_last_day.send_keys(to_day)
            select_last_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[3]")))
            select_last_year.send_keys(to_year)
            retrieve_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[6]/td/table/tbody/tr/td[1]/input")))
            retrieve_button.click()
            page_line = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dd"]/option[4]')))
            page_line.click()
            await self.info(f'Found Date(s): {from_date}-{to_date}:')
            WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.ID, "pnum")))
            WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.TAG_NAME, "option")))
            page_count_dropdown = self.driver.find_element(By.ID, "pnum")
            total_pages = len(page_count_dropdown.find_elements(By.TAG_NAME, "option"))
            await self.info('Processing the data…')
            for page_number in range(1, total_pages + 1):
                page_count_dropdown = self.driver.find_element(By.ID, "pnum")
                page_count_dropdown.find_element(By.CSS_SELECTOR, f"option[value='{page_number}']").click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr")))
                all_rows = self.driver.find_elements(By.XPATH, "/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr")
                counter = 1
                for row_index, row in enumerate(all_rows, start=1):
                    row_xpath = f"/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr[{row_index}]/td[1]/a"
                    row_element = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, row_xpath)))
                    try:
                        self.driver.execute_script("arguments[0].click();", row_element)
                    except TimeoutException:
                        self.log.debug('row eleemnt not found please try again')
                    self.log.debug('click on row element..')
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[2]")))
                    refresh_token = False
                    try:
                        click_on_download = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[2]")))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_download)
                        self.driver.execute_script("arguments[0].click();", click_on_download)
                        self.log.debug('click on download button..')
                        refresh_token = True
                    except TimeoutException:
                        self.log.debug("Download button not found")
                        refresh_token = False
                    if not refresh_token:
                        await self.log.error("Download button not clickable")
                        return
                    await self.wait_for_output(lambda files: any(file.startswith('000') and file.endswith('.xls') for file in files))
                    await self.sleep(2)
                    await self.info(f'Please wait file {counter} is downloading...')
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    counter += 1
                    try:
                        click_on_back = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[1]")))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_back)
                        self.driver.execute_script("arguments[0].click();", click_on_back)
                    except TimeoutException:
                        self.log.debug('back button is not found try again.')
                for filename in os.listdir(self.output_path):
                    if filename.startswith('000'):
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'MCKE_Remittance_{from_date}_{to_date}_file_{filename}'))
                        file_path = os.path.join(self.output_path, f'MCKE_Remittance_{from_date}_{to_date}_file_{filename}')
                        df_full = pd.read_csv(file_path, sep='\t', lineterminator='\r')
                        counter = 0
                        for detail in df_full.columns:
                            if counter == 1:
                                check = detail.split('\n')[0]
                                counter += 1
                            elif counter == 2:
                                date_value = detail.split('\n')[0]
                                counter += 1
                            elif counter == 3:
                                detail_refine = str(detail).replace('(', '')
                                ammount = str(detail_refine).replace(')', '')
                                counter += 1
                            else:
                                counter += 1
                        file_data = pd.read_csv(file_path, sep='\t', lineterminator='\r', skiprows=1)
                        file_data.fillna('', inplace=True)
                        extracted_col = file_data["Ref Date"]
                        enum_value = 0
                        values = [check, date_value, ammount]
                        for col in ['Check Number', 'Check date', 'Check Amount']:
                            file_data[f'{col}'] = values[enum_value]
                            enum_value += 1

                        def clean_value(value):
                            if pd.isna(value):
                                return value
                            value_str = str(value)
                            value_str = value_str.replace('$', '').replace('(', '').replace(')', '').replace(',', '')
                            return value_str
                        file_data['Shifted Amount'] = file_data['Net Amount'].apply(clean_value)
                        file_data['Shifted Amount'] = pd.to_numeric(file_data['Shifted Amount'], errors='coerce')
                        file_data['Ref #'] = file_data['Ref #'].astype(str)
                        columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                        for col in columns_addon:
                            file_data[f'{col}'] = ''
                        conditions = [
                            file_data['Shifted Amount'] < 0,
                            (file_data['Shifted Amount'] > 0) & (file_data['Ref #'].str.match(r'^\d{10}$', na=False)),
                            (file_data['Shifted Amount'] > 0) & (~file_data['Ref #'].str.match(r'^\d{10}$', na=False))
                        ]
                        choices = ['Deduction', 'Invoice Payment', 'Repayment']
                        file_data['BDF Record Type'] = np.select(conditions, choices, default='-')
                        tolerance_conditions = [
                            (file_data['BDF Record Type'] == 'Deduction') & (file_data['Shifted Amount'].abs() > 0) & (file_data['Shifted Amount'].abs() < 200),
                            (file_data['BDF Record Type'] == 'Deduction') & (file_data['Shifted Amount'].abs() > 200)]
                        tolerance_choices = ['UT', 'OT']
                        file_data['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                        file_data['Ref Date'] = pd.to_datetime(file_data['Ref Date'], format="%m-%d-%Y", errors='coerce')
                        file_data['BDF Expiry'] = file_data['Ref Date'] + pd.Timedelta(days=45)
                        file_data['BDF Record Type'] = file_data.apply(lambda row: 'Deduction' if any(c.isalpha() for c in row['Ref #']) else row['BDF Record Type'], axis=1)
                        await self.info('Data Transformation...')
                        reason_code_conditions = [
                            file_data['Ref #'].str.startswith('Q', na=False),
                            file_data['Ref #'].str.startswith('CC', na=False),
                            file_data['Ref #'].str.startswith('LDC', na=False),
                            file_data['Ref #'].str.startswith('XP', na=False),
                            file_data['Ref #'].str.startswith('M', na=False),
                            file_data['Ref #'].str.contains('BEI', case=False, na=False)
                        ]
                        reason_code_choices = ['101', '102', '102', '102', '105', '306']
                        reason_code_ID_choices = ["Quantity Difference", "Stock Return ", "Stock Return ", "Stock Return ", "Quality/Damaged Goods", "TTC Deduction - Invoice Missing"]
                        reason_code_description = ["SHORTAGE", "RETURNS", "RETURNS", "RETURNS", "UNSALEABLE", "COOP"]
                        file_data['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                        file_data['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                        file_data['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
                        file_data = file_data.drop('Shifted Amount', axis=1)
                        file_data = file_data.drop('Ref Date', axis=1)
                        file_data.fillna('', inplace=True)
                        file_data = file_data.iloc[:-1]
                        file_data = pd.concat([file_data, extracted_col.rename("Ref_Date")], axis=1)
                        final_data = file_data[[
                            '\nPO #', 'Ref #', 'Ref_Date', 'Ref Amount', 'Discount', 'Net Amount',
                            'Company Code', 'Due Date', 'Location', 'Line Text', 'Doc Type',
                            'Check Number', 'Check date', 'Check Amount', 'BDF Record Type',
                            'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name',
                            'BDF Reason Description']]
                        final_data.fillna('', inplace=True)
                        final_data.to_excel(os.path.join(self.output_path, f'MCKE_Remittance_{from_date}_{to_date}_Check_Number_{check}.xlsx'), index=False)
                        os.remove(os.path.join(self.output_path, f'MCKE_Remittance_{from_date}_{to_date}_file_{check}.xls'))
                    await self.info(f"This remittance data is being processed: {filename}")
                    consolidate_folder = os.path.join(self.output_path, 'Raw Data Remittance')
                    if not os.path.exists(consolidate_folder):
                        os.makedirs(consolidate_folder)
                    consolidated_data = pd.DataFrame()
                    try:
                        for filename in os.listdir(self.output_path):
                            if filename.endswith('.xlsx') and filename.startswith('MCKE_Remittance'):
                                file_path = os.path.join(self.output_path, filename)
                                df = pd.read_excel(file_path)
                                consolidated_data = pd.concat([consolidated_data, df], ignore_index=True)
                        # Export consolidated data to a single Excel file
                        consolidated_file_path = os.path.join(consolidate_folder, f'MCKE_Remittance_{from_date}_{to_date}_consolidated_file.xlsx')
                        consolidated_data.to_excel(consolidated_file_path, index=False)
                    except TimeoutException:
                        await self.error('Data Not found for consolidation')
            self.log.debug("Consolidated file saved: Raw_Data_Remittance")
            await self.info("Processing data for consolidation...")
            current_date = datetime.today().strftime('%Y%m%d')
            output_path = self.output_path
            consolidate_folder = os.path.join(output_path, 'Raw Data Remittance')
            zip_filename = os.path.join(output_path, f"MCKE_Remittance_{current_date}.zip")
            xl_files = [file for file in os.listdir(output_path) if file.endswith('.xlsx')]
            if len(xl_files) > 0:
                with zipfile.ZipFile(zip_filename, 'w') as zipf:
                    for file in os.listdir(output_path):
                        if file.endswith('.xlsx'):
                            file_path = os.path.join(output_path, file)
                            zipf.write(file_path, arcname=file)
                    for root, dirs, files in os.walk(consolidate_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, output_path)
                            zipf.write(file_path, arcname)
                await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
                return f'{zip_filename}'
            else:
                await self.error('Invalid! Not found. Please try again with valid date range.')
        else:
            await self.error(f"Date range difference exceeds 365 days: {delta.days} days")
            return
        
    def is_logged_in(self) -> bool:
        return 'https://connect.mckesson.com/portal' not in self.driver.current_url
