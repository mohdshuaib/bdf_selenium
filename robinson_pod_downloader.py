from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
import os
import zipfile
from accelerators import Accelerator
from datetime import datetime
class CHROPodAccelerator(Accelerator):
    display_name = "POD Backup Downloader"
    group_name = "C.H. Robinson"
    start_url = "https://account.chrobinson.com/"
    input_display_names = {'invoice_numbers': 'Enter PRO Number(s)'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> POD Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Please note the PRO# should only include the values expected, for example, SAP may include "PRO123456 SL34567". Instead, only input 123456, because that is how this portal works.</p>
        <br>
        <p><strong>Vendor Code:</strong> CHRO</p>
        <p><strong>Vendor Name:</strong> C.H. Robinson</p>
        <p><strong>Vendor Portal Link:</strong> <a href="https://online.chrobinson.com">https://online.chrobinson.com</a></p>
        <p><strong>OTP Verification:</strong> No. OTP verification is not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 6910000017</p>
        <p><strong>SAP Account Name:</strong> CH ROBINSON</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        if len(invoice_numbers) < 20:
            wait = WebDriverWait(self.driver, 30)
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.info('Starting Accelerator...')
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
                    user_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-username"]')))
                    user_input.clear()
                    user_input.send_keys(username)
                    auth_tocken = False
                    try:
                        pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                        auth_tocken = True
                    except TimeoutException:
                        auth_tocken = False
                        self.log.debug('method change for login...')
                    if not auth_tocken:
                        submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"][@value="Sign in"]')))
                        submit_login.click()
                        pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                        pass_input.clear()
                        pass_input.send_keys(password)
                    else:
                        pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                        pass_input.clear()
                        pass_input.send_keys(password)
                        submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                        submit_login.click()
                    try:
                        await self.info('Please wait...')
                        WebDriverWait(self.driver, 60).until(EC.invisibility_of_element((By.XPATH, '//*[@type="submit"]')))
                    except TimeoutException:
                        await self.error('Login failed. Please try again.')
                        return
                    WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    if not self.is_logged_in():
                        await self.error('Login failed. Please try again.')
                        return
                    await self.info("Great! We're logged in. Let's proceed.")
            await self.info("Please wait, we're processing the request...")
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
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
                if len(invoice_number) > 5:
                    invoice_number = invoice_number.strip()
                    await self.info(f'Processing:{invoice_number}')
                    self.driver.get(f'https://online.chrobinson.com/search/#/?view=purchaseOrder&page=1&search={invoice_number}&customsStatus=&status=&riskLevels=&account=&supplier=&transportMode=&shippingMethod=&timeFrame=&timeFrames=&sortByDirection=desc&sortByField=earliestPickupDate&bookingFromDate=&bookingToDate=&pickupFromDate=&pickupToDate=&deliveryFromDate=&deliveryToDate=&activeTimeframePanel=Pre-Defined&currentTimeframe=&pickupLocation=&deliveryLocation=&deliveryLocationName=&portLoading=&countryOfOrigin=&countryOfExport=&entryPort=&bookingDateType=Requested&pickupDateType=Requested&deliveryDateType=Requested&redirecting=&shipDateType=Requested&shipFromDate=&shipToDate=&entrySubmittedDateType=Submitted&entrySubmittedFromDate=&entrySubmittedToDate=&entryPortArrivalDateType=Expected&entryPortArrivalFromDate=&entryPortArrivalToDate=&entryType=&carrier=&disruption=&box=&isClusterView=&flightNumber=&vesselImoNumber=&facilityStop=')
                    WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    self.driver.get(f'https://online.chrobinson.com/search/#/?view=purchaseOrder&page=1&search={invoice_number}&customsStatus=&status=&riskLevels=&account=&supplier=&transportMode=&shippingMethod=&timeFrame=&timeFrames=&sortByDirection=desc&sortByField=earliestPickupDate&bookingFromDate=&bookingToDate=&pickupFromDate=&pickupToDate=&deliveryFromDate=&deliveryToDate=&activeTimeframePanel=Pre-Defined&currentTimeframe=&pickupLocation=&deliveryLocation=&deliveryLocationName=&portLoading=&countryOfOrigin=&countryOfExport=&entryPort=&bookingDateType=Requested&pickupDateType=Requested&deliveryDateType=Requested&redirecting=&shipDateType=Requested&shipFromDate=&shipToDate=&entrySubmittedDateType=Submitted&entrySubmittedFromDate=&entrySubmittedToDate=&entryPortArrivalDateType=Expected&entryPortArrivalFromDate=&entryPortArrivalToDate=&entryType=&carrier=&disruption=&box=&isClusterView=&flightNumber=&vesselImoNumber=&facilityStop=')
                    WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    pan_order = WebDriverWait(self.driver, 160).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]')))
                    stable_tocken = False
                    try:
                        self.driver.execute_script("arguments[0].click();", pan_order)
                        stable_tocken = True
                    except TimeoutException:
                        self.log.debug('Page Load failed Re-try again with attemp 1')
                        stable_tocken = False

                    if not stable_tocken:
                        try:
                            WebDriverWait(self.driver, 80).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]'))).click()
                            stable_tocken = True
                        except TimeoutException:
                            self.log.debug('Page Load failed Re-try again with attemp 2')
                            stable_tocken = False
                    if not stable_tocken:
                        self.log.debug('Page Load failed Re-try again with attemp 3')
                        await self.info(f"Not Found:{invoice_number}")
                        continue
                    WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        results = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-view-tabs-component-pane-purchaseOrder"]/div/div[2]/div/div/div[1]/h3'))).text
                        if "We couldn't find any results that match your search." in results:
                            await self.info(f"Not Found:{invoice_number}")
                            continue
                    except TimeoutException:
                        self.log.debug(f'Record found for POD - {invoice_number}')
                        
                    try:
                        WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                    except TimeoutException:
                        self.log.debug('not find close button')
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]'))).click()
                    tocken_id = False
                    try:
                        doc_id = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-view-tabs-component-pane-order"]/div/div[3]/div/div/div[2]/div[2]/div[1]/div/div/div[2]/a/span'))).text
                        tocken_id = True
                    except TimeoutException:
                        tocken_id = False

                    if not tocken_id:
                        await self.info(f"Not Found:{invoice_number}")
                        continue
                    else:
                        doc_id_link = f"https://online.chrobinson.com/ordersdetail/#/{doc_id}"
                        self.driver.get(doc_id_link)
                        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                    except TimeoutException:
                        self.log.debug('not find close button')
                    tocken_toor = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ordersDetail-tab-documents"]'))).click()
                        tocken_toor = True
                    except TimeoutException:
                        tocken_toor = False
                    if not tocken_toor:
                        try:
                            WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                        except TimeoutException:
                            self.log.debug('not find close button')
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ordersDetail-tab-documents"]'))).click()
                        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    table = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Documents Table"]')))
                    rows = table.find_elements(By.TAG_NAME, 'tr')
                    await self.info(f"Please wait we are processing the data for {int(len(rows))-1} files")
                    for download_index in range(1, int(len(rows))):
                        download_div = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/section/div/div[3]/div[3]/div[7]/div/div[2]/table/tbody/tr[{download_index}]/td[2]/button')))
                        if download_div.text.startswith('DOC'):
                            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                            for _ in range(5):
                                try:
                                    download = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, f'/html/body/div/div/section/div/div[3]/div[3]/div[7]/div/div[2]/table/tbody/tr[{download_index}]/td[7]/div/button'))
                                    )
                                    download.click()
                                    break
                                except StaleElementReferenceException:
                                    continue
                            await self.wait_for_output(lambda files: f'{download_div.text}-{doc_id}.pdf' in files)
                            os.rename(os.path.join(self.output_path, f'{download_div.text}-{doc_id}.pdf'), os.path.join(self.output_path, f"CHRO_POD Backup_{download_div.text}_PRO_{invoice_number}_{doc_id}.pdf"))
                            # await self.info(f'Pod DOC - {invoice_number} - {download_div.text}-{doc_id}.pdf, Processed')
                        elif download_div.text.startswith('Pallet'):
                            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                            for _ in range(5):
                                try:
                                    download = WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.XPATH, f'/html/body/div/div/section/div/div[3]/div[3]/div[7]/div/div[2]/table/tbody/tr[{download_index}]/td[7]/div/button'))
                                    )
                                    download.click()
                                    break
                                except StaleElementReferenceException:
                                    continue
                            await self.wait_for_output(lambda files: f'Pallet Label-{doc_id}.pdf' in files)
                            os.rename(os.path.join(self.output_path, f'Pallet Label-{doc_id}.pdf'), os.path.join(self.output_path, f"CHRO_POD Backup_Label{download_div.text}_PRO_{invoice_number}_{doc_id}.pdf"))
                            # await self.info(f'Pallet Label- - {invoice_number} - {download_div.text}-{doc_id}.pdf, Processed')
                    await self.info(f'Found #: {invoice_number}')
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if pdf_files:
                await self.info("Processing the data…")
                current_date = datetime.now()
                formatted_date = current_date.strftime("%m%d%Y")
                zip_filename = os.path.join(self.output_path, f"CHRO_POD Backup_{formatted_date}")
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! Please click 'Download' to receive files.")
                return f'{zip_filename}.zip'
            await self.error('Accelerator failed. Please try again. If issue persists, contact admin or go direct to vendor portal.')
            return
        else:
            await self.error('PRONum limit exceeds count 10.')
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-username"]')))
            return False
        except Exception:
            return True
