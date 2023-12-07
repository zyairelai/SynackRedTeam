import subprocess
import sys
import requests
from bs4 import BeautifulSoup
import json
import time
import urllib3
import datetime
from time import sleep

# Constants
EMAIL = ""
PASSWORD = ""
DUO_POLL_INTERVAL = 2  # seconds
MAX_RETRIES = 3
DEVICE_NAME = ""
DEVICE_KEY = ""
file_path = '/tmp/synacktoken'


def synack():
    def is_json(response):
        try:
            response.json()
            return True
        except ValueError:
            return False

    # Function to exit on error with a message
    def exit_on_error(message):
        print(message)
        sys.exit(1)

    # Initialize a session with a cookie jar
    session = requests.Session()
    session.cookies = requests.cookies.RequestsCookieJar()

    # Custom headers
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br"
    }

    # Step 1: GET request to login.synack.com to fetch CSRF token
    try:
        response = session.get('https://login.synack.com', headers=custom_headers)
        if response.status_code != 200:
            exit_on_error("Failed to fetch CSRF token")
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']
    except Exception as e:
        exit_on_error(f"Error during fetching CSRF token: {e}")

    # Step 2: POST request to /api/authenticate with credentials
    for attempt in range(MAX_RETRIES):
        try:
            login_url = 'https://login.synack.com/api/authenticate'
            login_data = {"email": EMAIL, "password": PASSWORD}
            headers = {'X-Csrf-Token': csrf_token}
            response = session.post(login_url, json=login_data, headers=headers)
            
            if response.status_code == 200 and is_json(response):
                response_data = response.json()
                duo_auth_url = response_data.get('duo_auth_url')
                if duo_auth_url:
                    print("[!] Login successful on attempt {}".format(attempt + 1))
                    break  # Successful login, break out of the loop
                else:
                    exit_on_error("Duo Auth URL missing in response")
            else:
                print(f"Login attempt {attempt + 1} failed, status code: {response.status_code}, retrying...")
                if attempt == MAX_RETRIES - 1:
                    exit_on_error("Login failed after maximum retries")

        except Exception as e:
            print(f"Login attempt {attempt + 1} failed with error: {e}")
            if attempt == MAX_RETRIES - 1:
                exit_on_error("Error during login after maximum retries: {e}")



    # Step 3: GET request to Duo Auth URL (Request 1 to DUO)
    try:
        response = session.get(duo_auth_url, headers=custom_headers)
        if response.status_code != 200:
            exit_on_error("Failed to GET Duo Auth URL")
        session.cookies.update(response.cookies)  # Update cookie jar

        # Handle redirection
        redirect_url = response.history[-1].headers['Location']
        redirect_full_url = f"https://api-64d8e0cf.duosecurity.com{redirect_url}"
        response = session.get(redirect_full_url, headers=custom_headers)
        if response.status_code != 200:
            exit_on_error("Failed to follow redirect URL")
        session.cookies.update(response.cookies)  # Update cookie jar
    except Exception as e:
        exit_on_error(f"Error during Duo Auth process: {e}")

    # Extract XSRF token from the script tag in the HTML response
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': 'base-data'})
        json_data = json.loads(script_tag.text)
        xsrf_token = json_data['xsrf_token']
    except Exception as e:
        exit_on_error(f"Error extracting XSRF token: {e}")

    # Extract 'sid' and 'tx' from URL
    try:
        sid = response.url.split('sid=')[1].split('&')[0]
        tx = redirect_url.split('&tx=')[1].split('&')[0]
    except Exception as e:
        exit_on_error(f"Error extracting 'sid' and 'tx': {e}")
    # Step 4: POST Request to Duo with XSRF Token and extracted data
    try:
        base_url = "https://api-64d8e0cf.duosecurity.com/frame/frameless/v4/auth"
        post_url = f"{base_url}?sid={sid}&tx={tx}"
        post_data = {
        'tx': tx,
        'parent': 'None',
        '_xsrf': xsrf_token,
        'java_version': '',
        'flash_version': '',
        'screen_resolution_width': '1920',
        'screen_resolution_height': '1080',
        'color_depth': '24',
        'ch_ua_error': '',
        'client_hints': '',
        'is_cef_browser': 'false',
        'is_ipad_os': 'false',
        'is_ie_compatibility_mode': '',
        'is_user_verifying_platform_authenticator_available': 'false',
        'user_verifying_platform_authenticator_available_error': '',
        'acting_ie_version': '',
        'react_support': 'true',
        'react_support_error_message': '',
        }
        cookies_header = {'Cookie': '; '.join([f'{name}={value}' for name, value in session.cookies.items()])}
        response = session.post(post_url, data=post_data, headers={**custom_headers, **cookies_header})
        if response.status_code != 200:
            exit_on_error("Failed to POST data to Duo")
        session.cookies.update(response.cookies)
    except Exception as e:
        exit_on_error(f"Error during POST request to Duo: {e}")

    # Step 5: Follow Redirects and Perform Health Check
    try:
        health_check_urls = [
            f'https://api-64d8e0cf.duosecurity.com/frame/v4/preauth/healthcheck?sid={sid}',
            f'https://api-64d8e0cf.duosecurity.com/frame/v4/preauth/healthcheck/data?sid={sid}',
            f'https://api-64d8e0cf.duosecurity.com/frame/v4/return?sid={sid}'
        ]
        for url in health_check_urls:
            response = session.get(url)
            if response.status_code != 200:
                exit_on_error(f"Health check failed for URL: {url}")
            session.cookies.update(response.cookies)
    except Exception as e:
        exit_on_error(f"Error during health check: {e}")

    # Step 5.1: POST Request again to Duo with XSRF Token and extracted data
    try:
        base_url = "https://api-64d8e0cf.duosecurity.com/frame/frameless/v4/auth"
        post_url = f"{base_url}?sid={sid}&tx={tx}"
        post_data = {
        'tx': tx,
        'parent': 'None',
        '_xsrf': xsrf_token,
        'java_version': '',
        'flash_version': '',
        'screen_resolution_width': '1920',
        'screen_resolution_height': '1080',
        'color_depth': '24',
        'ch_ua_error': '',
        'client_hints': '',
        'is_cef_browser': 'false',
        'is_ipad_os': 'false',
        'is_ie_compatibility_mode': '',
        'is_user_verifying_platform_authenticator_available': 'false',
        'user_verifying_platform_authenticator_available_error': '',
        'acting_ie_version': '',
        'react_support': 'true',
        'react_support_error_message': '',
        }
        cookies_header = {'Cookie': '; '.join([f'{name}={value}' for name, value in session.cookies.items()])}
        response = session.post(post_url, data=post_data, headers={**custom_headers, **cookies_header})
        if response.status_code != 200:
            exit_on_error("Failed to POST data to Duo for step 5.1")
        session.cookies.update(response.cookies)
    except Exception as e:
        exit_on_error(f"Error during POST request to Duo: {e}")

    # Step 6: Setup Device Prompt
    try:
        prompt_urls = [
            f'https://api-64d8e0cf.duosecurity.com/frame/v4/auth/prompt?sid={sid}',
            f'https://api-64d8e0cf.duosecurity.com/frame/v4/auth/prompt/data?sid={sid}'
        ]
        for url in prompt_urls:
            response = session.get(url)
            if response.status_code != 200:
                exit_on_error(f"Failed to setup device prompt for URL: {url}")
    except Exception as e:
        exit_on_error(f"Error during device prompt setup: {e}")
    # Step 7: Sending POST to Duo for Device Selection and Duo Push
    try:
        prompt_url = 'https://api-64d8e0cf.duosecurity.com/frame/v4/prompt'
        prompt_data = {
            'device': DEVICE_NAME,  # Default device
            'factor': 'Duo Push',
            'postAuthDestination': 'OIDC_EXIT',
            'browser_features': '{"touch_supported":false, "platform_authenticator_status":"unavailable", "webauthn_supported":true}',
            'sid': sid
        }
        prompt_response = session.post(prompt_url, data=prompt_data)
        if prompt_response.status_code != 200 or not is_json(prompt_response):
            exit_on_error("Failed to send POST to Duo for device selection")
        txid = prompt_response.json()['response']['txid']
        subprocess.run(["python3","main.py"], check=True)
    except Exception as e:
        exit_on_error(f"Error during Duo device selection POST: {e}")

    # Step 8: Polling for Duo Push Status
    try:
        while True:
            status_data = {'txid': txid, 'sid': sid}
            status_response = session.post('https://api-64d8e0cf.duosecurity.com/frame/v4/status', data=status_data)
            if not status_response.status_code == 200 or not is_json(status_response):
                exit_on_error("Failed to poll Duo Push status")
            status_response_data = status_response.json()

            if status_response_data['response']['status_code'] == 'allow':
                # print("Duo authentication successful.")
                break
            elif status_response_data['response']['status_code'] == 'timeout':
                print("Device failed to respond.")
                # Handling a timeout scenario without switching to a backup device.
                # Additional actions can be added here.
                break

            time.sleep(DUO_POLL_INTERVAL)
    except Exception as e:
        exit_on_error(f"Error during polling for Duo Push status: {e}")


    # Step 9: Finalizing Authentication with Synack
    try:
        final_auth_url = 'https://api-64d8e0cf.duosecurity.com/frame/v4/oidc/exit'
        final_auth_data = {
            'sid': sid,
            'txid': txid,
            'factor': 'Duo Push',
            'device_key': DEVICE_KEY,
            '_xsrf': xsrf_token,
            'dampen_choice': 'false'
        }
        final_auth_response = session.post(final_auth_url, data=final_auth_data)
        if final_auth_response.status_code != 200:
            exit_on_error("Failed to finalize authentication with Synack")
        #print("URL:", final_auth_response.url)
    except Exception as e:
        exit_on_error(f"Error during final authentication with Synack: {e}")


    # Step 10: Final Redirect to Synack with Grant Token
    try:
        final_response = session.get(final_auth_response.url)
        if final_response.status_code != 200:
            exit_on_error("Failed during final redirect to Synack")
        grant_token = final_response.url.split('grant_token=')[1]
        #print("Login process complete. Grant Token:", grant_token)
    except Exception as e:
        exit_on_error(f"Error during final redirect: {e}")

    # Step 11: GET request to /token?grant_token= to receive access_token
    headers['X-Requested-With'] = 'XMLHttpRequest'
    response = requests.get(f'https://platform.synack.com/token?grant_token={grant_token}', headers=headers)
    #print("Text:", response.text)
    access_token = response.json().get('access_token') if is_json(response) else None
    return access_token

def write_token_to_file(token, file_path):
    try:
        with open(file_path, 'w') as file:
            file.write(token)
    except Exception as e:
        print(f"Error writing to file: {e}")


auth = synack()

print("Access-Token:", auth)

write_token_to_file(auth, file_path)