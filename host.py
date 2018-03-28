import subprocess
import sys


def create_bridge(br_name, physical_eth, br_ip='', autoactive=True):
    try:
        res = subprocess.check_output('ovs-vsctl del-br ' + br_name, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if not "no bridge named" in e.output:
            print "Pre-del bridge: {}".format(e.output)
    try:
        res = subprocess.check_output('ovs-vsctl add-br ' + br_name, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print "Add bridge: {} failed.".format(e.output)
    
    res = subprocess.check_output('ovs-vsctl show', shell=True, stderr=subprocess.STDOUT)
    #print res
    if not br_name in res:
        print 'Create bridge {} failed.'.format(br_name)
        sys.exit(1)
    print 'Create bridge {} successfully.'.format(br_name)

    try:
        subprocess.check_output(['ovs-vsctl', 'del-port', br_name, physical_eth], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        if not "no port named" in e.output:
            print "Pre-del port: {}".format(e.output)
    try:
        subprocess.check_output(['ovs-vsctl', 'add-port', br_name, physical_eth], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print 'config bridge failed:'
        print e.output
        sys.exit(1)
    print "Add port {} into {} successfully.".format(physical_eth, br_name)

    if autoactive:
        #subprocess.call(['ifconfig', physical_eth, '0'], stderr=subprocess.STDOUT)
        subprocess.call(['ifconfig', br_name, 'up'], stderr=subprocess.STDOUT)
    
    if br_ip.strip():
        subprocess.call(['ifconfig', br_name, br_ip], stderr=subprocess.STDOUT)
        try:
            res = subprocess.check_output(['ifconfig', br_name], stderr=subprocess.STDOUT)
            if br_ip in res:
                print 'Create bridge IP [%s] successfully.' %(br_ip)
            else:
                print 'Create bridge IP [%s] failed.' %(br_ip)
        except subprocess.CalledProcessError as e:
            print 'config bridge IP failed:'
            print e.output
            sys.exit(1)
    
    print "\n"


def create_host_vlan(physical_eth, vlan_id):
    try:
        res = subprocess.check_output('vconfig add ' + physical_eth + ' ' + str(vlan_id), shell=True, stderr=subprocess.STDOUT)
        subprocess.check_output("ifconfig {}.{} up".format(physical_eth, str(vlan_id)), shell=True, stderr=subprocess.STDOUT)
        #print res
    except subprocess.CalledProcessError as e:
        if not "error: File exists" in e.output:
            print "vconfig: {}".format(e.output)
    
    return '.'.join([physical_eth, str(vlan_id)])


def create_bridge_based_vlan(br_name, physical_eth, vlan_id):
    br = '.'.join([br_name, str(vlan_id)])
    veth = create_host_vlan(physical_eth, vlan_id)
    create_bridge(br, veth)
