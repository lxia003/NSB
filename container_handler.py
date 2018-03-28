import sys
import container
import commands

#Begin: these variables should be modified 
#       according to your test environment.
#       The asterisk items can be not modified.
#       Whether the question mark items are modified will be based on your configuration.
#=========================================
# container
images = "135.242.139.122:5000/ute"        # (*) for others
container_name = "sc01"                   # the length of container_name should be not greater than 5.
hostname = "{}-nj".format(container_name)  # the default hostname, but you can set any hostname
config_rdnet = True                        # (? depending on your configuration) True or False. True if you start container with RD net
vnc_port = 7001                            # (? depending on config_rdnet) set unique vnc port on you host machine if config_rdnet is False
vnc_resolution = '1600x900'                # (*)
vnc_color_depth = 24
volumes = [                                # (*)
    "-v /home/ute/enb_load:/home/ute/enb_load",   # you can map host file or dir to container
    #"-v /host/path2:/container/path2",
]

# rdnet
rd_net = "135.242.xxx.yyy/24"              # (? depending on config_rdnet) if config_rdnet is true, you must configure rd_net and rd_route
rd_route = "135.242.xxx.129"               # (? depending on config_rdnet) gateway

# lmt
config_lmp = True                          # (? depending on your configuration) True or False
lmt_vtag = 0                               # (? depending on config_lmp) the default value is 0. If you plan to start more than one 
                                           # container, lmt_vtag should be VLAN id which you defined in switch.

# s1ap
config_s1 = True                           # (? depending on your configuration) True or False. True if you will to configure s1ap
# BE CAREFUL: if config_s1 is True, you must configure the below parameters, s1ap with vlan or not, you only need to configure in switch, 
#             if s1ap configure with no valn, you only need one vlan to isolate different containers, vtag is unique in host machine. 
s1_infos = [                               # (? depending on config_s1)
    {'vtag': 404, 'ip': '10.10.80.20/24'}, 
    #{'vtag': 700, 'ip': '10.10.70.23/24'}, 
    #{'vtag': 701, 'ip': '10.10.71.23/24'}, 
    #{'vtag': 702, 'ip': '10.10.72.23/24'}, 
    #{'vtag': 703, 'ip': '10.10.73.23/24'}, 
]
#==========================================
#End


def start():
    # if len(container_name) > 5:
    #    print "The length of the container name should be not greater than 5."
    #    sys.exit(1)

    cmd = "docker ps -a --format '{{.Names}}' "
    containers = commands.run(cmd)

    if container_name not in containers:
        print "container name is not exist. create it..."
        if config_rdnet:
            cmd = "docker run --name {} --hostname {} --net='none' --restart=always -e VNC_COL_DEPTH={} -e VNC_RESOLUTION={} {} --privileged -d {}".format(
                container_name, hostname, vnc_color_depth, vnc_resolution, " ".join(volumes), images)
        else:
            cmd = "docker run --name {} --hostname {} -p {}:5900 --restart=always -e VNC_COL_DEPTH={} -e VNC_RESOLUTION={} {} --privileged -d {}".format(
                container_name, hostname, vnc_port, vnc_color_depth, vnc_resolution, " ".join(volumes), images)

        res = commands.run(cmd)
        if 'Error' in res:
            print "create container failed, error: {}.".format(res)
            sys.exit(99)

    cmd = "docker ps --format '{{.Names}}' "
    containers = commands.run(cmd)
    if container_name not in containers:
        print "container is not started, try starting..."
        commands.run("docker start {}".format(container_name))

    cmd = "docker ps --format '{{.Names}}' "
    containers = commands.run(cmd)
    if container_name not in containers:
        print "container cannot be started, exit."
        sys.exit(99)
    else:
        cmd = "docker exec {} sudo -- bash -c \"echo '127.0.0.1  {}'>>/etc/hosts\"".format(container_name, hostname)
        commands.run(cmd)

    bridge_rd = "br-rd"
    bridge_lmp = "br-lmp"
    bridge_s1 = "br-s1"

    i = 1
    if config_rdnet:
        veth = container.config_veth(container_name, bridge_rd, "eth{}".format(i))
        container.config_container(container_name, veth, rd_net)
        container.config_add_net_route(container_name, veth, rd_route)

    if config_lmp:
        i += 1
        veth = container.config_veth(container_name, bridge_lmp, "eth{}".format(i), lmt_vtag)
        container.config_container(container_name, veth, "192.168.255.126/24")

    if config_s1:
        for info in s1_infos:
            i += 1
            veth = container.config_veth(container_name, bridge_s1, "eth{}".format(i), info.get('vtag'))
            container.config_container(container_name, veth, "%s/24" % info.get('ip'), txoff=True)

        # container.config_container_vpn(container_name)


if __name__ == '__main__':
    start()
    