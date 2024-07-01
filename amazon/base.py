from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from accelerators import Accelerator


class AmazonBase(Accelerator):
    group_name = 'Amazon.com Inc.'
    start_url = "https://vendorcentral.amazon.com"
    accelerator_info = ''
    vendor_info = ''
    
    async def login(self):
        wait = WebDriverWait(self.driver, 30)
        async with self.authenticator() as auth:
            await self.info('Running...')
            if not self.is_logged_in():
                await self.info("Attempting to login…")
                username, word = await auth.userpass()
                if "/ap/signin?" in self.driver.current_url:
                    username_input_path = '//*[@type="email"]'
                    wait.until(EC.element_to_be_clickable((By.XPATH, username_input_path))).clear()
                    wait.until(EC.element_to_be_clickable((By.XPATH, username_input_path))).send_keys(username)
                    word_input_path = '//*[@type="password"]'
                    wait.until(EC.element_to_be_clickable((By.XPATH, word_input_path))).clear()
                    wait.until(EC.element_to_be_clickable((By.XPATH, word_input_path))).send_keys(word)
                    remember_check_xpath = '//*[@id="authportal-main-section"]/div[2]/div/div/form/div/div/div/div[3]/div[2]/div/label/div/label/input'
                    remember_check = wait.until(EC.element_to_be_clickable((By.XPATH, remember_check_xpath)))
                    remember_check.click()
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInSubmit"]'))).submit()

                def enter_captcha_and_submit(wait, captcha):
                    captcha_input_path = '//*[@name="cvf_captcha_input"]'
                    try:
                        captcha_input = wait.until(EC.element_to_be_clickable((By.XPATH, captcha_input_path)))
                    except TimeoutException:
                        captcha_input_path = '//*[@name="mfa_captcha_input"]'
                        captcha_input = wait.until(EC.element_to_be_clickable((By.XPATH, captcha_input_path)))
                    captcha_input.clear()
                    captcha_input.send_keys(captcha)
                    submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="verifyCaptcha"]')))
                    submit_button.submit()

                if "/ap/cvf/request?" in self.driver.current_url or "/ap/mfa/request?" in self.driver.current_url:
                    await self.info("Enter verification code(s) - Captcha…")
                    captcha_element = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@alt="captcha"]')))
                    await self.info("Please input captcha code correctly")
                    captcha = await auth.captcha(captcha_element)
                    enter_captcha_and_submit(wait, captcha)
                attempts = 0
                while "ap/cvf/verify" in self.driver.current_url or "ap/mfa/verify" in self.driver.current_url:
                    if attempts >= 5:
                        await self.error(f'Failed to solve Captcha with {attempts} attempts')
                        return
                    captcha_element = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@alt="captcha"]')))
                    await self.info(f"Trying to solve captcha with Attemp {attempts}")
                    captcha = await auth.captcha(captcha_element)
                    enter_captcha_and_submit(wait, captcha)
                    attempts += 1
                try:
                    self.log.debug("checking for multi select OTP")
                    option_otp = self.driver.find_elements(By.XPATH, "//span[@class='a-label a-radio-label']")
                    for element in option_otp:
                        if str(element.text).endswith(".com"):
                            self.log.debug(element.text)
                            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="continue"]'))).click()
                except TimeoutException:
                    self.log.debug("[+] Email/Mobile Otp Selection page not available...")

                if "/ap/cvf/transactionapproval?" in self.driver.current_url or "/ap/cvf/approval?" in self.driver.current_url:
                    status = False
                    self.log.debug(self.driver.current_url)
                    for input_otp_path in ['//*[@id="input-box-otp"]', '//*[@id="cvf-input-code"]', '//*[@id="auth-mfa-otpcode"]']:
                        try:
                            input_otp = wait.until(EC.element_to_be_clickable((By.XPATH, f'{input_otp_path}')))
                            await self.info("Enter verification code(s) - OTP/MFA/Captcha…")
                            enter_otp = await auth.otp()
                            input_otp.send_keys(enter_otp)
                            status = True
                            break
                        except TimeoutException:
                            self.log.debug("There was an error with the otp field")
                        
                    for submit_button in ['//*[@id="cvf-submit-otp-button"]/span/input', '//*[@id="auth-signin-button"]', '//*[text() ="Continue"]']:
                        try:
                            wait.until(EC.element_to_be_clickable((By.XPATH, f'{submit_button}'))).click()
                            status = True
                            break
                        except TimeoutException:
                            self.log.debug("[+] Not find Submit Button")

                    if not status:
                        await self.error("Incorrect input OTP/MFA code try again...")
                        return

                elif "/ap/mfa/transactionapproval?" in self.driver.current_url or "/ap/mfa/approval?" in self.driver.current_url:
                    status = False
                    self.log.debug(self.driver.current_url)
                    for input_otp in ['//*[@id="mfa-input-code"]', '//*[@id="input-box-otp"]', '//*[@id="auth-mfa-otpcode"]']:
                        try:
                            input_otp = wait.until(EC.element_to_be_clickable((By.XPATH, f'{input_otp}')))
                            await self.info("Enter verification code(s) - OTP/MFA/Captcha…")
                            enter_otp = await auth.otp()
                            input_otp.send_keys(enter_otp)
                            status = True
                            break
                        except TimeoutException:
                            self.log.debug("There was an error with the otp field")

                    for submit_button in ['//*[@id="cvf-submit-otp-button"]/span/input', '//*[@id="mfa-submit-otp-button"]/span/input']:
                        try:
                            wait.until(EC.element_to_be_clickable((By.XPATH, f'{submit_button}'))).click()
                            status = True
                            break
                        except TimeoutException:
                            self.log.debug("[+] Not find Submit Button")

                    if not status:
                        await self.error("There was an error with the otp submit")
                        return
                
                self.driver.get('https://vendorcentral.amazon.com/hz/vendor/members/remittance/home')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('Login failed. Please try again.')
                    return
                await self.info("Valid code entered.")
                await self.info("Great! We're logged in. Let's proceed.")
                
        return True

    def is_logged_in(self) -> bool:
        return '/ap/signin?' not in self.driver.current_url
