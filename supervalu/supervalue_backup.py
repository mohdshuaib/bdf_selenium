from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import os
import zipfile

from accelerators.implementations.supervalu.base import SupervaluBase

class SupervaluBackupAccelerator(SupervaluBase):
    display_name = 'All Backups Downloader'
    input_display_names = {'documents': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """ <div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong></p>
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
    
    async def run(self, documents: list[str]) -> str:
        if len(documents) < 20:
            await self.info("Starting Accelerator...")
            if not await self.login():
                return

            wait = WebDriverWait(self.driver, 30)
            wait.until(EC.visibility_of_element_located((By.XPATH, '//*[text() ="Go"]')))
            await self.info('Searching the portal…')
            
            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            
            for document_no in remove_duplicates_and_blanks(documents):
                if len(str(document_no)) > 4:
                    self.driver.get("https://epass.svharbor.com/epass/newDocumentSearch")
                    await self.info(f"Processing: {document_no}")
                    input_doc_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="docNum1"]')))
                    input_doc_field.clear()
                    input_doc_field.send_keys(document_no)
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="dateCriteria"][@value="4"]'))).click()
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Go"]'))).click()
                    status = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/form/div/table/tbody/tr[1]/td[3]"))).text
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name = "documentOutputType"][@value = "pdf"]'))).click()
                    if status == "View":
                        document_status = wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[text() ="{document_no}"]')))
                        document_status.click()
                        self.driver.switch_to.window(self.driver.window_handles[1])
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                        await self.sleep(5)
                        window_handles = self.driver.window_handles
                        if len(window_handles) > 0:
                            self.driver.close()
                            first_window_handle = window_handles[0]
                            for filename in os.listdir(self.output_path):
                                if filename.startswith('BATCH'):
                                    os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'SUPR_Backup_Assign_{document_no}.pdf'))
                            self.driver.switch_to.window(first_window_handle)
                            await self.info(f'Found: {document_no}')
                    else:
                        await self.info(f"Not Found: {document_no}")

            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"SUPR_Backups_{formatted_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if len(pdf_files) > 0:
                await self.info('Processing the data…')
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
                return
        else:
            await self.error('AssignNum limit exceeds count 20.')
