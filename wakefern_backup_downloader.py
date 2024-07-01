from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
import pandas as pd
 
class WKFRNBCKUPAccelerator(Accelerator):
    display_name = "All Backups Downloader"
    group_name = "Wakefern Foods"
    start_url = 'http://www8.wakefern.com/servlet/com.wakefern.wgl.framework.controller.ServletController3'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    accelerator_info = """<div class="accelerator">
        <p><strong>Accelerator Type:</strong> Backup</p>
        <br>
        <p><strong>Accelerator Info:</strong> Be advised, the Wakefern portal formats data in a way that makes data more difficult to parse. In order to save process time, we have limited the search window to a max. of 3 days.</p>
        <br>
        <p><strong>Vendor Code:</strong> WAKE</p>
        <p><strong>Vendor Name:</strong> Wakefern Foods</p>
        <p><strong>Vendor Portal Link:</strong> <a href="http://www8.wakefern.com">http://www8.wakefern.com</a> (Allow pop-ups)</p>
        <p><strong>OTP Verification:</strong> OTP not required.</p>
        <br>
        <p><strong>SAP Account ID:</strong> 40299386</p>
        <p><strong>SAP Account Name:</strong> WAKEFERN FOODS INC</p><br>
    </div>"""
    vendor_info = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        await self.info('Starting Accelerator')
        delta = to_date - from_date
        if delta.days <= 3:
            wait = WebDriverWait(self.driver, 30)
    
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
    
                    self.driver.switch_to.default_content()
                    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="USERID"]')))
                    username_input.clear()
                    username_input.send_keys(username)
                    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="CURPASS"]')))
                    password_input.clear()
                    password_input.send_keys(password)
                    submit = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="SUBMIT"]')))
                    submit.click()
                    self.driver.switch_to.default_content()
    
                    if not self.is_logged_in():
                        await self.error('Login failed. Please try again.')
                        return
                    await self.info("Great! We're logged in. Let's proceed.")
            
            await self.info("Please wait, we're processing the request...")
            from_date_value = from_date.strftime("%m%d%Y")
            to_date_value = to_date.strftime("%m%d%Y")
            self.driver.switch_to.default_content()
            live = False
            try:
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                live = True
            except Exception:
                live = False
            if not live:
                self.driver.refresh()
                await self.sleep(2)
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
            await self.info('Searching the portal…')
            select_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "M"]')))
            select_menu.click()
            show_menu = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Show Menu"]')))
            show_menu.click()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="treeFrame"]'))))
            vendor = self.driver.find_elements(By.XPATH, '//*[@alt="Click to open this folder"]')[0]
            vendor.click()
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@align="TEXTTOP"]')))
            select_vendor.click()
            try:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                from_date_input = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, '//*[@name="FROM_CHK_DATE"]')))
            except Exception:
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="FROM_CHK_DATE"]')))
            to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="TO_CHK_DATE"]')))
            from_date_input.clear()
            to_date_input.clear()
            from_date_input.send_keys(from_date_value)
            to_date_input.send_keys(to_date_value)
            await self.info(f'Found Date(s): {from_date_value} - {to_date_value}')
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="actionFrame"]'))))
            submit_dates = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="CONTINUE PROCESSING"]')))
            submit_dates.click()
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
            rows = self.driver.find_elements(By.XPATH, '//*[@id="fwAppDiv"]/form/center/table/tbody/tr')
            row_count = len(rows)
            await self.info('Processing the data…')
            for row_num in range(4, 4 + row_count - 3):
                if row_num > 4:
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Back to Payment Search Results"]'))).click()
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div[7]/div/form/center/table/tbody/tr[{row_num}]/td[1]/font/a'))).click()
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="chkDetail"]'))).text
                self.driver.switch_to.default_content()
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="pageFrame"]'))))
                rows = self.driver.find_elements(By.XPATH, "//*[text() = 'CR']")
                df_temp = pd.DataFrame()
                jvs = []
                checks = []
                for row in rows:
                    if len(str(row.get_attribute('href'))) > 13:
                        ch_num = str(row.get_attribute('href'))[38:46]
                        jvs.append(row.get_attribute('href'))
                        checks.append(ch_num)
                df_temp['JS'] = jvs
                df_temp['Check'] = checks
                for index, data in df_temp.iterrows():
                    jspath = data['JS']
                    checkspath = data['Check']
                    checkspath = str(checkspath).replace('-', '')
                    self.driver.execute_script(jspath)
                    await self.sleep(2)
                    tocken_data = False
                    try:
                        df_data = self.driver.find_element(By.XPATH, '/html/body/div[7]/div/form/center[2]/table').text
                        tocken_data = True
                    except Exception:
                        tocken_data = False
                    if tocken_data:
                        intro_data = df_data.replace(':', '::')
                        second_data_tocken = False
                        try:
                            df_data_second = self.driver.find_element(By.XPATH, '//*[@id="discDetailDiv"]').text
                            second_data_tocken = True
                        except Exception:
                            second_data_tocken = False
                        if second_data_tocken:
                            final_df = pd.DataFrame()
                            columns = ['Eff Date', 'Redemption QTY', 'Redemption $', 'Redemption LBS', 'Handling', 'Rainchecks', 'Total']
                            for column in columns:
                                final_df[f'{column}'] = ''
                            for line in df_data_second.split('\n'):
                                gen_row = line.split(' ')
                                new_row = pd.DataFrame([gen_row], columns=final_df.columns)
                                final_df = pd.concat([new_row, final_df], ignore_index=True)
                            tables = [intro_data, final_df]
                            with open(os.path.join(self.output_path, f"WAKE_Backup_Range_{from_date_value}_{to_date_value}Check Number_{checkspath}.txt"), 'w', encoding='utf-8') as file:
                                for i, table in enumerate(tables):
                                    file.write(str(table))
                                    file.write("\n\n")
                            self.driver.execute_script("javascript:processAction('CHECK_DTL_SCREEN')")
                            await self.sleep(1)
                            await self.info(f"Found: {checkspath}")

                        else:
                            tables = [intro_data]
                            with open(os.path.join(self.output_path, f"WAKE_Backup_Range_{from_date_value}_{to_date_value}Check Number_{checkspath}.txt"), 'w', encoding='utf-8') as file:
                                for i, table in enumerate(tables):
                                    file.write(str(table))
                                    file.write("\n\n")
                            self.driver.execute_script("javascript:processAction('CHECK_DTL_SCREEN')")
                            await self.sleep(1)
                            await self.info(f"Found: {checkspath}")
                    else:
                        else_data = False
                        try:
                            default_data = self.driver.find_element(By.XPATH, '/html/body/div[7]/div/form/center').text
                            else_data = True
                        except Exception:
                            else_data = False
                        if else_data:
                            with open(os.path.join(self.output_path, f"WAKE_Backup_Range_{from_date_value}_{to_date_value}_Check Number_{checkspath}.txt"), 'w', encoding='utf-8') as file:
                                file.write(str(default_data))
                                file.write("\n\n")
                            self.driver.execute_script("javascript:processAction('CHECK_DTL_SCREEN')")
                            await self.sleep(1)
                            await self.info(f"Found: {checkspath}")
                        else:
                            await self.info(f"Not Found: {checkspath}")

            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"WAKE_Backup_{formatted_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.txt')]
            if len(pdf_files) > 0:
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
            await self.error(f"Date range difference exceeds 3 days: {delta.days} days")
            return
        
    def is_logged_in(self) -> bool:
        try:
            self.driver.switch_to.default_content()
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@name="USERID"]')))
            return False
        except Exception:
            self.driver.switch_to.default_content()
            return True
