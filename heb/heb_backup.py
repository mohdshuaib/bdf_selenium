from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import os
import zipfile

from accelerators.implementations.heb.base import HEBBase

class HEBBackupAccelerator(HEBBase):
    display_name = 'All Backups Downloader'
    input_display_names = {'invoice_input_file': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong></p>
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
    
    async def run(self, invoice_input_file: list[str]) -> str:
        await self.info('Starting Accelerator...')
        if not await self.login():
            return

        wait = WebDriverWait(self.driver, 30)
        await self.info("Please wait, we're processing the request...")
        
        def remove_duplicates_and_blanks(lst):
            seen = set()
            result = []
            for item in lst:
                if item and item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
            
        for invoice_number in remove_duplicates_and_blanks(invoice_input_file):
            await self.info(f"Processing: {invoice_number}")
            try:
                search_tab = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="search-indicator"]')))
                search_tab.click()
                backup = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="deduction"]')))
                backup.click()
                invoice = wait.until(EC.presence_of_element_located((By.XPATH, '//label[@id="invoice"]')))
                invoice.click()
                invoice_search = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="searchByMyInvoice"]')))
                invoice_search.clear()
                invoice_search.send_keys(invoice_number, Keys.ENTER)
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_5"]')))
                export_button.click()
                details = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_8"]')))
                details.click()
                my_download = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="myDownloads-indicator"]')))
                my_download.click()
                file_download = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div[3]/div[1]/div[1]/a')))
                file_download.click()
                await self.info(f'Found: {invoice_number}')
                await self.wait_for_output(lambda files: any('.crdownload' not in file for file in files))
                await self.wait_for_output(lambda files: any('.tmp' not in file for file in files))
                csv_files = [file for file in os.listdir(self.output_path) if file.endswith(".csv")]
                if csv_files:
                    for file in csv_files:
                        if file.startswith('adjustment_detail'):
                            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f'HEBG_backup_downloader_Reference Number_{invoice_number}_{file}'))
            except Exception:
                await self.info(f"Not Found: {invoice_number}")
                continue
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"HEBG_Backups_{formatted_date}")
        csv_files = [file for file in os.listdir(self.output_path) if file.endswith(".csv")]
        if len(csv_files) > 0:
            await self.info("Processing the data…")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for csv_file in csv_files:
                    zipf.write(os.path.join(self.output_path, csv_file), arcname=csv_file)
            await self.info("Success! Please click 'Download' to receive files.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
