from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from accelerators import Accelerator
import os
import zipfile
from datetime import date, datetime

 
class MeijerRemittanceAccelerator(Accelerator):
    display_name = "Remittance Downloader"
    group_name = "Meijer"
    start_url = "https://vendornet.meijer.com/Welcome"
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Remittance</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the Meijer portal will return only the most recent report by Date</p>
        <br>
        <p><strong>Vendor Code:</strong> MEIJ</p>
        <p><strong>Vendor Name:</strong> Meijer Inc.</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://vendornet.meijer.com/">https://vendornet.meijer.com/</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299392</p>
        <p><strong>SAP Account Name:</strong> MEIJER INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, user_date: date) -> str:
        wait = WebDriverWait(self.driver, 30)
        async with self.authenticator() as auth:
            month, day, year = user_date.strftime("%b %d %Y").split()
            await self.info('Running...')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                user_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@autocomplete='username']")))
                user_input.clear()
                user_input.send_keys(username)
                auth_tocken = False
                try:
                    pass_input = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    auth_tocken = True
                except TimeoutException:
                    auth_tocken = False
                    self.log.debug('method change for login...')
                if not auth_tocken:
                    submit_login = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]')))
                    submit_login.click()
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    pass_input.clear()
                    pass_input.send_keys(password)
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                else:
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    pass_input.clear()
                    pass_input.send_keys(password)
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                await self.info('Please wait...')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! You've successfully logged into the targeted portal.")
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        except TimeoutException:
            self.log.debug('order_payment element not found')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        order_payment = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        self.driver.execute_script("arguments[0].click();", order_payment)
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        except TimeoutException:
            self.log.debug('payment_claims_drop element not found')
        payment_claims_drop = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        self.driver.execute_script("arguments[0].click();", payment_claims_drop)
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        except TimeoutException:
            self.log.debug('account_pay_query element not found')
        account_pay_query = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        self.driver.execute_script("arguments[0].click();", account_pay_query)
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/p[5]/a")))
        except TimeoutException:
            self.log.debug('for switching  element not found')
        anchor_element = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/p[5]/a')))
        url = anchor_element.get_attribute('href')
        self.log.debug(f"URL: {url}")
        self.start_url = url
        async with self.authenticator() as auth:
            await self.info('check for the Attempting to login…')
            try:
                username_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[1]")))
                username, password = await auth.userpass()
                username_element.send_keys(username)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                password_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[2]")))
                password_element.send_keys(password)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                click_signon = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/a")))
                self.driver.execute_script("arguments[0].click();", click_signon)
            except TimeoutException:
                self.log.debug('Not required..')
            await self.info('check for the Attempting to login…')
            try:
                username_element = WebDriverWait(self.driver, 13).until(EC.element_to_be_clickable((By.XPATH, '//*[@type="text"] [@autocomplete="username"]')))
                username, password = await auth.userpass()
                username_element.send_keys(username)
                click_next = WebDriverWait(self.driver, 13).until(EC.element_to_be_clickable((By.XPATH, '//*[@class="button button-primary"]')))
                self.driver.execute_script("arguments[0].click();", click_next)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                password_element = WebDriverWait(self.driver, 13).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="password"] [@name="credentials.passcode"]')))
                password_element.send_keys(password)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                verify_button = WebDriverWait(self.driver, 13).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"] [@value="Verify"]')))
                self.driver.execute_script("arguments[0].click();", verify_button)
            except TimeoutException:
                self.log.debug('Not required..')
        await self.info('session refreshed not required further login..')
        await self.sleep(3)
        try:
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
            select_vendor.click()
        except TimeoutException:
            self.log.debug('select_vendor element not found.')
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
        except TimeoutException:
            self.log.info('for choose_vendor  element not found')
        choose_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
        choose_vendor.click()
        await self.sleep(2)
        day = int(day)
        select_year = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="cboYear"]')))
        select_year.send_keys(year)
        select_month = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="cboMonth"]')))
        select_month.send_keys(month)
        select_day = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="cboDay"]')))
        select_day.send_keys(day)
        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"] [@name="cmdSubmit"]')))
        submit_button.click()

        def export_files():
            date_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//td/a[starts-with(@id, 'grdResult__ctl')]")))
            for i in range(len(date_elements)):
                date_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//td/a[starts-with(@id, 'grdResult__ctl')]")))
                date_elements[i].click()
                clickexport = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lnkExcelExport1"]')))
                clickexport.click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                clickreturn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lnkDateSelect1"]')))
                clickreturn.click()
        export_files()
        await self.wait_for_output(lambda files: any(file.startswith("Remittance") for file in files))
        self.log.debug("[+] Stage Download output")
        counter = 1
        for filename in os.listdir(self.output_path):
            if filename.startswith('Remittance'):
                new_filename = f'MEIJ_Remittance_file_{counter}_Remittance_details.csv'
                os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, new_filename))
                counter += 1
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f'MEIJ_Remittance_{current_date}')
        csv_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
        if csv_files:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in csv_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been extracted from the portal. Click the button to download")
            return f'{zip_filename}.zip'
        else:
            await self.error("try 'Invalid! Data not found. Please try again with valid Date.")
            return
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 19)
        try:
            click_log = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Log In')]")))
            click_log.click()
        except TimeoutException:
            self.log.debug('click_log button not found')
        return 'https://vendornet.meijer.com/Welcome' in self.driver.current_url
