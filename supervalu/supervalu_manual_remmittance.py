from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.common.exceptions import TimeoutException
import os
from accelerators.implementations.supervalu.base import SupervaluBase
import pandas as pd
import numpy as np
import zipfile
from datetime import datetime

class SupervalueRemittanceManualAccelerator(SupervaluBase):
    display_name = 'Remittance by Specific Dates'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> SUPR</p>
        <p><strong>Vendor Name:</strong> Supervalu Inc.</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://myhome.svharbor.com/content/svpublic/home.html">https://myhome.svharbor.com/content/svpublic/home.html</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299678</p>
        <p><strong>SAP Account Name:</strong> SUPERVALU INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        await self.info("Starting Accelerator...")
        if not await self.login():
            return
        from_date_field = f"{from_date.month}/{from_date.day}/{from_date.year}"
        to_date_field = f"{to_date.month}/{to_date.day}/{to_date.year}"
        wait = WebDriverWait(self.driver, 30)

        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[text() ="Go"]')))
        await self.info('Searching the portal…')
        xpath_range = '//*[@name="dateCriteria"][@value="manual"]'

        input_doc_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="docNum1"]')))
        input_doc_field.clear()

        wait.until(EC.element_to_be_clickable((By.XPATH, f'{xpath_range}'))).click()
        from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="f_date_a"]')))
        from_date_input.clear()
        from_date_input.send_keys(from_date_field)

        to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="f_date_b"]')))
        to_date_input.clear()
        to_date_input.send_keys(to_date_field)

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Go"]'))).click()
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Export All"]'))).click()
        except TimeoutException:
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        
        files = await self.wait_for_output(lambda files: 'epassSearchResults.csv' in files)
        from_date = from_date.strftime("%m%d%Y")
        to_date = to_date.strftime("%m%d%Y")
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"SUPR_Remittance_Date_{from_date}-{to_date}_{file}"))
            dataframe_super = pd.read_csv(os.path.join(self.output_path, f"SUPR_Remittance_Date_{from_date}-{to_date}_{file}"), skiprows=4)
            columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
            dataframe_super['Document #'] = dataframe_super['Document #'].str.replace('=', '')
            dataframe_super['Document #'] = dataframe_super['Document #'].str.replace('"', '')
            dataframe_super['Document #'] = dataframe_super['Document #'].str.replace("'", '')

            for col in columns_addon:
                dataframe_super[f'{col}'] = ''
            conditions = [
                dataframe_super['Net Amount'] < 0,
                (dataframe_super['Net Amount'] > 0) & (dataframe_super['Document #'].str.match(r'^\d{10}$', na=False)),
                (dataframe_super['Net Amount'] > 0) & (~dataframe_super['Document #'].str.match(r'^\d{10}$', na=False)),
            ]

            choices = ['Deduction', 'Invoice Payment', 'Repayment']

            dataframe_super['BDF Record Type'] = np.select(conditions, choices, default='-')


            tolerance_conditions = [
                (dataframe_super['BDF Record Type'] == 'Deduction') & (dataframe_super['Net Amount'].abs() > 0) & (dataframe_super['Net Amount'].abs() < 200),
                (dataframe_super['BDF Record Type'] == 'Deduction') & (dataframe_super['Net Amount'].abs() > 200)
            ]

            tolerance_choices = ['UT', 'OT']

            dataframe_super['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

            dataframe_super['Document Date'] = pd.to_datetime(dataframe_super['Document Date'])
            dataframe_super['BDF Expiry'] = dataframe_super['Document Date'] + pd.Timedelta(days=45)

            reason_code_conditions = [
                dataframe_super['Document #'].str.endswith('A', na=False),
                dataframe_super['Document #'].str.startswith('99PRC', na=False),
                dataframe_super['Document #'].str.startswith('99S', na=False),
                dataframe_super['Document #'].str.contains('B', case=False, na=False),
                dataframe_super['Document #'].str.endswith('FI', na=False),
                dataframe_super['Document #'].str.contains('J', case=False, na=False),
                dataframe_super['Document #'].str.contains('Q', case=False, na=False)
            ]

            reason_code_ID_choices = ['101', '105', '306', '306', '306', '306', '306']
            reason_code_choices = ['Quantity Difference', 'Quality/Damaged Goods', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing']
            reason_code_description = ['Shortage', 'Unsaleable', 'Co-Op', 'Co-Op', 'Co-Op', 'Co-Op', 'Co-Op']
            dataframe_super['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
            dataframe_super['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
            dataframe_super['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
            dataframe_super['BDF Record Type'] = np.where(dataframe_super['BDF Reason Code Name'].str.contains('Deduction', case=False, na=False), 'Deduction', dataframe_super['BDF Record Type'])
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            output_zip = os.path.join(self.output_path, f"SUPR_Remittance_{formatted_date}.zip")
            os.makedirs(os.path.join(self.output_path, 'Remittance with Document Date'))
            os.makedirs(os.path.join(self.output_path, 'Consolidate Version'))
            from_date_value = from_date.replace('/', '')
            to_date_value = to_date.replace('/', '')
            df_1 = dataframe_super.groupby('Document Date')
            df_2 = {group: df_1.get_group(group) for group in df_1.groups}
            download_focus = False
            for document_date in df_2:
                filtered_df = df_2[document_date]
                download_focus = True
                document_date = str(document_date).replace(' 00:00:00', '')
                document_date = str(document_date).replace('-', '')
                filtered_df.to_csv(os.path.join(self.output_path, 'Remittance with Document Date', f"SUPR_Remittance_with_document_date_{document_date}_date_range_{from_date_value}_{to_date_value}_{file}"), index=False)
            dataframe_super.to_csv(os.path.join(self.output_path, 'Consolidate Version', f"SUPR_Remittance_Consolidate_{from_date_value}_{to_date_value}_{file}"), index=False)
            
            if download_focus:
                await self.info('Processing the data…')
                all_dirs = [file for file in os.listdir(self.output_path) if file.endswith('Document Date') or file.endswith('Version')]
                with zipfile.ZipFile(output_zip, 'w') as zipf:
                    for all_dir in all_dirs:
                        if all_dir.endswith('Document Date'):
                            version_folder_path = os.path.join(self.output_path, 'Remittance with Document Date')
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
