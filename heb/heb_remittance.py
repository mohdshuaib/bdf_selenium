from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
import os
from accelerators.implementations.heb.base import HEBBase
import pandas as pd
import numpy as np

class HEBRemittanceAccelerator(HEBBase):
    display_name = 'Remittance Downloader'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> HEBG</p>
        <p><strong>Vendor Name:</strong> H.E. Butt Grocery</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://avp.heb.com/VendorPortal/loginPage">https://avp.heb.com/VendorPortal/loginPage</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299284</p>
        <p><strong>SAP Account Name:</strong> H E BUTT GROCERY CO</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        await self.info('Starting Accelerator...')
        delta = to_date - from_date
        if delta.days <= 31:
            if not await self.login():
                return
            
            wait = WebDriverWait(self.driver, 30)
            await self.info("Please wait, we're processing the request...")
            search_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="search-indicator"]')))
            search_tab.click()
            payment = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@id="payment"]')))
            payment.click()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="customFilter"]/span'))).click()
            from_date_value = f"{from_date.month}/{from_date.day}/{from_date.year}"
            to_date_value = f"{to_date.month}/{to_date.day}/{to_date.year}"
            self.log.debug(f"Date Range from {from_date} : To {to_date} format MM/DD/YYYY")
            from_date_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="dateFrom"]')))
            from_date_field.clear()
            from_date_field.send_keys(from_date_value)
            to_date_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="dateTo"]')))
            to_date_field.clear()
            to_date_field.send_keys(to_date_value)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="customDateSearchButton"]')))
            button.click()
            await self.info(f'Found Date(s): {from_date_value} - {to_date_value}')
            export_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_4"]')))
            export_button.click()
            details = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_6"]')))
            details.click()
            my_download = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="myDownloads-indicator"]')))
            my_download.click()
            file_download = WebDriverWait(self.driver, 250).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div[3]/div[1]/div[1]/a')))
            file_download.click()
            files = await self.wait_for_output(lambda files: any('.tmp' not in file for file in files))
            files = await self.wait_for_output(lambda files: any('.crdownload' not in file for file in files))
            from_date = from_date.strftime("%m%d%Y")
            to_date = to_date.strftime("%m%d%Y")
            for file in files:
                await self.info('Processing the data…')
                os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"HEBG_Remittance_Date_{from_date}-{to_date}_{file}"))
                dataframe_heb = pd.read_csv(os.path.join(self.output_path, f"HEBG_Remittance_Date_{from_date}-{to_date}_{file}"))
                columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
                for col in columns_addon:
                    dataframe_heb[f'{col}'] = ''
                dataframe_heb['Paid amount'] = dataframe_heb['Paid amount'].astype(str)
                dataframe_heb['Paid amount'] = dataframe_heb['Paid amount'].str.replace(',', '')
                dataframe_heb['Paid amount'] = dataframe_heb['Paid amount'].astype('float')

                conditions = [
                    dataframe_heb['Paid amount'] < 0,
                    (dataframe_heb['Paid amount'] > 0) & (dataframe_heb['Invoice number'].str.match(r'^\d{10}$', na=False)),
                    (dataframe_heb['Paid amount'] > 0) & (~dataframe_heb['Invoice number'].str.match(r'^\d{10}$', na=False)),
                ]

                choices = ['Deduction', 'Invoice Payment', 'Repayment']

                dataframe_heb['BDF Record Type'] = np.select(conditions, choices, default='-')


                tolerance_conditions = [
                    (dataframe_heb['BDF Record Type'] == 'Deduction') & (dataframe_heb['Paid amount'].abs() > 0) & (dataframe_heb['Paid amount'].abs() < 200),
                    (dataframe_heb['BDF Record Type'] == 'Deduction') & (dataframe_heb['Paid amount'].abs() > 200)
                ]

                tolerance_choices = ['UT', 'OT']

                dataframe_heb['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

                dataframe_heb['Payment date'] = pd.to_datetime(dataframe_heb['Payment date'])
                dataframe_heb['BDF Expiry'] = dataframe_heb['Payment date'] + pd.Timedelta(days=45)

                reason_code_conditions = [
                    dataframe_heb['Invoice number'].str.endswith('S', na=False),
                    dataframe_heb['Invoice number'].str.startswith('MR', na=False),
                    dataframe_heb['Invoice number'].str.startswith('RGC', na=False),
                    dataframe_heb['Invoice number'].str.startswith('UNL', na=False),
                    dataframe_heb['Invoice number'].str.endswith('L', na=False),
                    dataframe_heb['Invoice number'].str.startswith('CMS', na=False),
                    dataframe_heb['Invoice number'].str.startswith('CPN', na=False),
                    dataframe_heb['Invoice number'].str.startswith('ECOM', na=False),
                    dataframe_heb['Invoice number'].str.startswith('FLAT', na=False),
                    dataframe_heb['Invoice number'].str.startswith('MD', na=False),
                    dataframe_heb['Invoice number'].str.endswith('OI', na=False),
                    dataframe_heb['Invoice number'].str.startswith('OMS', na=False),
                    dataframe_heb['Invoice number'].str.startswith('ONL', na=False),
                    dataframe_heb['Invoice number'].str.startswith('SHF', na=False),
                    dataframe_heb['Invoice number'].str.startswith('CB', na=False),
                ]
                reason_code_ID_choices = ['101', '102', '105', '108', '201', '306', '306', '306', '306', '306', '306', '306', '306', '306', '312']
                reason_code_choices = ['Quantity Difference', 'Stock Return ', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'Price Difference', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'Coupons']
                reason_code_description = ['INVOICE # WITH AN S = SHORTAGE', 'RETURNS', 'UNSALEABLES', 'FEE/FINE', 'PRICING', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COUPONS']
                dataframe_heb['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                dataframe_heb['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                dataframe_heb['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
                dataframe_heb.to_csv(os.path.join(self.output_path, f"HEBG_Remittance_Date_{from_date}-{to_date}_{file}"), index=False)
                await self.info("Success! Please click 'Download' to receive files.")
            return os.listdir(self.output_path)[0] if len(files) else None
        else:
            await self.error(f"Date range difference exceeds 31 days: {delta.days} days")
            return
