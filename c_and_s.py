from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from accelerators import Accelerator
from datetime import timedelta, date, datetime
import zipfile
import os
import pandas as pd
import numpy as np


class SelectSearchCriteria(str, Enum):
    LAST_01 = "Last 1 Day"
    LAST_03 = "Last 3 Days"
    LAST_07 = "Last 7 Days"
    Enter_date = "Last 15 days"

class CAndSAccelerator(Accelerator):
    display_name = 'Remittance'
    group_name = 'C&S Wholesale Grocers'
    start_url = "https://websso.cswg.com/oam/server/obrareq.cgi?encquery%3DS3YmdXVDxozZJNsQ1kaD8B392xA2nxCvfyc%2FtcT%2FQDNtSHNThYBzZyOsekisHxh1TtAoTq5T%2Fqkkj1punHwCLvO1Vc9t1dLOxf18uM6KK2Xx4caNl0119iwgVNDT%2BrSt1mXxDH03RGaRnq1jLcgELO8W4gx%2BvQIIId5b1LUiRdc2PHPPtXfjXnRwoL6a5ucEfTSfJEUiC1qhZOAo2R3%2BzHR4D%2BCUcyvRgAD1rOa1dUauMR1fuJQc3aLXrp3hRR9nfgHrG3knZG0CkaXm1cLF9vdO%2BfZKuq408LrxsRc10lA%3D%20agentid%3Dvendorportal.cswg.com%20ver%3D1%20crmethod%3D2"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> CSWG</p>
        <p><strong>Vendor Name:</strong> C&S Wholesale Grocers</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://vendorportal.cswg.com">https://vendorportal.cswg.com</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299379</p>
        <p><strong>SAP Account Name:</strong> C & S WHOLESALE GROC</p><br>
    </div>"""
    vendor_info = ''

    
    async def run(self, Select_Search_Criteria: SelectSearchCriteria, user_date: date) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            await self.info('Starting Accelerator...')
            if not self.is_logged_in():
                await self.info('Attempting to login...')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="username"]')))
                username_input.clear()
                username_input.send_keys(username)
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="password"]')))
                password_input.clear()
                password_input.send_keys(password)
                submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_button.click()
                try:
                    acknowledge_popup_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pgl12"]')))
                    acknowledge_popup_button.click()
                except Exception:
                    self.log.debug("acknowledge_popup_button not found")
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! We're logged in. Let's proceed.")
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Reports']")))
        except TimeoutException:
            self.log.debug('not available advanced filter')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        self.driver.get('https://vendorportal.cswg.com/vip/faces/pages_reports/CheckCoverSheetsDashboard')
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body//button[@id='pt1:pt_sfm1j_id_3:pt_s12j_id_7:pt_cb2']")))
        except TimeoutException:
            self.log.debug('not available advanced filter')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div/form/div/div/div/div[5]/div/div[2]/div/div/div/div/iframe")))
        date_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td')))
        self.driver.execute_script("arguments[0].click();", date_box)
        if Select_Search_Criteria == SelectSearchCriteria.LAST_01:
            start_date = user_date - timedelta(days=1)
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_03:
            start_date = user_date - timedelta(days=3)
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_07:
            start_date = user_date - timedelta(days=7)
        elif Select_Search_Criteria == SelectSearchCriteria.Enter_date:
            start_date = user_date - timedelta(days=15)  # Assuming "last 15 days" means the past 15 days including today
        else:
            await self.error('Invalid search criteria. Please select a valid option.')
            return
        current_date = start_date
        while current_date < user_date:
            current_date_str = current_date.strftime("%m/%d/%Y")
            insert_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td/span/input')))
            insert_date_input.clear()
            insert_date_input.send_keys(current_date_str)
            insert_date_input.send_keys(Keys.ENTER)
            insert_date_input.send_keys(Keys.ENTER)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            for _ in range(5):
                try:
                    apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[3]/td/input')))
                    apply_button.click()
                    break
                except StaleElementReferenceException:
                    continue
            export_button_xpath = '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td[9]/a'
            export_button_visible = EC.visibility_of_element_located((By.XPATH, export_button_xpath))
            try:
                wait.until(export_button_visible)
            except TimeoutException:
                await self.info(f"Not Found Date: {current_date_str}")
                current_date += timedelta(days=1)
                continue
            try:
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("arguments[0].click();", export_button)
            except StaleElementReferenceException:
                self.log.debug('export button element is stale. Trying to find it again...')
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("arguments[0].click();", export_button)
            try:
                click_excel = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Excel 2007+')]")))
                click_excel.click()
            except TimeoutException:
                self.log.debug('click excel not found, please try again')
                continue
            await self.wait_for_output(lambda files: any(file.startswith("Check Cover Sheets Report") for file in files))
            try:
                click_ok = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.masterToolbarTextButton.button[name="OK"]')))
                click_ok.click()
            except TimeoutException:
                self.log.debug("click_ok button not found ...")
                continue
            current_date_str = current_date_str.replace('/', '-')
            for filename in os.listdir(self.output_path):
                if filename.startswith('Check Cover Sheets Report'):
                    try:
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'CSWG_Remittance_{Select_Search_Criteria.value}_CheckDate_{current_date_str}.xlsx'))
                    except TimeoutException:
                        self.log.debug("TimeoutException while renaming file or maybe file is not found")
                    file_data = pd.read_excel(os.path.join(self.output_path, f'CSWG_Remittance_{Select_Search_Criteria.value}_CheckDate_{current_date_str}.xlsx'), skiprows=4)
                    file_data = file_data.drop('Unnamed: 1', axis=1)
                    columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                    for col in columns_addon:
                        file_data[f'{col}'] = ''
                    file_data['Invoice Num/Desc'] = file_data['Invoice Num/Desc'].fillna('').astype(str)
                    conditions = [
                        file_data['Net'] < 0,
                        (file_data['Net'] > 0) & (file_data['Invoice Num/Desc'].str.match(r'^\d{10}$', na=False)),
                        (file_data['Net'] > 0) & (~file_data['Invoice Num/Desc'].str.match(r'^\d{10}$', na=False))]
                    choices = ['Deduction', 'Invoice Payment', 'Repayment']
                    file_data['BDF Record Type'] = np.select(conditions, choices, default='-')
                    tolerance_conditions = [
                        (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net'].abs() > 0) & (file_data['Net'].abs() < 200),
                        (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net'].abs() > 200)]
                    tolerance_choices = ['UT', 'OT']
                    file_data['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                    file_data['Voucher Date'] = pd.to_datetime(file_data['Voucher Date'])
                    file_data['BDF Expiry'] = file_data['Voucher Date'] + pd.Timedelta(days=45)
                    file_data['Voucher Date'] = file_data['Voucher Date'].dt.strftime('%m/%d/%Y')
                    file_data['BDF Expiry'] = file_data['BDF Expiry'].dt.strftime('%m/%d/%Y')
                    file_data['Check Date'] = file_data['Check Date'].dt.strftime('%m/%d/%Y')
                    file_data['Invoice Num/Desc'].fillna('', inplace=True)
                    await self.info('Starting data transformation...')
                    reason_code_conditions = [
                        file_data['Invoice Num/Desc'].str.startswith('9079510413', na=False),
                        file_data['Invoice Num/Desc'].str.endswith('R', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('DC', na=False),
                        file_data['Invoice Num/Desc'].str.endswith('IL', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('DL', na=False),
                        file_data['Invoice Num/Desc'].str.endswith('F', na=False),
                        file_data['Invoice Num/Desc'].str.endswith('FG', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('OTP', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('A', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('9079510413', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('CLA', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('J', na=False),
                        file_data['Invoice Num/Desc'].str.startswith('Z', na=False),
                        file_data['Invoice Num/Desc'].str.contains('CPI', case=False, na=False)
                    ]
                    reason_code_choices = ['101', '102', '105', '105', '108', '108', '108', '108', '306', '306', '306', '306', '306', '312']
                    reason_code_ID_choices = ["Quantity Difference", "Stock Return", "Quality/Damaged Goods", "Quality/Damaged Goods", "DCS Penalties / Fine", "DCS Penalties / Fine", "DCS Penalties / Fine", "DCS Penalties / Fine", "TTC Deduction - Invoice Missing", "TTC Deduction - Invoice Missing", "TTC Deduction - Invoice Missing", "TTC Deduction - Invoice Missing", "TTC Deduction - Invoice Missing", "Coupons"]
                    reason_code_description = ["BDF INVOICE# AND QTY SHORTAGE", "RETURNS", "UNSALEABLES", "UNSALEABLES", "FINES (TEXT IS UL)", "FINE (TEXT IS SF)", "FINE (TEXT IS UL)", "FINES (TEXT IS OT)", "COOP", "BDF INVOICE# AND SSA ALLOWANCE DEDUCTION", "COOP", "COOP", "CO OP-TOPS", "COUPONS"]
                    file_data['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                    file_data['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                    file_data['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
                    await self.info("Processing...")
                    file_data['Invoice Num/Desc'].fillna('', inplace=True)
                    file_data.to_excel(os.path.join(self.output_path, f'CSWG_Remittance_{Select_Search_Criteria.value}_CheckDate_{current_date_str}.xlsx'), index=False)
                    consolidate_folder = os.path.join(self.output_path, 'Raw Data Remittance')
                    if not os.path.exists(consolidate_folder):
                        os.makedirs(consolidate_folder)
                    consolidated_data = pd.DataFrame()
                    try:
                        for filename in os.listdir(self.output_path):
                            if filename.endswith('.xlsx') and filename.startswith('CSWG_Remittance_'):
                                file_path = os.path.join(self.output_path, filename)
                                df = pd.read_excel(file_path)
                                consolidated_data = pd.concat([consolidated_data, df], ignore_index=True)
                                await self.info(f"Processed for consolidation: {filename}")
                        # Export consolidated data to a single Excel file
                        consolidated_file_path = os.path.join(consolidate_folder, 'CSWG_Remittance_consolidated_file.xlsx')
                        consolidated_data.to_excel(consolidated_file_path, index=False)
                    except TimeoutException:
                        await self.error('Data Not found for consolidation')
            await self.info(f"Found: {current_date_str}")
            current_date += timedelta(days=1)
        self.log.debug("Consolidated file saved: Raw_Data_Remittance")
        current_date = datetime.today().strftime('%Y%m%d')
        output_path = self.output_path
        consolidate_folder = os.path.join(output_path, 'Raw Data Remittance')
        zip_filename = os.path.join(output_path, f"CSWG_Remittance_{Select_Search_Criteria.value}_{current_date}.zip")
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
            await self.error('Invalid! Not found. Please try again with valid check creation date.')

    def is_logged_in(self) -> bool:
        return 'https://websso.cswg.com/oam' not in self.driver.current_url
