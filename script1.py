import json
from pyVim.connect import SmartConnect, Disconnect
import ssl
import getpass
import socket
from pyVmomi import vim
#Function that reads my vCenter hostname and username from vcenterconfig.json
def read_config_file(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config['vcenter_host'], config['username']

config_file = 'vcenterconfig.json'
vcenter_host, username = read_config_file(config_file)

print(f"vCenter Host: {vcenter_host}")
print(f"Username: {username}")
#Function to provide session data
def get_session_info(service_instance, vcenter_host):
    session_manager = service_instance.content.sessionManager
    session_info = session_manager.currentSession

    source_ip = socket.gethostbyname(socket.gethostname())
#output of domain user, vcenter server, and source IP
    print(f"DOMAIN/Username: {session_info.userName}")
    print(f"vCenter Server: {vcenter_host}")
    print(f"Source IP: {source_ip}")



#Function to search VMs and return their relevant data (name, state, CPUs, memory, and IP)
def get_vm_data(service_instance, search_name=None):
    content = service_instance.RetrieveContent()
    vm_view = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True
    )
    vms = vm_view.view #list of all VMs in vCenter
    filtered_vms = [] #store filtered VMs

    #apply the filter after looping through VMs
    for vm in vms:
        if search_name:
            if search_name.lower() in vm.name.lower():
                filtered_vms.append(vm)
        else: filtered_vms.append(vm) #return all VMs if no filter provided
    vm_view.Destroy()
    for vm in filtered_vms:
        print_vm_data(vm)

def print_vm_data(vm):
    summary = vm.summary
    guest = vm.guest

    vm_name = summary.config.name
    power_state = summary.runtime.powerState
    num_cpus = summary.config.numCpu
    memory_gb = summary.config.memorySizeMB / 1024

    if guest.toolsRunningStatus == 'guestToolsRunning' and guest.ipAddress:
        ip_address = guest.ipAddress
    else:
        ip_address = "VMware Tools not running or no IP"

        print(f"VM Name: {vm_name}")
        print(f"Power State: {power_state}")
        print(f"Number of CPUs: {num_cpus}")
        print(f"Memory: {memory_gb:.2f} GB")
        print(f"IP Address: {ip_address}")
        
if __name__ == "__main__":
    config_file = 'vcenterconfig.json'
    vcenter_host, username = read_config_file(config_file)
    password = getpass.getpass("Enter vCenter Password: ")

    sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    sslContext.verify_mode = ssl.CERT_NONE
#Here is where the connection to vCenter is established and the session info function is called
    service_instance = SmartConnect(host=vcenter_host, user=username, pwd=password, sslContext=sslContext)

    try:
        get_session_info(service_instance, vcenter_host)
        search_name = input("Enter VM name (leave blank for all VMS): ")
        get_vm_data(service_instance, search_name)
    finally:
        Disconnect(service_instance)