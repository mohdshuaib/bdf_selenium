from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from glob import glob
import os
import pandas as pd
from selenium.common.exceptions import TimeoutException
import shutil
from accelerators.implementations.amazon.base import AmazonBase
from datetime import datetime

class AmazonPromoAccelerator(AmazonBase):
    display_name = 'Promotion Backup Downloader'
    input_display_names = {'invoice_numbers': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the common format for Promotion CO-OP reference numbers includes the prefixes of "6403-", "6430-", "6440-".</p>
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
            report_output_path = os.path.join(self.output_path, "CoOp(Promotions)")
            self.log.debug("[+] Promo Steps ")
            final_df_new = pd.DataFrame()
            browser_default_path = self.output_path
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            os.makedirs(report_output_path, exist_ok=True)
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
                    invoice_url = f"https://vendorcentral.amazon.com/hz/vendor/members/coop?searchText={invoice_number}"
                    self.driver.get(invoice_url)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Maybe later "]'))).click()
                        self.log.debug("Popup Window Close Success...!")
                    except TimeoutException:
                        self.log.debug("[+] No window Popups")
                    main_window_handle = self.driver.current_window_handle
                    all_window_handles = self.driver.window_handles
                    for window_handle in all_window_handles:
                        if window_handle != main_window_handle:
                            self.driver.switch_to.window(window_handle)
                            self.driver.close()

                    self.driver.switch_to.window(main_window_handle)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    
                    self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                    
                    report_output_path = os.path.join(browser_default_path, "CoOp(Promotions)", "Invoice-PDF", selected_account)

                    os.makedirs(report_output_path, exist_ok=True)
                    download_xpath = ""
                    for i in range(1, 6):
                        try:
                            download_xpath = f'/html/body/div[1]/div[2]/div/div[1]/div[2]/div[1]/div/div[{i}]/div[2]/div[2]/div/div/kat-data-table/table/tbody/tr/td[7]/div/span[1]/span/span/span/span'
                            WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, download_xpath)))
                            break
                        except TimeoutException:
                            self.log.debug('Searching Download button')
                    # Downloading PDF Invoice
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                        wait.until(EC.element_to_be_clickable((By.ID, f"invoiceDownloads-{invoice_number}_0"))).click()
                    except TimeoutException:
                        self.log.debug(f"Amazon_Invoice_{invoice_number}.pdf Not Downloaded")
                        await self.info(f"Not Found:{invoice_number}")
                        continue
                    await self.wait_for_output(lambda files: f"Amazon_Invoice_{invoice_number}.pdf" in files)

                    if os.path.exists(os.path.join(self.output_path, f"Amazon_Invoice_{invoice_number}.pdf")):
                        shutil.move(os.path.join(self.output_path, f"Amazon_Invoice_{invoice_number}.pdf"), os.path.join(report_output_path, f"Amazon_Invoice_{invoice_number}.pdf"))
                    report_output_path = os.path.join(browser_default_path, "CoOp(Promotions)", "Invoice-CSV", selected_account)
                    os.makedirs(report_output_path, exist_ok=True)
                    # Downloading CSV Invoice
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                        wait.until(EC.element_to_be_clickable((By.ID, f"invoiceDownloads-{invoice_number}_1"))).click()
                    except TimeoutException:
                        self.log.debug(f"Amazon_Invoice_{invoice_number}.csv Not Downloaded")
                        await self.info(f"Not Found:{invoice_number}")
                        continue
                    await self.wait_for_output(lambda files: f"Amazon_Invoice_{invoice_number}.csv" in files)
                    if os.path.exists(os.path.join(self.output_path, f"Amazon_Invoice_{invoice_number}.csv")):
                        shutil.move(os.path.join(self.output_path, f"Amazon_Invoice_{invoice_number}.csv"), os.path.join(report_output_path, f"Amazon_Invoice_{invoice_number}.csv"))

                    report_output_path = os.path.join(browser_default_path, "CoOp(Promotions)", "Backup Report", selected_account)

                    os.makedirs(report_output_path, exist_ok=True)

                    # Downloading Backup Report
                    for i in range(1, 3):
                        try:
                            WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                            WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.ID, f"invoiceDownloads-{invoice_number}_2"))).click()
                            break
                        except TimeoutException:
                            self.log.debug('retrying to click')
                    backup_status_xpath = '//*[@id="backup-report-not-found"]/div/div'
                    no_backup_text = "Straight Payment does not support backup reports. Visit CoOp support for more info."
                    tocken_message = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, backup_status_xpath))).text
                        tocken_message = True
                    except TimeoutException:
                        tocken_message = False
                    tocken_acknowledge = False
                    if tocken_message:
                        if wait.until(EC.element_to_be_clickable((By.XPATH, backup_status_xpath))).text == no_backup_text:
                            await self.info(f"Backup file not found for Invoice - {invoice_number}")
                            wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div[2]/span/span/span/input'))).click()
                        elif wait.until(EC.element_to_be_clickable((By.XPATH, backup_status_xpath))).text == 'No records were found.':
                            await self.info(f"Backup file not found for Invoice - {invoice_number}")
                            wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div[2]/span/span/span/input'))).click()
                        tocken_acknowledge = True
                    if not tocken_acknowledge:
                        await self.info(f"Backup file found for Invoice - {invoice_number}")
                        backup_status_xpath = '/html/body/div[5]/div/div/div[1]/form/div/div/div/table/tbody'
                        count_of_table = len(wait.until(EC.element_to_be_clickable((By.XPATH, backup_status_xpath))).find_elements(By.TAG_NAME, "a"))
                        if count_of_table >= 1:
                            for j in range(count_of_table):
                                xpath_tag_table = f'/html/body/div[5]/div/div/div[1]/form/div/div/div/table/tbody/tr[{str(j + 2)}]/td[3]/a'
                                self.driver.find_element(By.XPATH, xpath_tag_table).click()
                                await self.wait_for_output(lambda files: 'BackupReport.xls' in files)
                                shutil.move(os.path.join(self.output_path, "BackupReport.xls"), os.path.join(report_output_path, f"AMZN_Promotion_CoOp_BackupReport_{invoice_number}.xls"))
                            wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div[2]/span/span/span/input'))).click()
                    report_output_path = os.path.join(browser_default_path, "CoOp(Promotions)", "Agreement", selected_account)

                    os.makedirs(report_output_path, exist_ok=True)
                    coop_conagr_file = os.path.join(self.output_path, f"AMZN_Promotion_CoOp_BDF_Aggrement_{invoice_number}.txt")
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                        wait.until(EC.element_to_be_clickable((By.ID, f"invoiceDownloads-{invoice_number}_3"))).click()
                    except TimeoutException:
                        wait.until(EC.element_to_be_clickable((By.XPATH, download_xpath))).click()
                        wait.until(EC.element_to_be_clickable((By.ID, f"invoiceDownloads-{invoice_number}_3"))).click()
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    xpath_coop_agr = '/html/body/div/div/div/div[1]/table'
                    if wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath_coop_agr))):
                        coop_agr_dec = wait.until(EC.element_to_be_clickable((By.XPATH, xpath_coop_agr))).text
                        self.driver.back()
                    else:
                        coop_agr_dec = WebDriverWait(self.driver, 40).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div/div/div[1]/table'))).text
                        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[8]/div/div/header/button'))).click()
                    txt_file = open(coop_conagr_file, "w+")
                    txt_file.write(coop_agr_dec)
                    txt_file.close()
                    await self.wait_for_output(lambda files: f"AMZN_Promotion_CoOp_BDF_Aggrement_{invoice_number}.txt" in files)
                    shutil.move(os.path.join(self.output_path, f"AMZN_Promotion_CoOp_BDF_Aggrement_{invoice_number}.txt"), os.path.join(report_output_path, f"AMZN_Promotion_CoOp_BDF_Aggrement_{invoice_number}.txt"))
                    report_output_path = os.path.join(browser_default_path, "CoOp(Promotions)")
                    await self.info(f"Found #:{invoice_number}")
            # For collating the CSV Invoices
            await self.sleep(5)
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            filenames = glob(os.path.join(report_output_path, "Invoice-CSV", selected_account, "*.csv"))
            for file in filenames:
                df_total = pd.read_csv(file, dtype='object')
                df_total.insert(0, "Account Name", selected_account)
                final_df_new = pd.concat([final_df_new, df_total])
                file_name = os.path.basename(file)
                file_rname = file_name.split('_')[-1]
                new_file_name = f'AMZN_Promo_Backup_{formatted_date}_{file_rname}'
                new_file_path = os.path.join(report_output_path, "Invoice-CSV", selected_account, new_file_name)
                os.rename(file, new_file_path)
            if len(final_df_new) > 0:
                await self.info('Processing the data…')
                final_df_new = final_df_new.reset_index(drop=True)
                final_df_new.to_excel(os.path.join(report_output_path, "Invoice-CSV", f"AMZN_Promo_Backup_downloader_Consolidated_{formatted_date}.xlsx"), index=False, header=True)
                zip_filename = os.path.join(self.output_path, f"AMZN_Promotion_Backup_{formatted_date}")
                shutil.make_archive(zip_filename, 'zip', report_output_path)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
        else:
            await self.error('AssignNum limit exceeds count 20.')
