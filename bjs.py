from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from datetime import date
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
import pandas as pd
import numpy as np
 
class BJSAccelerator(Accelerator):
    display_name = "All Data Downloader"
    group_name = "BJ's Wholesale Club"
    start_url = "https://vendorportal.bjs.com/bd/public/frameset_top_html.jsp"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance/Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, you must select less than a 90 day window, within the past 12 months.</p>
        <br>
        <p><strong>Vendor Code:</strong> BJSW</p>
        <p><strong>Vendor Name:</strong> BJ's Wholesale Club</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://vendorportal.bjs.com/">https://vendorportal.bjs.com/</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299255</p>
        <p><strong>SAP Account Name:</strong> BJ'S WHLSE CLUB</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 30)
 
        async with self.authenticator() as auth:
            await self.info('Starting Accelerator...')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
 
                for frame_change in ["billerdirect_application", "billerdirect_content"]:
                    self.driver.switch_to.frame(frame_change)
 
                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="User *"]')))
                username_element.clear()
                username_element.send_keys(username)
 
                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="j_password"]')))
                password_element.clear()
                password_element.send_keys(password)
 
                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_login.click()
                self.driver.switch_to.default_content()
 
                if not self.is_logged_in():
                    await self.error('Login failed. Please try again.')
                    return
                await self.info("Great! We're logged in. Let's proceed.")
        
        await self.info("Please wait, we're processing the request...")
        for frame_change in ["billerdirect_application", "billerdirect_navigation"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for Payment Detail {frame_change}")
 
        payment_detail = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Payment Detail']")))
        payment_detail.click()
        self.driver.switch_to.default_content()
 
        for frame_change in ["billerdirect_application", "billerdirect_content"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
 
        select_range_date = wait.until(EC.element_to_be_clickable((By.ID, "searchDateId")))
        self.driver.execute_script("arguments[0].click();", select_range_date)
        select_range_date.send_keys(Keys.END)
 
        # start date range
        from_date_field_month = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom1")))
        from_date_field_day = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom2")))
        from_date_field_year = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom3")))
        # End date range
        to_date_field_month = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo1")))
        to_date_field_day = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo2")))
        to_date_field_year = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo3")))
        await self.info('Searching the portal…')
        from_date_field_month.clear()
        from_date_field_month.send_keys(from_date.month)
        from_date_field_day.clear()
        from_date_field_day.send_keys(from_date.day)
        from_date_field_year.clear()
        from_date_field_year.send_keys(from_date.year)
 
        to_date_field_month.clear()
        to_date_field_month.send_keys(to_date.month)
        to_date_field_day.clear()
        to_date_field_day.send_keys(to_date.day)
        to_date_field_year.clear()
        to_date_field_year.send_keys(to_date.year)
 
        submit_filter = wait.until(EC.element_to_be_clickable((By.NAME, "Search")))
        submit_filter.click()
        await self.info(f'Found Date(s): {from_date} - {to_date}')
        download_file = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Download"]')))
        download_file.click()
        self.driver.switch_to.default_content()
        await self.info('Processing the data…')
        for frame_change in ["billerdirect_application", "billerdirect_navigation"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for Open Invoice {frame_change}")
 
        open_Invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Open Invoices/Credits"]')))
        open_Invoice.click()
 
        self.driver.switch_to.default_content()
        for frame_change in ["billerdirect_application", "billerdirect_content"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
        download_file = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Download"]')))
        download_file.click()
        self.driver.switch_to.default_content()
        required_files = ["Payment_Details.csv", "Open_Invoices_Credits.csv"]
        files = await self.wait_for_output(lambda files: all(file in required_files for file in files))
        dataframe_bjs = pd.read_csv(os.path.join(self.output_path, 'Payment_Details.csv'), skiprows=4)
        columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Code Description']
        for col in columns_addon:
            dataframe_bjs[f'{col}'] = ''
        dataframe_bjs['Amount'] = dataframe_bjs['Amount'].str.replace(',', '')
        dataframe_bjs['Amount'] = dataframe_bjs['Amount'].str.replace(r'[()]', '', regex=True)
        dataframe_bjs['Amount'] = dataframe_bjs['Amount'].astype('float')
        dataframe_bjs['Invoice #'] = dataframe_bjs['Invoice #'].astype(str)
        dataframe_bjs['Doc Type'] = dataframe_bjs['Doc Type'].astype(str)
        conditions = [
            dataframe_bjs['Amount'] < 0,
            (dataframe_bjs['Amount'] > 0) & (dataframe_bjs['Invoice #'].str.match(r'^\d{10}$', na=False)),
            (dataframe_bjs['Amount'] > 0) & (~dataframe_bjs['Invoice #'].str.match(r'^\d{10}$', na=False)),
        ]

        choices = ['Deduction', 'Invoice Payment', 'Repayment']

        dataframe_bjs['BDF Record Type'] = np.select(conditions, choices, default='-')


        tolerance_conditions = [
            (dataframe_bjs['BDF Record Type'] == 'Deduction') & (dataframe_bjs['Amount'].abs() > 0) & (dataframe_bjs['Amount'].abs() < 200),
            (dataframe_bjs['BDF Record Type'] == 'Deduction') & (dataframe_bjs['Amount'].abs() > 200)
        ]

        tolerance_choices = ['UT', 'OT']

        dataframe_bjs['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

        dataframe_bjs['Check Date'] = pd.to_datetime(dataframe_bjs['Check Date'])
        dataframe_bjs['BDF Expiry'] = dataframe_bjs['Check Date'] + pd.Timedelta(days=45)

        reason_code_conditions = [
            dataframe_bjs['Invoice #'].str.match(r'^\d{10}$', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Y8', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z5', na=False),
            dataframe_bjs['Invoice #'].str.startswith('8', na=False),
            dataframe_bjs['Doc Type'].str.startswith('ZB', na=False),
            dataframe_bjs['Invoice #'].str.startswith('100', na=False),
            dataframe_bjs['Doc Type'].str.startswith('CP', na=False),
            dataframe_bjs['Invoice #'].str.startswith('MS', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z1', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z2', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z3', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z7', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z8', na=False),
            dataframe_bjs['Doc Type'].str.startswith('ZO', na=False),
            dataframe_bjs['Doc Type'].str.startswith('KG', na=False),
            dataframe_bjs['Doc Type'].str.startswith('KR', na=False),
            dataframe_bjs['Doc Type'].str.startswith('RE', na=False),
            dataframe_bjs['Doc Type'].str.startswith('RK', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Y1', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Y6', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Y9', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z0', na=False),
            dataframe_bjs['Doc Type'].str.startswith('Z4', na=False),
            dataframe_bjs['Doc Type'].str.startswith('ZF', na=False),
        ]

        reason_code_ID_choices = ['101', '102', '105', '108', '108', '306', '306', '306', '306', '306', '306', '306', '306', '306', '', '', '', '', '', '', '', '', '', '']
        reason_code_choices = ['Quantity Difference', 'Stock Return ', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'DCS Penalties / Fine', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A']
        reason_code_des_choices = ['BDF INVOICE# AND "RECVD QTY", "INV QTY" in Comments', 'RETURN', 'SALVAGE', 'FINE', 'Logistic Chargeback', 'PROMO COUPON', 'PROMO COUPON', 'COOP', 'REBATE', 'PRICE PROTECTION', 'INSERTION FEE', 'INSTANT SAVINGS REBATE', 'VOLUME REBATE', 'PROMO COUPON', 'Vendor Deduction', 'Vendor Repayment', 'Paper Invoice', 'Invoice Reduction', 'EDI Invoice Reduciton', 'EDI Invoice', 'Consignment Invoice', 'Coupon Deduction', 'Demos', 'Engagement Fee']
        dataframe_bjs['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
        dataframe_bjs['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
        dataframe_bjs['BDF Reason Code Description'] = np.select(reason_code_conditions, reason_code_des_choices, default='-')
        
        dataframe_bjs.to_csv(os.path.join(self.output_path, 'Payment_Details.csv'), index=False)
        from_date = from_date.strftime("%m%d%Y")
        to_date = to_date.strftime("%m%d%Y")
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        output_zip = os.path.join(self.output_path, f"BJS_All_Backup_{formatted_date}.zip")
        os.makedirs(os.path.join(self.output_path, 'Remittance with Check Number'))
        os.makedirs(os.path.join(self.output_path, 'Backup with Invoice Number'))
        os.makedirs(os.path.join(self.output_path, 'Consolidate Version'))
        if len(files) == 2:
            for file in files:
                if 'Payment_Details' in file:
                    df_1 = dataframe_bjs.groupby('Check #')
                    df_2 = {group: df_1.get_group(group) for group in df_1.groups}
                    for payment_number in df_2:
                        filtered_df = df_2[payment_number]
                        filtered_df.to_csv(os.path.join(self.output_path, 'Remittance with Check Number', f"BJSW_Remittance_Check_{payment_number}_Date_{from_date}_{to_date}_{file}"), index=False)
                    dataframe_bjs.to_csv(os.path.join(self.output_path, 'Consolidate Version', f"BJSW_Remittance_Backup_Date_{from_date}_{to_date}_{file}"), index=False)
                else:
                    dataframe_bjs_bckup = pd.read_csv(os.path.join(self.output_path, 'Open_Invoices_Credits.csv'), skiprows=4)
                    for dataframes in [dataframe_bjs_bckup, dataframe_bjs]:
                        df_1 = dataframes.groupby('Invoice #')
                        df_2 = {group: df_1.get_group(group) for group in df_1.groups}
                        for payment_number in df_2:
                            filtered_df = df_2[payment_number]
                            filtered_df.to_csv(os.path.join(self.output_path, 'Backup with Invoice Number', f"BJSW_Backup_Invoice_{payment_number}.csv"), index=False)
                    dataframe_bjs_bckup.to_csv(os.path.join(self.output_path, 'Consolidate Version', f"BJSW_Backup_Date_range_All_{file}"), index=False)
            all_dirs = [file for file in os.listdir(self.output_path) if file.endswith('Check Number') or file.endswith('Version') or file.endswith('Invoice Number')]
            with zipfile.ZipFile(output_zip, 'w') as zipf:
                for all_dir in all_dirs:
                    if all_dir.endswith('Check Number'):
                        version_folder_path = os.path.join(self.output_path, 'Remittance with Check Number')
                    if all_dir.endswith('Version'):
                        version_folder_path = os.path.join(self.output_path, 'Consolidate Version')
                    if all_dir.endswith('Invoice Number'):
                        version_folder_path = os.path.join(self.output_path, 'Backup with Invoice Number')
                    for foldername, subfolders, filenames in os.walk(version_folder_path):
                        for filename in filenames:
                            file_path = os.path.join(foldername, filename)
                            relative_path = os.path.relpath(file_path, self.output_path)
                            zipf.write(file_path, arcname=relative_path)
            if os.path.exists(output_zip):
                await self.info("Success! Please click 'Download' to receive files.")
                return output_zip
        else:
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return

    def is_logged_in(self) -> bool:
        try:
            for frame_change in ["billerdirect_application", "billerdirect_content"]:
                self.driver.switch_to.frame(frame_change)
                self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="j_password"]')))
            self.driver.switch_to.default_content()
            return False
        except Exception:
            self.driver.switch_to.default_content()
            return True
