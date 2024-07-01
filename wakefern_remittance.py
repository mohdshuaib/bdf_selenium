from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
import pandas as pd
import numpy as np
 
class WKFRNAccelerator(Accelerator):
    display_name = "Remittance Downloader"
    group_name = "Wakefern Foods"
    start_url = 'http://www8.wakefern.com/servlet/com.wakefern.wgl.framework.controller.ServletController3'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong>Be advised, the Wakefern portal website uses payment dates to display a list of checks/EFT's, which the system must read 1 at a time. In order to save process time, we have limited the search window to a max. of 3 days.</p>
        <br>
        <p><strong>Vendor Code:</strong> WAKE</p>
        <p><strong>Vendor Name:</strong> Wakefern Foods</p>
        <p><strong>Vendor Portal Link:</strong> <a href="http://www8.wakefern.com">http://www8.wakefern.com</a> (Allow pop-ups)</p>
        <p><strong>OTP Verification:</strong> OTP not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299386</p>
        <p><strong>SAP Account Name:</strong> WAKEFERN FOODS INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        await self.info('Starting Accelerator')
        delta = to_date - from_date
        if delta.days <= 31:
            wait = WebDriverWait(self.driver, 30)
    
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
    
                    self.driver.switch_to.default_content()
                    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="USERID"]')))
                    username_input.clear()
                    username_input.send_keys(username)
                    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="CURPASS"]')))
                    password_input.clear()
                    password_input.send_keys(password)
                    submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="SUBMIT"]')))
                    submit.click()
                    self.driver.switch_to.default_content()
    
                    if not self.is_logged_in():
                        await self.error('Login failed. Please try again.')
                        return
                    await self.info("Great! We're logged in. Let's proceed.")
            
            await self.info("Please wait, we're processing the request...")
            from_date_value = from_date.strftime("%m%d%Y")
            to_date_value = to_date.strftime("%m%d%Y")
            self.driver.switch_to.default_content()
            live = False
            try:
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                live = True
            except Exception:
                live = False
            if not live:
                self.driver.refresh()
                await self.sleep(2)
                self.driver.switch_to.frame()
            await self.info('Searching the portal…')
            select_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "M"]')))
            select_menu.click()
            show_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Show Menu"]')))
            show_menu.click()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="treeFrame"]'))))
            vendor = self.driver.find_elements(By.XPATH, '//*[@alt="Click to open this folder"]')[0]
            vendor.click()
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@align="TEXTTOP"]')))
            select_vendor.click()
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                from_date_input = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, '//*[@name="FROM_CHK_DATE"]')))
            except Exception:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="FROM_CHK_DATE"]')))
            to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="TO_CHK_DATE"]')))
            from_date_input.clear()
            to_date_input.clear()
            from_date_input.send_keys(from_date_value)
            to_date_input.send_keys(to_date_value)
            await self.info(f'Found Date(s): {from_date_value} - {to_date_value}')
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="actionFrame"]'))))
            submit_dates = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="CONTINUE PROCESSING"]')))
            submit_dates.click()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
            rows = self.driver.find_elements(By.XPATH, '//*[@id="fwAppDiv"]/form/center/table/tbody/tr')
            row_count = len(rows)
            await self.info('Processing the data…')
            for row_num in range(4, 4 + row_count - 3):
                if row_num > 4:
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Back to Payment Search Results"]'))).click()
                    await self.sleep(1)
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[7]/div/form/center/table/tbody/tr[{row_num}]/td[1]/font/a'))).click()
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                check_num = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/form/center/table/tbody/tr/td/table/tbody/tr[2]/td[1]/font'))).text
                check_date = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/form/center/table/tbody/tr/td/table/tbody/tr[2]/td[2]/font'))).text
                check_ammt = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/form/center/table/tbody/tr/td/table/tbody/tr[2]/td[3]/font'))).text
                test_text = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="chkDetail"]'))).text
                final_df = pd.DataFrame()
                columns = ['Date', 'Invoice/Credit Memo', 'Type', 'PO Number', 'Gross', 'Discount', 'Net', 'Check Number', 'Check Date', 'Check Ammount']
                for column in columns:
                    final_df[f'{column}'] = ''
                for line in test_text.split('\n'):
                    gen_row = line.split(' ')
                    gen_row.extend([check_num, check_date, check_ammt])
                    if len(gen_row) == 9:
                        gen_row.insert(3, '')
                    elif len(gen_row) == 11:
                        new_value = f'{gen_row[3]} {gen_row[4]}'
                        gen_row.pop(3)
                        gen_row.pop(4)
                        gen_row.insert(3, new_value)
                    new_row = pd.DataFrame([gen_row], columns=final_df.columns)
                    final_df = pd.concat([new_row, final_df], ignore_index=True)
                wakefern_df = final_df

                columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                for col in columns_addon:
                    wakefern_df[f'{col}'] = ''
                wakefern_df['Net'] = wakefern_df['Net'].astype(str)
                wakefern_df['Net'] = wakefern_df['Net'].str.replace(',', '')
                wakefern_df['Net'] = wakefern_df['Net'].astype('float')
                wakefern_df['Invoice/Credit Memo'] = wakefern_df['Invoice/Credit Memo'].astype(str)

                def determine_bdf_record_type(row):
                    if row['Type'] == 'CR':
                        return 'Deduction'
                    elif row['Type'] == 'PO':
                        if any(char.isalpha() for char in row['Invoice/Credit Memo']) and any(char.isdigit() for char in row['Invoice/Credit Memo']):
                            return 'Repayment'
                        elif row['Invoice/Credit Memo'].isdigit():
                            return 'Invoice Payment'
                    return np.nan
                
                wakefern_df['BDF Record Type'] = wakefern_df.apply(determine_bdf_record_type, axis=1)
                # conditions = [
                #     wakefern_df['Net'] < 0,
                #     (wakefern_df['Net'] > 0) & (wakefern_df['Invoice/Credit Memo'].str.match(r'^\d{10}$', na=False)),
                #     (wakefern_df['Net'] > 0) & (~wakefern_df['Invoice/Credit Memo'].str.match(r'^\d{10}$', na=False)),
                # ]
                
                # choices = ['Deduction', 'Invoice Payment', 'Repayment']
                # wakefern_df['BDF Record Type'] = np.select(conditions, choices, default='-')
                
                tolerance_conditions = [
                    (wakefern_df['BDF Record Type'] == 'Deduction') & (wakefern_df['Net'].abs() > 0) & (wakefern_df['Net'].abs() < 200),
                    (wakefern_df['BDF Record Type'] == 'Deduction') & (wakefern_df['Net'].abs() > 200)
                ]
                
                tolerance_choices = ['UT', 'OT']
                
                wakefern_df['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                
                wakefern_df['Date'] = pd.to_datetime(wakefern_df['Date'])
                wakefern_df['BDF Expiry'] = wakefern_df['Date'] + pd.Timedelta(days=45)
                reason_code_conditions = [
                    wakefern_df['Invoice/Credit Memo'].str.match(r'^\d{10}$', na=False),
                    wakefern_df['Invoice/Credit Memo'].str.startswith('RTV', na=False),
                    wakefern_df['Invoice/Credit Memo'].str.contains(r'^\d{5}-\d{5}$', case=False, na=False),
                    wakefern_df['Invoice/Credit Memo'].str.startswith('DC', na=False),
                    wakefern_df['Invoice/Credit Memo'].str.startswith('GM', na=False),
                    wakefern_df['Invoice/Credit Memo'].str.startswith('CPN', na=False),
                ]
                
                reason_code_ID_choices = ['101', '102', '105', '306', '306', '312']
                reason_code_choices = ['Quantity Difference', 'Stock Return', 'Quality/Damaged Goods', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'Coupons']
                description_reason_code_choice = ['SHORTAGE', 'RETURN', 'UNSALEABLES', 'COOP', 'COOP', 'COUPONS']
                wakefern_df['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                wakefern_df['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                wakefern_df['BDF Reason Description'] = np.select(reason_code_conditions, description_reason_code_choice, default='-')
                wakefern_df['BDF Expiry'] = wakefern_df['BDF Expiry'].dt.strftime('%m/%d/%Y')
                for col in ['BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']:
                    wakefern_df[col] = np.where(wakefern_df['BDF Record Type'] == 'Invoice Payment', '', wakefern_df[col])
                
                wakefern_df[['BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']] = wakefern_df[['BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']].replace('-', '')

                wakefern_df.loc[
                    (wakefern_df['BDF Record Type'] == 'Deduction') & (wakefern_df['BDF Reason Code'].str.strip() == '') & (wakefern_df['BDF Reason Code Name'].str.strip() == '') & (wakefern_df['BDF Reason Description'].str.strip() == ''),
                    ['BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                ] = ['306', 'TTC Deduction - Invoice Missing', 'COOP']

                wakefern_df.loc[
                    wakefern_df['Invoice/Credit Memo'].str.startswith('X-'), ['BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                ] = ['101', 'Quantity Difference', 'SHORTAGE']

                wakefern_df.to_excel(os.path.join(self.output_path, fr"WAKE_Remittance_Range_{from_date_value}-{to_date_value}_check_number_{check_num}.xlsx"), index=False)
                await self.info(f"Found: {check_num}")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"WAKE_Remittance_{formatted_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.xlsx') or file.endswith('Version')]
            os.makedirs(os.path.join(self.output_path, 'Remittance Consolidate Version'))
            final_df = pd.DataFrame()
            for file in pdf_files:
                df = pd.read_excel(os.path.join(self.output_path, file))
                final_df = pd.concat([final_df, df], ignore_index=True)
            final_df.to_excel(os.path.join(self.output_path, 'Remittance Consolidate Version', f"WAKE_Remittance_Range_{from_date_value}-{to_date_value}_consolidate.xlsx"), index=False)
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.xlsx') or file.endswith('Version')]
            if len(pdf_files) > 0:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        if pdf_file.endswith('Version'):
                            version_folder_path = os.path.join(self.output_path, 'Remittance Consolidate Version')
                            for foldername, subfolders, filenames in os.walk(version_folder_path):
                                for filename in filenames:
                                    file_path = os.path.join(foldername, filename)
                                    relative_path = os.path.relpath(file_path, self.output_path)
                                    zipf.write(file_path, arcname=relative_path)
                        else:
                            pdf_file_path = os.path.join(self.output_path, pdf_file)
                            zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
                return
        else:
            await self.error(f"Date range difference exceeds 31 days: {delta.days} days")
            return
        
    def is_logged_in(self) -> bool:
        try:
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@name="USERID"]')))
            return False
        except Exception:
            self.driver.switch_to.default_content()
            return True
