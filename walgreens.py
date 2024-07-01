from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from enum import Enum
from selenium.common.exceptions import StaleElementReferenceException
import os
from accelerators import Accelerator
import pandas as pd
import numpy as np
from datetime import datetime
import zipfile

class DocumentDateRange(str, Enum):
    # LAST_10 = "Last 10 days"
    LAST_30 = "Last 30 days"
    LAST_60 = "Last 60 days"
    LAST_90 = "Last 90 days"

class WalgreensAccelerator(Accelerator):
    display_name = 'All Data Downloader'
    group_name = 'Walgreens'
    start_url = 'https://ppxvimspot.walgreens.com/sap/bc/ui5_ui5/ui2/ushell/shells/abap/FioriLaunchpad.html#OTBCWUI_PF07_BC_SEMOBJ-displayDesktopOnly?workplaceId=ACC_INBOX&system=OTBCWUI_BACKEND&appMode=FS'
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance/Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, this operation may take some time to complete.</p>
        <br>
        <p><strong>Vendor Code:</strong> WALG</p>
        <p><strong>Vendor Name:</strong> Walgreens</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://sso.walgreens.com/idp/SSO.saml2">https://sso.walgreens.com/idp/SSO.saml2</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299387</p>
        <p><strong>SAP Account Name:</strong> WALGREENS</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, payment_ref_range: DocumentDateRange) -> str:
        await self.info('Starting Accelerator...')
        wait = WebDriverWait(self.driver, 70)
        
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()

                username_element = wait.until(EC.element_to_be_clickable((By.ID, "username")))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.ID, "txtpassword")))
                password_element.clear()
                password_element.send_keys(password)

                wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Sign On"]'))).click()

                if not self.is_logged_in():
                    await self.error('Login failed. Please try again.')
                    return
                await self.info("Great! We're logged in. Let's proceed.")
        await self.info("Please wait, we're processing the request...")
        wait.until(EC.element_to_be_clickable((By.XPATH, '//td[text() = "No data"]')))
        date_range = payment_ref_range.value
        for _ in range(5):
            try:
                supplier = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[text()= "Document Date"]'))
                )
                supplier.click()
                break
            except StaleElementReferenceException:
                continue
            
        wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[text() = "{date_range}"]')))
        for _ in range(5):
            try:
                daterange = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'//*[text() = "{date_range}"]'))
                )
                daterange.click()
                daterange_select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//bdi[text() = "OK"]'))
                )
                daterange_select.click()
                break
            except StaleElementReferenceException:
                continue
        wait.until(EC.element_to_be_clickable((By.XPATH, f'//bdi[text() = "Document Date ({date_range})"]')))
        await self.info('Searching the portal…')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        for _ in range(5):
            try:
                supplier = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[text()= "Supplier"]'))
                )
                supplier.click()
                break
            except StaleElementReferenceException:
                continue
        await self.info(f'Found Date(s): {date_range}')
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "BEIERSDORF INC(0001044697)"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//bdi[text() = "OK"]'))).click()
        
        for _ in range(5):
            try:
                saplink = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '(//*[contains(@class, "sapMLnk")])[1]'))
                )
                saplink.click()
                break
            except StaleElementReferenceException:
                continue

        await self.info('Processing the data…')
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Download"]'))).click()
        files = await self.wait_for_output(lambda files: any('.crdownload' not in file and '.tmp' not in file for file in files))
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"WALG_Remittance_Date_{date_range}_{file}"))
        files = await self.wait_for_output(lambda files: any('.crdownload' not in file and '.tmp' not in file for file in files))
        for file in files:
            dataframe_walgreen = pd.read_excel(os.path.join(self.output_path, file))
            columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
            for col in columns_addon:
                dataframe_walgreen[f'{col}'] = ''
            dataframe_walgreen['Invoice Number'] = dataframe_walgreen['Invoice Number'].astype(str)
            conditions = [
                dataframe_walgreen['Original Inv Amount'] < 0,
                (dataframe_walgreen['Original Inv Amount'] > 0) & (dataframe_walgreen['Invoice Number'].str.match(r'^\d{10}$', na=False)),
                (dataframe_walgreen['Original Inv Amount'] > 0) & (~dataframe_walgreen['Invoice Number'].str.match(r'^\d{10}$', na=False))
            ]

            choices = ['Deduction', 'Invoice Payment', 'Repayment']

            dataframe_walgreen['BDF Record Type'] = np.select(conditions, choices, default='-')

            tolerance_conditions = [
                (dataframe_walgreen['BDF Record Type'] == 'Deduction') & (dataframe_walgreen['Original Inv Amount'].abs() > 0) & (dataframe_walgreen['Original Inv Amount'].abs() < 200),
                (dataframe_walgreen['BDF Record Type'] == 'Deduction') & (dataframe_walgreen['Original Inv Amount'].abs() > 200)
            ]

            tolerance_choices = ['UT', 'OT']

            dataframe_walgreen['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

            dataframe_walgreen['Invoice Date'] = pd.to_datetime(dataframe_walgreen['Invoice Date'], format='%m/%d/%Y')
            dataframe_walgreen['BDF Expiry'] = dataframe_walgreen['Invoice Date'] + pd.Timedelta(days=45)

            reason_code_conditions = [
                dataframe_walgreen['Invoice Number'].str.match(r'^\d{10}$', na=False),
                dataframe_walgreen['Invoice Number'].str.endswith('C', na=False),
                dataframe_walgreen['Invoice Number'].str.startswith('51', na=False),
                dataframe_walgreen['Invoice Number'].str.startswith('1', na=False) & dataframe_walgreen['Invoice Number'].str.match(r'^\d{12}$', na=False),
                dataframe_walgreen['Invoice Number'].str.startswith('EDI', na=False),
                dataframe_walgreen['Invoice Number'].str.contains('FR', case=False, na=False)
            ]

            reason_code_ID_choices = ['101', '101', '102', '105', '108', '108']
            reason_code_choices = ['Quantity Difference', 'Quantity Difference', 'Stock Return ', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'DCS Penalties / Fine']
            reason_code_description = ['Shortage. Deductions w/Invoice #, download remit from WAGS, look in "Description" column for "Quantity Debit Note"', 'Shortage. Invoice Numbers followed by a "C"', 'Starts with 51 and is 10-digits.  Return to Vendor (RTV)', 'Starts with "1" + 2 digits for the year.  Total of 12-digits', 'EDI FINE', 'FINE']
            dataframe_walgreen['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
            dataframe_walgreen['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
            dataframe_walgreen['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
            dataframe_walgreen['BDF Expiry'] = dataframe_walgreen['BDF Expiry'].dt.strftime('%m/%d/%Y')
            dataframe_walgreen['Payment Reference'] = dataframe_walgreen['Payment Reference'].fillna('NoPaymentRef')
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            output_zip = os.path.join(self.output_path, f"WALG_All_Data_{formatted_date}.zip")
            os.makedirs(os.path.join(self.output_path, 'Remittance with Payment Reference'))
            os.makedirs(os.path.join(self.output_path, 'Consolidate Version'))
            df_1 = dataframe_walgreen.groupby('Payment Reference')
            df_2 = {group: df_1.get_group(group) for group in df_1.groups}
            download_focus = False
            file_na = file.split('_')[-1]
            for payment_ref in df_2:
                filtered_df = df_2[payment_ref]
                download_focus = True
                payment_ref = str(payment_ref).strip()
                payment_ref = str(payment_ref).replace('.0', '')
                filtered_df.to_excel(os.path.join(self.output_path, 'Remittance with Payment Reference', f"WALG_All_data_{formatted_date}_Date_{date_range}_with_payment Ref_{payment_ref}_{file_na}"), index=False)
            dataframe_walgreen.to_excel(os.path.join(self.output_path, 'Consolidate Version', f"WALG_All_data_{formatted_date}_Date_{date_range}_Consolidate_{file_na}"), index=False)
            if download_focus:
                all_dirs = [file for file in os.listdir(self.output_path) if file.endswith('Payment Reference') or file.endswith('Version')]
                with zipfile.ZipFile(output_zip, 'w') as zipf:
                    for all_dir in all_dirs:
                        if all_dir.endswith('Payment Reference'):
                            version_folder_path = os.path.join(self.output_path, 'Remittance with Payment Reference')
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
    
    def is_logged_in(self) -> bool:
        return 'sso.walgreens.com' not in self.driver.current_url
