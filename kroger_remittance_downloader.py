from datetime import date
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import numpy as np
import os
import zipfile
from accelerators import Accelerator

class KrogerRemittanceAccelerator(Accelerator):
    display_name = 'Remittance Downloader'
    group_name = 'Kroger'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    start_url = "https://partnerpass.krogerapps.com/vendorsso/dashboard"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the mappings provided in the Remittance may not fulfill every reason code. As new or modiied Assignment #s occur please make note of these patterns.</p>
        <br>
        <p><strong>Vendor Code:</strong> KROG</p>
        <p><strong>Vendor Name:</strong> Kroger Company</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://partnerpass.krogerapps.com/">https://partnerpass.krogerapps.com/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from OKTA Verify App.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299335</p>
        <p><strong>SAP Account Name:</strong> KROGER CO</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            await self.info('Starting Accelerator')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_element = "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[3]/div/div[2]/span/input"
                try:
                    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, username_element)))
                    username_input.clear()
                    username_input.send_keys(username)
                except TimeoutException:
                    self.log.debug('username element not found.')
                    return
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='form19']/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", next_button)
                except TimeoutException:
                    self.log.debug('next button not found.')
                try:
                    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                    password_input.clear()
                    password_input.send_keys(password)
                except TimeoutException:
                    self.log.debug('password input element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    verify_password = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", verify_password)
                except TimeoutException:
                    self.log.debug('verify password element not found')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    select_octa_push = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[1]/div[2]/div[2]/a")))
                    self.driver.execute_script("arguments[0].click();", select_octa_push)
                except TimeoutException:
                    self.log.debug('select octa push element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.info('Enter verification code(s) - OTP/MFA/Captcha…')
                try:
                    code = await auth.otp()
                    octa_code = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                    octa_code.send_keys(code)
                    verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", verify_button)
                    await self.info('Valid code entered.')
                except TimeoutException:
                    await self.info('Invalid code entered. Please try again.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                self.log.debug('Please wait, verifying the OTP/MFA code.')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
        except TimeoutException:
            self.log.debug('popup not found...')
        if '/vendorsso/dashboard' in self.driver.current_url:
            await self.info("Great! We're logged in. Let's proceed.")
            self.driver.get("https://partnerpass.lavante.com/sim/supplierDashboard.lvp")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            self.driver.get('https://partnerpass.lavante.com/sim/supplierClaimsPaymentResult.lvp#search')
            await self.info('Searching the portal…')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            self.log.debug('Trying to fill all the required feilds.')
            from_date_str = from_date.strftime('%m/%d/%Y')
            to_date_str = to_date.strftime('%m/%d/%Y')
            read_only = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateFrom"]')))
            self.driver.execute_script("arguments[0].value = arguments[1];", read_only, from_date_str)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateTo"]'))).clear()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateTo"]'))).send_keys(to_date_str)
            await self.info(f'Found Date(s):{from_date_str}-{to_date_str}:')
            refresh_token = False
            try:
                click_on_search = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="claimsPaymentBasicSearch"]')))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_search)
                self.driver.execute_script("arguments[0].click();", click_on_search)
                self.log.debug('click on search button..')
                refresh_token = True
            except TimeoutException:
                self.log.debug("search button not found")
                refresh_token = False
            if not refresh_token:
                await self.log.error("search button not clickable")
                return
            iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
            self.driver.switch_to.frame(iframe_element)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dLabel"]')))
            self.driver.execute_script("arguments[0].click();", button)
            hover_span = self.driver.find_element(By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/a')
            ActionChains(self.driver).move_to_element(hover_span).perform()
            tocken_data = False
            try:
                click_download_csv = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/ul/li[2]/a')))
                tocken_data = True
            except TimeoutException:
                self.log.debug('No Data Found for given date Range...')
                tocken_data = False
            if not tocken_data:
                self.driver.switch_to.default_content()
                iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
                self.driver.switch_to.frame(iframe_element)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dLabel"]')))
                self.driver.execute_script("arguments[0].click();", button)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                click_download_csv = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/ul/li[2]/a')))
            except TimeoutException:
                await self.error('No Data Found for given date Range...')
                return
            hover_span = self.driver.find_element(By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/a')
            ActionChains(self.driver).move_to_element(hover_span).perform()
            self.driver.execute_script("arguments[0].click();", click_download_csv)
            await self.info('Processing the data…')
            await self.wait_for_output(lambda files: 'BasicSupplierPaymentList.csv' in files)
            self.log.debug("[+] Stage Download output")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            begin_date = from_date_str.replace('/', '-')
            last_date = to_date_str.replace('/', '-')
            remittance_path = os.path.join(self.output_path, 'Remittance_with_Payment_Ref_No')
            raw_data_remittance_path = os.path.join(remittance_path, 'Raw Data Remittance')
            os.makedirs(remittance_path, exist_ok=True)
            os.makedirs(raw_data_remittance_path, exist_ok=True)
            for filename in os.listdir(self.output_path):
                if filename.startswith('BasicSupplierPaymentList'):
                    new_filename = f'KROG_Remittance_Date_{begin_date}_to_{last_date}_file_{filename}'
                    new_file_path = os.path.join(self.output_path, new_filename)
                    os.rename(os.path.join(self.output_path, filename), new_file_path)
                    file_path = os.path.join(self.output_path, new_filename)
                    file_data = pd.read_csv(file_path, skiprows=1)
                    columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code', 'BDF Reason Code Name', 'BDF Reason Code Description']
                    for col in columns_addon:
                        file_data[f'{col}'] = ''
                    file_data['Invoice Number'] = file_data['Invoice Number'].astype(str)
                    conditions = [
                        file_data['Net invoice amount'] < 0,
                        (file_data['Net invoice amount'] > 0) & (file_data['Invoice Number'].str.match(r'^\d{10}$', na=False)),
                        (file_data['Net invoice amount'] > 0) & (~file_data['Invoice Number'].str.match(r'^\d{10}$', na=False))
                    ]
                    choices = ['Deduction', 'Invoice Payment', 'Repayment']
                    file_data['BDF Record Type'] = np.select(conditions, choices, default='-')
                    tolerance_conditions = [
                        (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net invoice amount'].abs() > 0) & (file_data['Net invoice amount'].abs() < 200),
                        (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net invoice amount'].abs() > 200)
                    ]
                    tolerance_choices = ['UT', 'OT']
                    file_data['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                    
                    file_data['Invoice Date'] = pd.to_datetime(file_data['Invoice Date'])
                    file_data['BDF Expiry'] = file_data['Invoice Date'] + pd.Timedelta(days=45)
                    await self.info('Data Transformation...')
                    reason_code_conditions = [
                        file_data['Invoice Number'].str.endswith('CM', na=False),
                        file_data['Invoice Number'].str.contains('-V', case=False, na=False),
                        file_data['Invoice Number'].str.contains('-NC-', case=False, na=False),
                        file_data['Invoice Number'].str.startswith('060-C', na=False),
                        file_data['Invoice Number'].str.startswith('092-R', na=False),
                        file_data['Invoice Number'].str.startswith('092-A', na=False),
                        file_data['Invoice Number'].str.startswith('5', na=False)
                    ]
                    reason_code_choices = ["101", "105", "108", "306", "306", "306", "312"]
                    reason_code_ID_choices = ['Quantity Difference', 'Quality/Damaged Goods', 'DCS Penalties / Fine', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'TTC Deduction - Invoice Missing', 'Coupons']
                    reason_code_description = ["shortages", "ddd = Division", "fees", "COOP", "post-audit", "Claim trade promo or discount, review for accuracy", "coupon"]
                    file_data['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                    file_data['BDF Reason Code Name'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                    file_data['BDF Reason Code Description'] = np.select(reason_code_conditions, reason_code_description, default='-')
                    # os.rename(file_path, os.path.join(raw_data_remittance_path, new_filename))
                    await self.info("Processing...")
                    if not isinstance(file_data, pd.DataFrame):
                        raise ValueError("Loaded data is not a DataFrame")
                    if 'Payment Ref No' not in file_data.columns:
                        raise KeyError("Column 'Payment Ref No' not found in the DataFrame")
                    df_1 = file_data.groupby('Payment Ref No')
                    df_2 = {group: df_1.get_group(group) for group in df_1.groups}
                    for Payment_Ref_No in df_2:
                        filtered_df = df_2[Payment_Ref_No]
                        csv_filename = f"KROG_Remittance_Date_{begin_date}-{last_date}_Payment_Ref_No_{Payment_Ref_No}_{filename}"
                        filtered_df.to_csv(os.path.join(remittance_path, csv_filename), index=False)
                    file_data.to_csv(os.path.join(raw_data_remittance_path, new_filename), index=False)
                    zip_filename = os.path.join(remittance_path, f"KROG_Remittance_Date_{begin_date}_to_{last_date}.zip")
                    csv_files = [file for file in os.listdir(remittance_path) if file.endswith('.csv')]
                    with zipfile.ZipFile(f'{zip_filename}', 'w') as zipf:
                        for csv_file in csv_files:
                            csv_file_path = os.path.join(remittance_path, csv_file)
                            zipf.write(csv_file_path, arcname=csv_file)
                            os.remove(csv_file_path)  # Remove CSV file after adding to zip
                        for root, dirs, files in os.walk(raw_data_remittance_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, remittance_path)
                                zipf.write(file_path, arcname)
                    await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
                    return f'{zip_filename}'
            else:
                await self.error('Invalid! Not found. Please try again with Date range.')
                return
        else:
            await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
            return

    def is_logged_in(self) -> bool:
        return "https://okta.supplier-prod.kroger.com/oauth2/" in self.driver.current_url
