from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import pandas as pd
import shutil
from glob import glob
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from accelerators.implementations.amazon.base import AmazonBase
from datetime import datetime
from selenium.common.exceptions import StaleElementReferenceException

class AmazonOSDAccelerator(AmazonBase):
    display_name = 'OSD Backup Downloader'
    input_display_names = {'invoice_input_file': 'Enter Assignment/Vendor Reference Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the common format for OSD reference numbers includes the suffix "SC" or "SC-" indicating a shortage charge.</p>
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
    
    async def run(self, invoice_input_file: list[str]) -> str:
        if len(invoice_input_file) < 20:
            wait = WebDriverWait(self.driver, 10)
            await self.info("Please wait, we're processing the request...")
            if not await self.login():
                return
            report_output_path = os.path.join(self.output_path, "Shortage", "Shortage Backup Downloader")
            self.log.debug("[+] OSD Steps ")
            final_output_osd = pd.DataFrame()
            browser_default_path = self.output_path
            selected_account = 'US - Beiersdorf Inc. (current)'
            os.makedirs(report_output_path, exist_ok=True)

            def pop_up_handle():
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

            def refresh_untill():
                xpath = '//*[@id="sc-content-container"]/div/div/div[2]/div/div'
                while True:
                    try:
                        WebDriverWait(self.driver, 10).until(EC.visibility_of_element_located((By.XPATH, xpath)))
                        self.driver.refresh()
                    except TimeoutException:
                        break
            await self.info('Searching the portal…')

            def remove_duplicates_and_blanks(lst):
                seen = set()
                result = []
                for item in lst:
                    if item and item not in seen:
                        seen.add(item)
                        result.append(item)
                return result
            
            for invoice_number in remove_duplicates_and_blanks(invoice_input_file):
                if len(invoice_number) > 9 and invoice_number[:10].isnumeric():
                    invoice_number_url = invoice_number[:10]
                    await self.info(f"Processing:{invoice_number}")
                    report_output_path = os.path.join(report_output_path, selected_account)
                    os.makedirs(report_output_path, exist_ok=True)
                    invoice_filename = f"AMZN_OSD_Backup_downloader_{invoice_number}.xlsx"
                    invoice_path = os.path.join(report_output_path, invoice_filename)
                    if not os.path.exists(invoice_path):
                        invoice_link = f"https://vendorcentral.amazon.com/hz/vendor/members/inv-mgmt/invoice-po-search?searchByNumberToken={invoice_number_url}"
                        self.driver.get(invoice_link)
                        refresh_untill()
                        pop_up_handle()
                        try:
                            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                            if wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="advancedsearchresponsemelodictable"]'))).text == "No results were found.":
                                await self.info(f"Not Found:{invoice_number}")
                                continue
                        except TimeoutException:
                            self.log.debug("Invoice/OSD No message no result found!")
                        refresh_token = False
                        try:
                            payment_code = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="r0-PAYEE_CODE"]'))).text
                            refresh_token = True
                        except TimeoutException:
                            self.log.debug(f"Invoice/OSD information is not available for Invoice = {invoice_number}")
                            refresh_token = False

                        if not refresh_token:
                            refresh_untill()
                            self.driver.get(invoice_link)
                            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                            pop_up_handle()
                            try:
                                payment_code = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="r0-PAYEE_CODE"]'))).text
                            except TimeoutException:
                                await self.info(f"Not Found:{invoice_number}")
                                continue
                        download_link = f"https://vendorcentral.amazon.com/hz/vendor/members/inv-mgmt/invoice-details?invoiceNumber={invoice_number_url}&payeeCode={payment_code}&activeTab=lineItems"
                        self.driver.get(download_link)
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                        tocken = False
                        try:
                            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[5]/div/table')))
                            tocken = True
                        except TimeoutException:
                            self.log.debug(f"Invoice/OSD information is not available for Invoice = {invoice_number} re - chack")
                            tocken = False
                        if not tocken:
                            try:
                                refresh_untill()
                                self.driver.get(download_link)
                                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                                pop_up_handle()
                                wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[5]/div/table')))
                            except TimeoutException:
                                await self.info(f"Not Found:{invoice_number}")
                                continue
                        page_down = wait.until(EC.element_to_be_clickable((By.TAG_NAME, 'html')))
                        page_down.send_keys(Keys.END)
                        no_of_pages = ''
                        no_of_pages = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[6]/div[1]'))).text
                        no_of_pages = no_of_pages.strip()
                        web_table_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[5]/div/table')))
                        numbers_of_record = len(web_table_element.find_elements(By.CLASS_NAME, "mt-row"))

                        if numbers_of_record <= 20 and no_of_pages == '':

                            new_data_frame = pd.DataFrame()

                            web_table_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[5]/div/table')))
                            numbers_of_record = len(web_table_element.find_elements(By.CLASS_NAME, "mt-row"))

                            columns_names = ['Account Name', 'Invoice Number', 'PO #', 'External ID', 'Title', 'ASIN', 'Model #', 'Freight Term', 'Qty', 'Unit Cost', 'Amount', 'Shortage quantity', 'Amount shortage', 'Last received date', 'ASIN received', 'Quantity received', 'Unit cost', 'Amount received']
                            index_val = []
                            for k in range(1, numbers_of_record + 1):
                                index_val.append(k)
                            osd_data_frame = pd.DataFrame(columns=columns_names, index=index_val)
                            for count_of_row in range(1, numbers_of_record + 1):
                                osd_data_frame['Account Name'][count_of_row] = selected_account
                                osd_data_frame['Invoice Number'][count_of_row] = str(invoice_number)
                                wbele = web_table_element.find_elements(By.TAG_NAME, 'tr')[count_of_row]
                                osd_data_frame["PO #"][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[0].text
                                osd_data_frame['External ID'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[1].text
                                osd_data_frame['Title'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[2].text
                                osd_data_frame['ASIN'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[3].text
                                osd_data_frame['Model #'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[4].text
                                osd_data_frame['Freight Term'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[5].text
                                osd_data_frame['Qty'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[6].text
                                osd_data_frame['Unit Cost'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[7].text
                                osd_data_frame['Amount'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[8].text
                                osd_data_frame['Shortage quantity'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[9].text
                                osd_data_frame['Amount shortage'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[10].text
                                osd_data_frame['Last received date'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[11].text
                                osd_data_frame['ASIN received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[12].text
                                osd_data_frame['Quantity received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[13].text
                                osd_data_frame['Unit cost'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[14].text
                                osd_data_frame['Amount received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[15].text

                            new_data_frame = pd.concat([new_data_frame, osd_data_frame])

                            output_file_path = os.path.join(report_output_path, invoice_filename)
                            new_data_frame.to_excel(output_file_path, header=True, index=False)
                        else:
                            new_data_frame = pd.DataFrame()
                            click_next_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[6]/div[1]'))).text
                            clicks = int(click_next_button.split('\n')[-2])
                            for number_of_clicks in range(0, clicks):

                                web_table_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="lineitemsmelodictable"]/div[5]/div/table')))
                                numbers_of_record = len(web_table_element.find_elements(By.CLASS_NAME, "mt-row"))

                                columns_names = ['Account Name', 'Invoice Number', 'PO #', 'External ID', 'Title', 'ASIN', 'Model #', 'Freight Term', 'Qty', 'Unit Cost', 'Amount', 'Shortage quantity', 'Amount shortage', 'Last received date', 'ASIN received', 'Quantity received', 'Unit cost', 'Amount received']

                                index_val = []

                                for k in range(1, numbers_of_record + 1):
                                    index_val.append(k)

                                osd_data_frame = pd.DataFrame()
                                osd_data_frame = pd.DataFrame(columns=columns_names, index=index_val)

                                for count_of_row in range(1, numbers_of_record + 1):
                                    osd_data_frame['Account Name'][count_of_row] = selected_account
                                    osd_data_frame['Invoice Number'][count_of_row] = str(invoice_number)

                                    wbele = web_table_element.find_elements(By.TAG_NAME, 'tr')[count_of_row]

                                    osd_data_frame["PO #"][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[0].text
                                    osd_data_frame['External ID'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[1].text
                                    osd_data_frame['Title'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[2].text
                                    osd_data_frame['ASIN'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[3].text
                                    osd_data_frame['Model #'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[4].text
                                    osd_data_frame['Freight Term'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[5].text
                                    osd_data_frame['Qty'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[6].text
                                    osd_data_frame['Unit Cost'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[7].text
                                    osd_data_frame['Amount'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[8].text
                                    osd_data_frame['Shortage quantity'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[9].text
                                    osd_data_frame['Amount shortage'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[10].text
                                    osd_data_frame['Last received date'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[11].text
                                    osd_data_frame['ASIN received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[12].text
                                    osd_data_frame['Quantity received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[13].text
                                    osd_data_frame['Unit cost'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[14].text
                                    osd_data_frame['Amount received'][count_of_row] = wbele.find_elements(By.TAG_NAME, 'td')[15].text

                                new_data_frame = pd.concat([new_data_frame, osd_data_frame])

                                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                                for _ in range(5):
                                    try:
                                        next_button = WebDriverWait(self.driver, 10).until(
                                            EC.presence_of_element_located((By.XPATH, '//*[@id="lineItemsMelodicTable-pagination-next"]'))
                                        )
                                        next_button.click()
                                        break
                                    except StaleElementReferenceException:
                                        await self.info(f"Not Found:{invoice_number}")
                                        continue
                            new_data_frame.to_excel(os.path.join(report_output_path, invoice_filename), header=True, index=False)
                        await self.info(f"Found #:{invoice_number}")
                        report_output_path = os.path.join(browser_default_path, "Shortage", "Shortage Backup Downloader")
            report_output_path = os.path.join(browser_default_path, "Shortage", "Shortage Backup Downloader")
            await self.info('Processing the data…')
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            file_names = glob(os.path.join(report_output_path, selected_account, "*.xlsx"))
            for file in file_names:
                df_total = pd.read_excel(file, dtype='object')
                final_output_osd = pd.concat([final_output_osd, df_total])
                file_name = os.path.basename(file)
                file_rname = file_name.split('_')[-1]
                new_file_name = f'AMZN_Shortage_Backup_{formatted_date}_{file_rname}'
                new_file_path = os.path.join(report_output_path, selected_account, new_file_name)
                os.rename(file, new_file_path)
            if len(final_output_osd) > 0:
                final_output_osd = final_output_osd.reset_index(drop=True)
                final_output_osd['Invoice Number'] = final_output_osd['Invoice Number'].astype(str)
                final_output_osd.to_excel(os.path.join(report_output_path, f"AMZN_OSD_Backup_downloader_Consolidated_{formatted_date}.xlsx"), index=False, header=True)
                await self.info("Success! Please click 'Download' to receive files.")
                zip_filename = os.path.join(self.output_path, f"AMZN_OSD_Backup_downloader_{formatted_date}")
                shutil.make_archive(zip_filename, 'zip', report_output_path)
                return f'{zip_filename}.zip'
            else:
                await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
        else:
            await self.error('AssignNum limit exceeds count 20.')
