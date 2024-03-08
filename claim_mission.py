import requests
import time
import urllib3
import subprocess

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def read_token():
    token = "Bearer Authorization_token"
    return token

def get_tasks(token):
    url = "https://platform.synack.com/api/tasks/v2/tasks"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    params = {
        "perPage": 20,
        "viewed": "true",
        "page": 1,
        "status": "PUBLISHED",
        "sort": "CLAIMABLE",
        "sortDir": "DESC",
        "includeAssignedBySynackUser": "false"
    }
    
    response = requests.get(url, headers=headers, params=params, verify=False)
    if response.status_code == 200:
        tasks = response.json()
        if tasks:
            return tasks
    return None

def post_claim_task(token, task):
    url = f"https://platform.synack.com/api/tasks/v1/organizations/{task['organizationUid']}/listings/{task['listingUid']}/campaigns/{task['campaignUid']}/tasks/{task['id']}/transitions"
    payload = {"type": "CLAIM"}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    return response.status_code

def main():
    token = read_token()

    while True:
        tasks = get_tasks(token)
        if tasks:
            for task in tasks:
                while True:
                    status_code = post_claim_task(token, task)
                    if status_code == 201:
                        print("Mission claimed successfully.")
                        break
                    elif status_code == 412:
                        print("Precondition failed, stopping attempts to claim this task.")
                        break
                    else:
                        print("Attempting to claim mission again in 5 seconds.")
                        time.sleep(5)
                if status_code == 401:
                    print("Token is expired.") 
                    break
        time.sleep(5)

if __name__ == "__main__":
    main()
