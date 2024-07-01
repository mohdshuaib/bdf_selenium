from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from datetime import datetime
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import os
import zipfile
from accelerators import Accelerator
import pandas as pd
import numpy as np
 
class FLHFRemittanceAccelerator(Accelerator):
    display_name = "Remittance Downloader"
    group_name = "Food Lion/Hannaford"
    start_url = "https://ws1.aholdusa.com/jfitvp/news"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> FLHF</p>
        <p><strong>Vendor Name:</strong> Food Lion/Hannaford</p>
        <p><strong>Vendor Portal Link:</strong> <a href="http://Partners.Ahold.com">http://Partners.Ahold.com</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299350, 40299339</p>
        <p><strong>SAP Account Name:</strong> FOOD LION LLC, HANNAFORD BROS</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Starting Accelerator...')
        delta = to_date - from_date
        if delta.days <= 31:
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
    
                    username_element = wait.until(EC.element_to_be_clickable((By.ID, 'uid')))
                    username_element.clear()
                    username_element.send_keys(username)
    
                    password_element = wait.until(EC.element_to_be_clickable((By.ID, 'password')))
                    password_element.clear()
                    password_element.send_keys(password)
    
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"][@value="Sign in"]')))
                    submit_login.click()
    
                    if not self.is_logged_in():
                        await self.error('Login failed. Please try again.')
                        return
                    await self.info("Great! We're logged in. Let's proceed.")
            await self.info("Please wait, we're processing the request...")
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            self.driver.get("https://ws1.aholdusa.com/jfitvp/accounts/payable")
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            
            select_vendor = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@for="mat-radio-2-input"]')))
            select_vendor.click()
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Continue "]'))).click()
            except TimeoutException:
                for _ in range(5):
                    try:
                        select_vendor = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@for="mat-radio-2-input"]'))
                        )
                        select_vendor.click()
                        try:
                            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Continue "]'))).click()
                        except TimeoutException:
                            continue
                        break
                    except StaleElementReferenceException:
                        continue
                    
            await self.info('Searching the portal…')
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            select_range_date_start = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@formcontrolname="dateRangeStart"]')))
            select_range_date_end = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@formcontrolname="dateRangeEnd"]')))
            select_range_date_start.clear()
            select_range_date_end.clear()
            for i in range(1, 10):
                select_range_date_start.send_keys(Keys.BACKSPACE)
            for j in range(1, 10):
                select_range_date_end.send_keys(Keys.BACKSPACE)
            select_range_date_start.send_keys(f"{from_date.month}/{from_date.day}/{from_date.year}")
            select_range_date_end.send_keys(f"{to_date.month}/{to_date.day}/{to_date.year}")
            # start date range
            submit_filter = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()=' Go ']")))
            submit_filter.click()
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            # required because blank file download
            await self.sleep(10)
            try:
                download_file = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()=' Export All Acct Activity ']")))
            except TimeoutException:
                await self.error('Invalid! Remittance data not found. Please try again with valid date range.')
                return
            await self.info(f'Found Date(s): {from_date} - {to_date}')
            download_file.click()

            await self.info('Processing the data…')
            output_zip = os.path.join(self.output_path, "FLHF_Remittance.zip")
            files = await self.wait_for_output(lambda files: 'AP-AR DETAILS.csv' in files)
            from_date = from_date.strftime("%m%d%Y")
            to_date = to_date.strftime("%m%d%Y")
            if files:
                rename_files = []
                for file in files:
                    os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}"))
                    dataframe_food_lion = pd.read_csv(os.path.join(self.output_path, f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}"))
                    columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                    for col in columns_addon:
                        dataframe_food_lion[f'{col}'] = ''
                    conditions = [
                        dataframe_food_lion['Gross Amount'] < 0,
                        (dataframe_food_lion['Gross Amount'] > 0) & (dataframe_food_lion['Invoice #'].str.match(r'^\d{10}$', na=False)),
                        (dataframe_food_lion['Gross Amount'] > 0) & (dataframe_food_lion['Invoice #'].str.match(r'^\d{8}$', na=False)) & (dataframe_food_lion['Invoice #'].str.startswith('7')),
                        (dataframe_food_lion['Gross Amount'] > 0) & (~dataframe_food_lion['Invoice #'].str.match(r'^\d{10}$', na=False))
                    ]

                    choices = ['Deduction', 'Invoice Payment', 'VAN Invoice Payment', 'Repayment']

                    dataframe_food_lion['BDF Record Type'] = np.select(conditions, choices, default='-')
                    tolerance_conditions = [
                        (dataframe_food_lion['BDF Record Type'] == 'Deduction') & (dataframe_food_lion['Gross Amount'].abs() > 0) & (dataframe_food_lion['Gross Amount'].abs() < 200),
                        (dataframe_food_lion['BDF Record Type'] == 'Deduction') & (dataframe_food_lion['Gross Amount'].abs() > 200)
                    ]

                    tolerance_choices = ['UT', 'OT']

                    dataframe_food_lion['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                    dataframe_food_lion['Payment Date'] = dataframe_food_lion['Payment Date'].str.replace('-', '/')
                    dataframe_food_lion['Payment Date'] = pd.to_datetime(dataframe_food_lion['Payment Date'], format='%Y/%m/%d')
                    dataframe_food_lion['BDF Expiry'] = dataframe_food_lion['Payment Date'] + pd.Timedelta(days=45)
                    
                    reason_code_conditions = [
                        dataframe_food_lion['Invoice #'].str.startswith('IR', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('PR', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('VC', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('A', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('BB', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('CA', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('CL', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('COG', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('FR', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('GB', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('H', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('J', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('K', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('MK', na=False),
                        dataframe_food_lion['Invoice #'].str.startswith('MV', na=False)
                    ]
                    reason_code_ID_choices = ['105', '105', '108', '306', '306', '306', '306', '306', '306', '306', '306', '306', '306', '306', '306']
                    reason_code_choices = ['Quality/Damaged Goods', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing']
                    reason_code_description = ['Inventory Returns', 'UNSALEABLE', 'FINE', 'COOP C&S 40299379', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP C&S 40299379', 'COOP C&S 40299379', 'COOP C&S 40299379', 'COOP', 'COOP']
                    dataframe_food_lion['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                    dataframe_food_lion['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                    dataframe_food_lion['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
                    dataframe_food_lion.to_csv(os.path.join(self.output_path, f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}"), index=False)
                    rename_files.append(f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}")
                current_date = datetime.now()
                formatted_date = current_date.strftime("%m%d%Y")
                output_zip = os.path.join(self.output_path, f"FLHF_Remittance_{formatted_date}.zip")
                os.makedirs(os.path.join(self.output_path, 'Remittance with Invoice Date'))
                os.makedirs(os.path.join(self.output_path, 'Consolidate Version'))
                
                df_1 = dataframe_food_lion.groupby('Invoice Date')
                df_2 = {group: df_1.get_group(group) for group in df_1.groups}
                for invoice_date in df_2:
                    filtered_df = df_2[invoice_date]
                    filtered_df.to_csv(os.path.join(self.output_path, 'Remittance with Invoice Date', f"FLHF_Remittance_with_invoice_date_{invoice_date}_date_range_{from_date}_{to_date}_{file}"), index=False)
                dataframe_food_lion.to_csv(os.path.join(self.output_path, 'Consolidate Version', f"FLHF_Remittance_Consolidate_{from_date}_{to_date}_{file}"), index=False)
            
                all_dirs = [file for file in os.listdir(self.output_path) if file.endswith('Invoice Date') or file.endswith('Version')]
                with zipfile.ZipFile(output_zip, 'w') as zipf:
                    for all_dir in all_dirs:
                        if all_dir.endswith('Invoice Date'):
                            version_folder_path = os.path.join(self.output_path, 'Remittance with Invoice Date')
                        if all_dir.endswith('Version'):
                            version_folder_path = os.path.join(self.output_path, 'Consolidate Version')
                        for foldername, subfolders, filenames in os.walk(version_folder_path):
                            for filename in filenames:
                                file_path = os.path.join(foldername, filename)
                                relative_path = os.path.relpath(file_path, self.output_path)
                                zipf.write(file_path, arcname=relative_path)
                    await self.info("Success! Please click 'Download' to receive files.")
                    return output_zip
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
                return
        else:
            await self.error(f"Date range difference exceeds 31 days: {delta.days} days")
            return
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.visibility_of_element_located((By.ID, 'uid')))
            return False
        except Exception:
            return True
