from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
from enum import Enum
from selenium.webdriver.common.keys import Keys
import pandas as pd
import numpy as np


class SelectSearchCriteria(str, Enum):
    LAST_01 = "Last 1 Day"
    LAST_03 = "Last 3 Days"
    LAST_07 = "Last 7 Days"
    LAST_10 = "Last 10 Days"
    LAST_15 = "Last 15 days"

class WALRemittanceAccelerator(Accelerator):
    display_name = "Remittance Downloader (RetailLink)"
    group_name = "Walmart Stores"
    start_url = "https://retaillink2.wal-mart.com/"
    input_display_names = {'Select_Search_Criteria': 'Select Check Date Range'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> TBD</p>
        <br>
        <p><strong>Vendor Code:</strong> WALM</p>
        <p><strong>Vendor Name:</strong> Walmart Stores</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://retaillink.login.wal-mart.com/">https://retaillink.login.wal-mart.com/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299388</p>
        <p><strong>SAP Account Name:</strong> WAL-MART STORES INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, Select_Search_Criteria: SelectSearchCriteria) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Starting Accelerator...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="uname"]')))
                username_input.clear()
                username_input.send_keys(username)
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="pwd"]')))
                password_input.clear()
                password_input.send_keys(password)
                submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="loginBtn"]')))
                submit.click()
                try:
                    varify_with_message_OTP = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Verify with Text Message"]')))
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
                varify_with_message_OTP.click()
                try:
                    otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                    await self.info('Success!, OTP is successfully Generated.')
                    await self.info('Enter verification code(s) - OTP/MFA/Captcha…')
                except TimeoutException:
                    await self.info('Failed!, OTP is Not Generated.')
                    return
                otp_input = await auth.otp()
                otp_input_field.clear()
                otp_input_field.send_keys(otp_input)
                submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
                submit_otp.click()
                await self.info('Please wait!, validating OTP.')
                await self.sleep(8)
                attempts = 1
                while "/mfa?" in self.driver.current_url:
                    await self.info(f'OTP, Attemp - {attempts}/5.')
                    if attempts >= 5:
                        await self.error(f'Failed to submit OTP after {attempts} attempts')
                        return
                    try:
                        otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                        await self.info('Success!, OTP is successfully Generated.')
                    except TimeoutException:
                        await self.info('Failed!, OTP is Not Generated.')
                        return
                    otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
                    otp_input_field.clear()
                    for i in range(1, 20):
                        otp_input_field.send_keys(Keys.BACKSPACE)
                    otp_input = await auth.otp()
                    otp_input_field.send_keys(otp_input)
                    submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
                    submit_otp.click()
                    await self.sleep(8)
                    attempts += 1
                try:
                    WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get('https://retaillink2.wal-mart.com/apis/ChecksSearch.aspx')
                    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "MainContent_ddlVendor")])')))
                    await self.info("Great! We're logged in. Let's proceed.")
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
        await self.info("Please wait, we're processing the request...")
        await self.sleep(6)
        try:
            await self.info('Checking Session if Required OTP ?...')
            varify_with_message_OTP = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Verify with Text Message"]')))
            varify_with_message_OTP.click()
        except TimeoutException:
            await self.info('Recalling session, No need credentials')
        await self.sleep(6)
        attempts = 1
        while "/mfa?" in self.driver.current_url:
            await self.info(f'Need OTP, with  Attemp - {attempts}/5.')
            if attempts >= 5:
                await self.error(f'Failed to submit OTP after {attempts} attempts')
                return
            otp_input_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="code"]')))
            otp_input_field.clear()
            for i in range(1, 20):
                otp_input_field.send_keys(Keys.BACKSPACE)
            otp_input = await auth.otp()
            otp_input_field.send_keys(otp_input)
            submit_otp = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Submit"]')))
            submit_otp.click()
            await self.sleep(8)
            attempts += 1
        await self.info('Searching the portal…')
        WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get('https://retaillink2.wal-mart.com/apis/ChecksSearch.aspx')
        WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        drop_doown = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "MainContent_ddlVendor")])')))
        drop_doown.click()
        select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='051300 - BEIERSDORF INC (US)']")))
        select_vendor.click()
        
        search = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Search"]')))
        search.click()
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/fieldset/div/table[2]/tbody[1]/tr/td[1]/a/label')))
        except TimeoutException:
            await self.error('No record found..')
            return
        
        ammount = []
        che_in_date = []
        check_in = []

        if Select_Search_Criteria == SelectSearchCriteria.LAST_01:
            target = 1
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_03:
            target = 3
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_07:
            target = 7
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_10:
            target = 10
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_15:
            target = 15

        for label in range(1, int(target) + 1):
            await self.sleep(1)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            check_number = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div/div/fieldset/div/table[2]/tbody[{label}]/tr/td[1]/a/label')))
            check_date = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div/div/fieldset/div/table[2]/tbody[{label}]/tr/td[2]'))).text
            check_ammount = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div/div/fieldset/div/table[2]/tbody[{label}]/tr/td[3]'))).text
            check_nm = check_number.text
            check_in.append(check_nm)
            che_in_date.append(check_date)
            ammount.append(check_ammount)
        await self.info(f'Found Date(s): {Select_Search_Criteria.value}')
        account_table = pd.DataFrame(data={'Check Number': check_in, 'Check Date': che_in_date, 'Amount': ammount})
        for index, data in account_table.iterrows():
            ch_num = data['Check Number']
            ch_date = data['Check Date']
            ch_amt = data['Amount']
            await self.info(f'Processing: {ch_num}')
            file_url = f'https://retaillink2.wal-mart.com/apis/CheckDetails.aspx?vndrNbr=051300&checkNbr={ch_num}&checkDate={ch_date}&src=CheckList'
            self.driver.get(file_url)
            await self.sleep(5)
            while not os.path.isfile(os.path.join(self.output_path, f'Check_{ch_num}.xls')):
                export_file = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='btnExport']")))
                export_file.click()
                await self.sleep(3)
            os.rename(os.path.join(self.output_path, f'Check_{ch_num}.xls'), os.path.join(self.output_path, f'WALM-RL_Remittance_{target}-days-Check_{ch_num}.xls'))
            fresh_data = pd.read_html(os.path.join(self.output_path, f'WALM-RL_Remittance_{target}-days-Check_{ch_num}.xls'))
            dataframe_clean = fresh_data[0]
            walmart_summed_df = dataframe_clean.groupby(['Invoice Number', 'DEDUCTION CODE'], as_index=False)['Amount Paid($)'].sum()
            walmart_summed_df.rename(columns={'Amount Paid($)': 'updated_amount'}, inplace=True)

            walmart_df = pd.merge(dataframe_clean, walmart_summed_df, on=['Invoice Number', 'DEDUCTION CODE'], how='left')
            walmart_df['updated_amount'] = walmart_df['updated_amount'].fillna(walmart_df['Amount Paid($)'])
            columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Description']
            for col in columns_addon:
                walmart_df[f'{col}'] = ''
            walmart_df['updated_amount'] = walmart_df['updated_amount'].astype(str)
            walmart_df['updated_amount'] = walmart_df['updated_amount'].str.replace(',', '')
            walmart_df['updated_amount'] = walmart_df['updated_amount'].astype('float')
            walmart_df['Invoice Number'] = walmart_df['Invoice Number'].astype(str)
            conditions = [
                walmart_df['updated_amount'] < 0,
                (walmart_df['updated_amount'] > 0) & (walmart_df['Invoice Number'].str.match(r'^\d{10}$', na=False)),
                (walmart_df['updated_amount'] > 0) & (~walmart_df['Invoice Number'].str.match(r'^\d{10}$', na=False)),
            ]

            choices = ['Deduction', 'Invoice Payment', 'Repayment']
            walmart_df['BDF Record Type'] = np.select(conditions, choices, default='-')


            tolerance_conditions = [
                (walmart_df['BDF Record Type'] == 'Deduction') & (walmart_df['updated_amount'].abs() > 0) & (walmart_df['updated_amount'].abs() < 200),
                (walmart_df['BDF Record Type'] == 'Deduction') & (walmart_df['updated_amount'].abs() > 200)
            ]

            tolerance_choices = ['UT', 'OT']

            walmart_df['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

            walmart_df['Invoice Date'] = pd.to_datetime(walmart_df['Invoice Date'])
            walmart_df['BDF Expiry'] = walmart_df['Invoice Date'] + pd.Timedelta(days=45)
            reason_code_conditions = [
                walmart_df['DEDUCTION CODE'].str.contains('0022', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0024', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0028', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0025', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0021', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0092', case=False, na=False),
                walmart_df['Invoice Number'].str.startswith('1220', na=False),
                walmart_df['Invoice Number'].str.startswith('513', na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0060', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0044', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0150', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0110', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0130', case=False, na=False),
                walmart_df['DEDUCTION CODE'].str.contains('0100', case=False, na=False),
                walmart_df['Invoice Number'].str.startswith('700', na=False),
            ]

            reason_code_ID_choices = ['101', '101', '101', '101', '101', '102', '105', '108', '108', '108', '108', '201', '201', '201', '302']
            reason_code_choices = ['Quantity Difference', 'Quantity Difference', 'Quantity Difference', 'Quantity Difference', 'Quantity Difference', 'Stock Return', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'DCS Penalties / Fine', 'DCS Penalties / Fine', 'DCS Penalties / Fine', 'Price Difference', 'Price Difference', 'Price Difference', 'Payment Advice Missing']
            description_reason_code_choice = ['MERCHANDISE BILLED NOT SHIPPED [0022]', 'CARTON SHORTAGE FREIGHT BILL SIGNED SHORT [0024]', 'CARTON DAMAGE - FRT. BILL SIGNED DAMAGED [0028]', 'POD/NO MERCHANDISE RECEIVED FOR INVOICE [0025]', 'CONCEALED SHORTAGE [0021]', 'MERCHANDISE RETURN - OVERSTOCK/RECALL [0092]', 'DEFECTIVE MERCHANDISE ALLOWANCE [0059]', 'Non Invoice, 9 digits, begins with 513', 'HANDLING CHARGE AS DOCUMENTED [0060]', 'FREIGHT ON RETURNED MERCHANDISE [0044]', 'SOFTGOODS DEFECTIVE ALLOWANCE [0150] ', 'PRICE DIFFERENCE BETWEEN PO AND INV [0110]', 'SUBSTITUTION OVERCHARGE [0130]', 'PRICE DIFFERENCE AS DOCUMENTED [0100]', 'Starts with "700" and is 12-digits']
            walmart_df['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
            walmart_df['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_choices, default='-')
            walmart_df['BDF Reason Description'] = np.select(reason_code_conditions, description_reason_code_choice, default='-')
            walmart_df.rename(columns={'updated_amount': 'Clubed Amount Paid($)'}, inplace=True)
            walmart_df['Check Number'] = ch_num
            walmart_df['Check Date'] = ch_date
            walmart_df['Check Amount'] = ch_amt
            walmart_df.to_excel(os.path.join(self.output_path, f'WALM_RL_Remittance_{target}_days_Check_{ch_num}.xlsx'), index=False)
            await self.info(f'Found: {ch_num}')
            
        account_table.to_csv(os.path.join(self.output_path, f'WALM_RL_Remittance_Account_details_{target}_days.csv'), index=False)
        all_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv') or file.endswith('.xlsx') and file.startswith('WALM')]
        if all_files:
            await self.info("Processing the data…")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"WALM-RL_Remittance {formatted_date}")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for down_file in all_files:
                    down_file_path = os.path.join(self.output_path, down_file)
                    zipf.write(down_file_path, arcname=down_file)
            await self.info("Success! Please click 'Download' to receive files.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        
    def is_logged_in(self) -> bool:
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@data-automation-id="uname"]')))
            return False
        except Exception:
            return True
