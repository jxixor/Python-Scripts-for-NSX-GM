#This script deletes static routes from the T0 in a federated environment.  The list of static routes it will delete are from the test file VMlist.txt

#Add your NSX Global Manager fqdn, user, and password, along with the name of the T0 you want to add the static routes to.

import requests
import json
from requests.auth import HTTPBasicAuth
import urllib3

# Disable warnings for unverified SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# NSX Global Manager credentials and parameters
nsx_global_manager_fqdn = "nsxtgm.lab.localVARIABLE"
nsx_username = "USERVARIABLE"
nsx_password = "PASSWORD!password!VARIABLE"
global_t0_name = "GlobalT0VARIABLe"

# Read VM names and IP addresses from VMlist.txt file
def get_vms_from_file():
    vms = []
    try:
        with open('./VMlist.txt', 'r') as file:
            for line in file:
                vm_info = line.strip()
                if vm_info:
                    vm_name, vm_ip = vm_info.split(',')
                    vms.append({
                        'name': vm_name.strip(),
                        'ip': vm_ip.strip()
                    })
    except FileNotFoundError:
        print("Error: 'VMlist.txt' file not found.")
    except Exception as e:
        print(f"Error reading VMs from file: {e}")
    return vms

# Helper function: find NSX object ID (Tier-0 or Tier-1) by name using Global API
def find_nsx_object_id_by_name(object_type, object_name):
    headers = {"Content-Type": "application/json"}
    api_url = f"https://{nsx_global_manager_fqdn}/global-manager/api/v1/global-infra/{object_type}s"
    response = requests.get(api_url, auth=HTTPBasicAuth(nsx_username, nsx_password), headers=headers, verify=False)
    
    if response.status_code == 200:
        objects = response.json().get('results', [])
        for obj in objects:
            if obj['display_name'] == object_name:
                return obj['id']
        print(f"{object_name} not found.")
    else:
        print(f"Failed to retrieve {object_type} objects: {response.text}")
    return None

# Helper function: delete a static route on GlobalT0 using Basic Authentication with DELETE
def delete_static_route(t0_id, vm_name):
    headers = {"Content-Type": "application/json"}
    static_route_url = f"https://{nsx_global_manager_fqdn}/global-manager/api/v1/global-infra/tier-0s/{t0_id}/static-routes/{vm_name}"
    response = requests.delete(static_route_url, auth=HTTPBasicAuth(nsx_username, nsx_password), headers=headers, verify=False)
    
    if response.status_code in [200, 204]:
        print(f"Static route for {vm_name} deleted successfully.")
    else:
        print(f"Failed to delete static route for {vm_name}: {response.text}")

# Main function
def main():
    # Step 1: Get VMs from file
    vms = get_vms_from_file()
    if not vms:
        print("No VMs found in the file.")
        return
    
    # Step 2: Find NSX object ID for GlobalT0 using Global API
    global_t0_id = find_nsx_object_id_by_name("tier-0", global_t0_name)
    if not global_t0_id:
        print("Failed to retrieve NSX object ID for GlobalT0.")
        return

    # Step 3: Delete static routes for each VM in GlobalT0
    for vm in vms:
        delete_static_route(global_t0_id, vm['name'])

# Execute the script
if __name__ == "__main__":
    main()
