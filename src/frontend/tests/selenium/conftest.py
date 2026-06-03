import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="function")
def driver():
    chrome_options = Options()

    # 1. Resolve Sandbox and shared memory issues (useful for Windows/Linux interoperability)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 2. Disable notifications, pop-up blocking, and EU search engine choice screen
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-search-engine-choice-screen")

    # 3. FIX FOR PASSWORD POP-UP: Completely shut down the password manager
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.password_manager_leak_detection": False
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # 4. Ignore local SSL or certificate errors
    chrome_options.add_argument('--ignore-certificate-errors')

    # Initialize the browser with the correct options
    driver = webdriver.Chrome(options=chrome_options)

    # Maximize the window to ensure responsive layouts don't hide UI elements
    driver.maximize_window()

    yield driver

    # Cleanly close the browser at the end of the test
    driver.quit()