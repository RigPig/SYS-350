"""
I adapted code from the pyvmomi community samples: https://github.com/vmware/pyvmomi-community-samples/tree/master
I also utilized the Python GPT created by Nicholas Barker: https://www.linkedin.com/in/nickabarker/
"""

import json
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import atexit
import getpass
from pyVim.task import WaitForTask

# read vCenter info from vcenterconfig.json
def read_config_file(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config['vcenter_host'], config['username']

# function to connect to vCenter
def connect_to_vcenter(host, user, password):
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.verify_mode = ssl.CERT_NONE
    service_instance = SmartConnect(host=host, user=user, pwd=password, sslContext=context)
    atexit.register(Disconnect, service_instance)
    return service_instance

# Retrieve all VMs in vCenter
def get_all_vms(content):
    container = content.viewManager.CreateContainerView(
        content.rootFolder, [vim.VirtualMachine], True)
    vms = container.view    
    container.Destroy()
    return vms

# Filter VMs based on name (from filter_vms.py)
def filter_vms(vms, search_name=None):
    filtered_vms = []
    for vm in vms:
        if search_name:
            if search_name.lower() in vm.name.lower():
                filtered_vms.append(vm)
        else:
            filtered_vms.append(vm)
    return filtered_vms

# Power on the VMs (from virtual_machine_power_cycle_and_question.py)
def power_on_vms(vms):
    for vm in vms:
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOff:
            print(f"Powering on VM: {vm.name}")
            task = vm.PowerOn()
            task.wait_for_completion()

# Power off the VMs (from virtual_machine_power_cycle_and_question.py)
def power_off_vms(vms):
    for vm in vms:
        if vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn:
            print(f"Powering off VM: {vm.name}")
            task = vm.PowerOff()
            task.wait_for_completion()

# Snapshot the VMs
def take_snapshot(vms, snapshot_name="MilestoneSnapshot"):
    for vm in vms:
        print(f"Taking snapshot for VM: {vm.name}")
        task = vm.CreateSnapshot(snapshot_name, "Snapshot for automation script", False, False)
        task.wait_for_completion()

# Restore the most recent snapshot
def restore_snapshot(vms):
    for vm in vms:
        if vm.snapshot:
            print(f"Restoring latest snapshot for VM: {vm.name}")
            snapshot = vm.snapshot.currentSnapshot
            task = snapshot.RevertToSnapshot_Task()
            task.wait_for_completion()

def clone_vm(vm, clone_name):
    spec = vim.vm.CloneSpec()
    spec.location = vim.vm.RelocateSpec()  
    spec.powerOn = False  
    print(f"Cloning VM: {vm.name} to {clone_name}")
    task = vm.Clone(name=clone_name, folder=vm.parent, spec=spec)
    WaitForTask(task)  
# Delete VMs 
def delete_vms(vms):
    for vm in vms:
        print(f"Deleting VM: {vm.name}")
        task = vm.Destroy_Task()
        task.wait_for_completion()

# Main menu for operations
def menu(service_instance):
    content = service_instance.RetrieveContent()
    vms = get_all_vms(content)

    while True:
        print("\nSelect an action:")
        print("1. Power On VMs")
        print("2. Power Off VMs")
        print("3. Take Snapshot")
        print("4. Restore Snapshot")
        print("5. Clone VMs")
        print("6. Delete VMs")
        print("7. Exit")

        choice = input("Enter your choice: ")
        
        if choice == "7":
            print("Exiting.")
            break

        search_name = input("Enter VM name to filter (or leave blank for all VMs): ")
        filtered_vms = filter_vms(vms, search_name)

        if choice == "1":
            power_on_vms(filtered_vms)
        elif choice == "2":
            power_off_vms(filtered_vms)
        elif choice == "3":
            take_snapshot(filtered_vms)
        elif choice == "4":
            restore_snapshot(filtered_vms)
        elif choice == "5":
            clone_name = input("Enter new VM name for cloning: ")
            
            for vm in filtered_vms:
                clone_vm(vm, clone_name)
        elif choice == "6":
            confirm = input("Are you sure you want to delete these VMs? (y/n): ").lower() == 'y'
            if confirm:
                delete_vms(filtered_vms)
        else:
            print("Invalid choice, please try again.")

# Main execution
if __name__ == "__main__":
    config_file = 'vcenterconfig.json'
    vcenter_host, vcenter_user = read_config_file(config_file)

    # Prompt for the password
    vcenter_password = getpass.getpass("Enter vCenter password: ")

    service_instance = connect_to_vcenter(vcenter_host, vcenter_user, vcenter_password)
    try:
        menu(service_instance)
    finally:
        Disconnect(service_instance)
