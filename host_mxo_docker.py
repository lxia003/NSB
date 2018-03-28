from host import *

#Begin: these variables should be modified 
#       according to your host machine.
physical_rd_eth = ['eno2']            # e.g. 'eth1'
physical_lmp_eth = ['eno3']   # e.g. 'eth2', 'eth3'
physical_s1_eth = []                  # e.g. 'eth4', 'eth5'
#End---------------------

if __name__ == '__main__':
    bridge_rd = 'br-rd'
    bridge_lmp = 'br-lmp'
    bridge_s1 = 'br-s1'

    for eth in physical_rd_eth:
        create_bridge(bridge_rd, eth)

    for eth in physical_lmp_eth:
        create_bridge(bridge_lmp, eth)

    for  eth in physical_s1_eth:
        create_bridge(bridge_s1, eth)
    
