import sys
import time
import random
import commands

def config_veth(container_name, br_name, container_veth=None, tag_id=0):
    # Get container pid
    cmd = "docker inspect -f '{{.State.Pid}}' " + container_name
    nspid = commands.run(cmd).replace('\n', '')

    # Generate vethnet pair
    veth_name_host = "-".join([container_name, br_name.replace('br-', '').replace('s1.', ''), container_veth])
    print "veth_name_host:" + veth_name_host
    
    veth_name_peer = "if." + "{:.6f}".format(time.time())[-8:].replace('.', '')
    print "veth_name_peer:" + veth_name_peer

    cmd = "ip link del " + veth_name_host
    commands.run(cmd)

    cmd = "ip link add {} type veth peer name {}".format(veth_name_peer, veth_name_host)
    res = commands.run(cmd).replace('\n', '')
    if 'long' in res:
        print res
        sys.exit(1)
    print "Create veth pair (host:{}, container_out:{}) for container {}.".format(veth_name_host, veth_name_peer, container_name)

    cmd = "ovs-vsctl del-port {} {}".format(br_name, veth_name_host)
    commands.run(cmd)

    tag = "" if tag_id==0 else "tag={}".format(tag_id)
    cmd = "ovs-vsctl add-port {} {} {}".format(br_name, veth_name_host, tag)
    res = commands.run(cmd)
    print "Add port {} into {}.".format(veth_name_host, br_name)

    cmd = "ifconfig " + veth_name_host + " up"
    commands.run(cmd)

    random.seed()
    if container_veth == None:
        container_veth = "eth" + str(random.randint(1000, 10000))
    cmd = "ip link set dev {} name {} netns {}".format(veth_name_peer, container_veth, nspid)
    commands.run(cmd)
    print "Container {}: map ip device (container_out:{}, container_in:{}).".format(container_name, veth_name_peer, container_veth)

    #up veth in container
    cmd = "nsenter -t {} -n ip link set dev {} up".format(nspid, container_veth)
    commands.run(cmd)

    print "Container {}: create ethnet {} successfully.".format(container_name, container_veth)
    return container_veth

def config_container(container_name, veth_name, ip, txoff=False):
    cmd = "docker inspect -f '{{.State.Pid}}' " + container_name
    nspid = commands.run(cmd).replace('\n', '')

    cmd = "nsenter -t {} -n ip addr add {} dev {}".format(nspid, ip, veth_name)
    commands.run(cmd)
    print "Container {}: add ip address {} for {}.\n".format(container_name, ip, veth_name)
    if txoff:
        for i in range(2):
            cmd = "nsenter -t {} -n ethtool -K {} tx off".format(nspid, veth_name)
            commands.run(cmd)
            time.sleep(1)

def config_container_vpn(container_name):
    cmd = "docker inspect -f '{{.State.Pid}}' " + container_name
    nspid = commands.run(cmd).replace('\n', '')
    
    cmd = "docker exec {} openvpn --mktun --dev tun0".format(container_name)
    commands.run(cmd)
    
    cmd = "docker exec {} ip link set tun0 up".format(container_name)
    commands.run(cmd)

    cmd = "docker exec {} ip addr add 27.168.1.200/24 dev tun0".format(container_name)
    commands.run(cmd) 
    
def config_container_vlan(container_name, veth_name, ip, vlan_id):
    cmd = "docker inspect -f '{{.State.Pid}}' " + container_name
    nspid = commands.run(cmd).replace('\n', '')

    cmd = "docker exec {} vconfig add {} {}".format(container_name, veth_name, vlan_id)
    commands.run(cmd)

    cmd = "nsenter {} -n ip address add {} dev  {}.{}".format(nspid, ip, veth_name, vlan_id)
    commands.run(cmd)

    cmd = "nsenter {} -n ifconfig {}.{} up".format(nspid, veth_name, vlan_id)
    commands.run(cmd)

    cmd = "nsenter {} -n ip route add {} dev {}.{}".format(nspid, ip, veth_name, vlan_id)
    commands.run(cmd)

def config_add_net_route(container_name, veth_name, gw_ip):
    cmd = "docker inspect -f '{{.State.Pid}}' " + container_name
    nspid = commands.run(cmd).replace('\n', '')

    cmd = "docker exec {} sudo route add default gw {}".format(container_name, gw_ip)
    print(cmd)
    commands.run(cmd)

