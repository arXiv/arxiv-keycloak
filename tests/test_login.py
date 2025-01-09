import os
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, StaleElementReferenceException, NoSuchElementException
import time
from shutil import which
from . import ROOT_DIR

WEB_BROWSER = "firefox-esr"
WEB_DRIVER = "geckodriver"


@pytest.fixture(scope="module")
def web_driver() -> webdriver.Firefox:
    options = Options()
    options.headless = True
    options.binary_location = which(WEB_BROWSER)
    options.add_argument('--headless')

    service = Service(executable_path=which(WEB_DRIVER))
    _web_driver = webdriver.Firefox(service=service, options=options)
    _web_driver.implicitly_wait(10)  # Wait for elements to be ready
    yield _web_driver
    _web_driver.quit()  # Close the browser window after tests


@pytest.fixture(scope="module")
def testsite():
    # subprocess.run(["docker", "compose", f"--env-file={ROOT_DIR}/.env", "up", "-d"])
    # time.sleep(5)  # Give the server time to start
    yield None


@pytest.mark.skipif(which(WEB_BROWSER) is None or which(WEB_DRIVER) is None, reason="Web browser not found")
def test_login(web_driver, testsite):
    web_driver.get("http://localhost:5100/login")  # URL of your Flask app's login route

    # Wait for the IdP login page to load and input fields to appear
    WebDriverWait(web_driver, 10).until(
        EC.presence_of_element_located((By.ID, "kc-login"))
    )

    # Simulate user login on the IdP login page
    # Replace the following selectors with the actual ones from your IdP login form
    username_field = web_driver.find_element(By.ID, "username")
    password_field = web_driver.find_element(By.ID, "password")

    # Enter credentials
    username_field.send_keys("cookie_monster")
    password_field.send_keys("changeme")

    login_button = web_driver.find_element(By.ID, "kc-login")
    WebDriverWait(web_driver, 10).until(
        EC.element_to_be_clickable(login_button)
    )

    for _ in range(5):
        try:
            login_button = web_driver.find_element(By.ID, "kc-login")
            login_button.click()
        except ElementClickInterceptedException as exc:
            # It the button is not visible for whatever the reason, force the issue and click!
            web_driver.execute_script("arguments[0].click();", login_button)
            time.sleep(1)
            continue
        except StaleElementReferenceException:
            # Keycloak login screen may have refreshed and button may need to be fetched again.
            time.sleep(1)
            continue
        except NoSuchElementException:
            # The button disappeared. Move on
            break
        pass

    # After redirection, wait for the protected page to load
    web_driver.get("http://localhost:5100/protected")
    WebDriverWait(web_driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # Check if the login was successful by verifying the presence of a specific element or text
    web_driver.get("http://localhost:5100/protected")  # URL of your protected route
    body_text = web_driver.find_element(By.TAG_NAME, "body").text
    # 20583 is the user id of Cookie Monster
    assert "20583" in body_text
