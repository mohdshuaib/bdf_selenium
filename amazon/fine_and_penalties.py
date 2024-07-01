from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import pandas as pd
import shutil
from glob import glob
from selenium.common.exceptions import TimeoutException
from accelerators.implementations.amazon.base import AmazonBase
from datetime import datetime
class AmazonFNPAccelerator(AmazonBase):
    display_name = 'Penalties Backup Downloader'
    input_display_names = {'invoice_numbers': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the common format for Penalty reference numbers includes the suffix "VC" for Fines incidating vendor charge.</p>
        <br>
        <p><strong>Vendor Code:</strong> AMZN</p>
        <p><strong>Vendor Name:</strong> Amazon.com Inc.</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://vendorcentral.amazon.com/">https://vendorcentral.amazon.com/</a></p>
        <p><strong>OTP Verification:</strong> Yes. Enter code from Email/Mobile.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299543</p>
        <p><strong>SAP Account Name:</strong> AMAZON.COM</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        if len(invoice_numbers) < 20:
            wait = WebDriverWait(self.driver, 10)
            await self.info("Please wait, we're processing the request...")
            if not await self.login():
                return
            selected_account = 'US - Beiersdorf Inc. (current)'
            report_output_path = os.path.join(self.output_path, "Shortage", "Shortage_SKU", selected_account)
            self.log.debug("[+]FNP Steps")
            final_new_dataframe = pd.DataFrame()
            browser_default_path = self.output_path
            os.makedirs(report_output_path, exist_ok=True)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.info('Searching the portal…')

            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            
            for invoice_number in remove_duplicates_and_blanks(invoice_numbers):
                if len(invoice_number) > 3:
                    await self.info(f"Processing:{invoice_number}")
                    invoice_url = f"https://vendorcentral.amazon.com/hz/vendor/members/chargebacks/ui/invoice/{invoice_number}"
                    self.driver.get(invoice_url)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Maybe later "]'))).click()
                        self.log.debug("Window Close Success...!")
                    except TimeoutException:
                        self.log.debug("[+] No window Popups")
                        
                    main_window_handle = self.driver.current_window_handle
                    all_window_handles = self.driver.window_handles
                    for window_handle in all_window_handles:
                        if window_handle != main_window_handle:
                            self.driver.switch_to.window(window_handle)
                            self.driver.close()
                    self.driver.switch_to.window(main_window_handle)
                    if "Internal Error" not in wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]"))).text:
                        no_response_element = '/html/body/div[1]/div[2]/div/div/div[3]/span[1]'
                        if "0 - 0 of 0 total transactions" not in wait.until(EC.element_to_be_clickable((By.XPATH, no_response_element))).text:
                            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[4]/div/div[2]/div/div[5]/div/table/tbody/tr[1]/th[1]/input"))).click()
                            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/a"))).click()
                            await self.wait_for_output(lambda files: any(file.startswith("chargebacks-") for file in files))
                            await self.wait_for_output(lambda files: any('.tmp' not in filen and '.crdownload' not in filen for filen in files))
                            await self.sleep(2)
                            for file in os.listdir(browser_default_path):
                                if file.startswith("chargebacks-"):
                                    shutil.move(os.path.join(browser_default_path, file), os.path.join(report_output_path, f"CB_Invoice_{invoice_number}.csv"))
                                    await self.info(f"Found #:{invoice_number}")
                        else:
                            await self.info(f"Not Found:{invoice_number}")
                    else:
                        await self.error("404 Internal Error! Please Try Again..")
                        return
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            await self.info('Processing the data…')
            report_output_path = os.path.join(self.output_path, "Shortage", "Shortage_SKU")
            filenames = glob(os.path.join(report_output_path, selected_account, "*.csv"))
            for file in filenames:
                new_dataframe = pd.read_csv(file)
                new_dataframe.insert(0, "Account Name", selected_account)
                final_new_dataframe = pd.concat([final_new_dataframe, new_dataframe])
                file_name = os.path.basename(file)
                file_rname = file_name.split('_')[-1]
                new_file_name = f'AMZN_Fines_&_Penalties_Backup_{formatted_date}_{file_rname}'
                new_file_path = os.path.join(report_output_path, selected_account, new_file_name)
                os.rename(file, new_file_path)
            if len(final_new_dataframe) > 0:
                final_new_dataframe = final_new_dataframe.reset_index(drop=True)
                final_new_dataframe.to_excel(os.path.join(report_output_path, f"AMZN_Consolidated_Fines_&_Penalties_{formatted_date}.xlsx"), index=False, header=True)
                await self.info("Success! Please click 'Download' to receive files.")
                zip_filename = os.path.join(self.output_path, f"AMZN_Fines_&_Penalties_{formatted_date}")
                shutil.make_archive(zip_filename, 'zip', report_output_path)
                return f'{zip_filename}.zip'
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
                return
        else:
            await self.error('AssignNum limit exceeds count 20.')
