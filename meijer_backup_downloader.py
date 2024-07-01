from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from accelerators import Accelerator
from datetime import datetime
import os
import zipfile
import img2pdf

class MeijerBackupAccelerator(Accelerator):
    display_name = "Meijer Backup Downloader"
    group_name = "Meijer"
    start_url = "https://vendornet.meijer.com/Welcome"
    input_display_names = {'invoice_numbers': 'Enter INVOICE#s'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> TBD</p>
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
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        async with self.authenticator() as auth:
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
                try:
                    await self.info('Please wait...')
                    WebDriverWait(self.driver, 10).until(EC.invisibility_of_element((By.XPATH, '//*[@type="submit"]')))
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! You've successfully logged into the targeted portal.")
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        except TimeoutException:
            self.log.info('order_payment element not found')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        order_payment = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        order_payment.click()
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        except TimeoutException:
            self.log.info('payment_claims_drop element not found')
        payment_claims_drop = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        payment_claims_drop.click()
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        except TimeoutException:
            self.log.info('account_pay_query element not found')
        account_pay_query = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        account_pay_query.click()
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/p[5]/a")))
        except TimeoutException:
            self.log.info('for switching  element not found')
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/p[5]/a'))).click()
        self.driver.switch_to.window(self.driver.window_handles[-1])
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            username_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[1]")))
            username, password = await auth.userpass()
            username_element.send_keys(username)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            password_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[2]")))
            password_element.send_keys(password)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            click_signon = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/a")))
            click_signon.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.info('session refreshed')
        except TimeoutException:
            self.log.debug('username password not required..')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
        except TimeoutException:
            self.log.info('for select_vendor  element not found')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
        select_vendor.click()
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
        except TimeoutException:
            self.log.info('for choose_vendor  element not found')
        choose_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
        choose_vendor.click()
        for invoice_number in set(list(invoice_numbers)):
            if len(str(invoice_number)) > 7:
                try:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[2]/td[2]/input")))
                except TimeoutException:
                    self.log.info('document_number  element not found')
                document_number = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[2]/td[2]/input")))
                document_number.clear()
                document_number.send_keys(invoice_number)
                try:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[8]/td/input[1]")))
                except TimeoutException:
                    self.log.info('submit_button  element not found')
                submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[8]/td/input[1]")))
                submit_button.click()
                try:
                    click_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='grdResults']/tbody/tr[2]/td[4]/a")))
                    click_invoice.click()
                except TimeoutException:
                    self.log.info('click_invoice element not found')
                    await self.info(f'Invoice data for {invoice_number} was not found')
                    continue
                output_path = os.path.join(self.output_path)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                self.driver.save_screenshot(os.path.join(output_path, "screenshot.png"))
                input_image_path = os.path.join(output_path, "screenshot.png")
                output_pdf_path = os.path.join(output_path, "screenshot.pdf")
                with open(input_image_path, "rb") as image_file:
                    pdf_bytes = img2pdf.convert(image_file.read())
                with open(output_pdf_path, "wb") as pdf_file:
                    pdf_file.write(pdf_bytes)
                os.remove(input_image_path)
                self.driver.switch_to.window(self.driver.window_handles[1])
                try:
                    WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/p[4]/a")))
                except TimeoutException:
                    self.log.info('back_to_selection  element not found')
                back_to_selection = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/p[4]/a")))
                back_to_selection.click()
                await self.info('back_to_selection')
                for filename in os.listdir(output_path):
                    if filename.startswith('screenshot'):
                        old_file_path = os.path.join(output_path, filename)
                        new_file_path = os.path.join(output_path, f'MEIJ_Backup_InvoiceNUM_{invoice_number}_file_{filename.replace("screenshot", str(invoice_number))}')
                        if os.path.exists(new_file_path):
                            self.log.debug(f"File '{new_file_path}' already exists.")
                            continue
                        try:
                            os.rename(old_file_path, new_file_path)
                        except TimeoutException:
                            self.log.debug("TimeoutException while renaming file or maybe file is not found")
                await self.info(f"Meijer backup - {invoice_number} Processed")
        count_invoices = len(invoice_numbers)
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(output_path, f"MEIJ_Backup_{count_invoices}_{current_date}")
        await self.info('Processing...')
        pdf_files = [file for file in os.listdir(output_path) if file.endswith('.pdf')]
        if pdf_files:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for pdf_file in pdf_files:
                    pdf_files_path = os.path.join(output_path, pdf_file)
                    zipf.write(pdf_files_path, arcname=pdf_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid invoice numbers.')
            return

    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 30)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            click_log = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Log In')]")))
            click_log.click()
        except TimeoutException:
            self.log.debug("click login not found.")
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            click_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[1]/div[1]/div/div/span")))
            click_vendor.click()
        except TimeoutException:
            self.log.debug("click_vendor not found.")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        return 'https://vendornet.meijer.com/Welcome' in self.driver.current_url
