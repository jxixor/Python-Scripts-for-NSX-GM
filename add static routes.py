#This script will allow one to advertise a /32 route for VMs in a secondary site so that the traffic to and from the VM at the secondary site will go out the secondary sites T0 interfaces.

#Add your NSX Global Manager fqdn, user, and password, along with the name of the T0 you want to add the static routes to.
#Find the IP address of the Tier1 that connects to the T0.  Use the forwarding table on the T0 to fine the subnet the Vms will be on and it will show the IP to use as the next_hop_ip



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

# Static next-hop IP address
next_hop_ip = "100.64.0.1"
locationname = "LOCATIONNAMEVARIABL"

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

# Helper function: create a static route on GlobalT0 using Basic Authentication with PATCH
def create_static_route(t0_id, vm_name, vm_ip, next_hop_ip):
    headers = {"Content-Type": "application/json"}
    route_payload = {
#        "display_name": vm_name,
        "network": f"{vm_ip}/32",
        "next_hops": [
          {"ip_address": next_hop_ip,
          "admin_distance": 1,
          "scope": [
            f"/global-infra/tier-0s/Global_T0/locale-services/{locationname}"
            ]
          }
        ],
 #       "enabled": True
    }
    static_route_url = f"https://{nsx_global_manager_fqdn}/global-manager/api/v1/global-infra/tier-0s/{t0_id}/static-routes/{vm_name}"
    response = requests.patch(static_route_url, auth=HTTPBasicAuth(nsx_username, nsx_password), headers=headers, data=json.dumps(route_payload), verify=False)
    
    if response.status_code in [200, 201, 204]:
        print(f"Static route for {vm_name} created successfully.")
    else:
        print(f"Failed to create static route for {vm_name}: {response.text}")

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

    # Step 3: Create static routes for each VM in GlobalT0 with the fixed next hop IP
    for vm in vms:
        create_static_route(global_t0_id, vm['name'], vm['ip'], next_hop_ip)

# Execute the script
if __name__ == "__main__":
    main()
