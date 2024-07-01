from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException


class HEBBase(Accelerator):
    group_name = 'H.E. Butt Grocery'
    start_url = "https://avp.heb.com/VendorPortal"
    accelerator_info = ''
    vendor_info = ''
    
    async def login(self):
        wait = WebDriverWait(self.driver, 30)
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info("Attempting to login…")
                username, password = await auth.userpass()

                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="username"]')))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="password"]')))
                password_element.clear()
                password_element.send_keys(password)

                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginButton1"]')))
                submit_login.click()

                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="search-indicator"]')))
                    await self.info("Great! We're logged in. Let's proceed.")
                except TimeoutException:
                    await self.error('Login failed. Please try again.')
                    return
        return True

    def is_logged_in(self) -> bool:
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@id="username"]')))
            return False
        except Exception:
            return True
