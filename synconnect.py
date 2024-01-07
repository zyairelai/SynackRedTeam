import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


# Replace with your login credentials
username = 'username'
password = 'password'

# Specify the file path
file_path = '/tmp/synacktoken'
proxy_host = ''

# Check if proxy settings are provided
if proxy_host and proxy_port:
    # Create a Proxy object
    proxy = Proxy({
        'proxyType': ProxyType.MANUAL,
        'httpProxy': f'{proxy_host}:{proxy_port}',
        'ftpProxy': f'{proxy_host}:{proxy_port}',
        'sslProxy': f'{proxy_host}:{proxy_port}',
        'noProxy': ''  # You can specify exceptions here
    })

    # Set up Firefox options with proxy settings
    options = webdriver.FirefoxOptions()
    options.add_argument('--proxy-server=http://{}:{}'.format(proxy_host, proxy_port))
else:
    # If no proxy is required, set up Firefox options without proxy settings
    options = webdriver.FirefoxOptions()


options.headless = True  # Set to True if you don't want to see the browser
driver = webdriver.Firefox(options=options)

try:
    # Step 1: Perform an initial request to get the CSRF token
    driver.get('https://login.synack.com/')

    # Step 2: Perform the login
    driver.get('https://login.synack.com/')
    driver.find_element(By.NAME, 'email').send_keys(username)
    driver.find_element(By.NAME, 'password').send_keys(password)
    driver.implicitly_wait(20)
    driver.find_element(By.CLASS_NAME, 'btn-blue').click()
    driver.implicitly_wait(25)
    driver.find_element(By.CLASS_NAME, 'btn-blue').click()
    try:
        driver.implicitly_wait(25)
        element = WebDriverWait(driver, 25).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'button--xlarge'))
        )
        element.click()
    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        pass
    
    # DUO logic
    subprocess.run(["python3","main.py"], check=True)
    # DUO logic end
    WebDriverWait(driver, 50).until(EC.title_contains("Platform"))


    key_to_retrieve = "shared-session-com.synack.accessToken"
    stored_value = driver.execute_script(f"return sessionStorage.getItem('{key_to_retrieve}');")
    
    # Print and write the retrieved value to the specified file
    print(f"Value from session storage for key '{key_to_retrieve}': {stored_value[:10]}")
    with open(file_path, 'w') as file:
        file.write(stored_value)

finally:
    try:
        # Close the browser window
        if 'driver' in locals() and driver is not None:
            driver.quit()
    except WebDriverException as e:
        print(f"Error closing the browser: {str(e)}")

