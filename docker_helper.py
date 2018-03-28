# author: kun.shi@nokia-sbell.com
# date: 2017-12-30
# description: to check and launch container for user
from __future__ import print_function

import getopt

import os
import re
import subprocess
import pwd
import grp
import sys
import pexpect
import time
from pexpect import TIMEOUT, EOF
import commands
import container_handler
from tool_logger import init_log

__version__ = "V1.2"


def generate_container_name(ute_debug_ip):
    suffix = "%03d" % int(ute_debug_ip.split('.')[-1])
    return 'sc' + suffix


def check_user(user):
    logger.info("To check if user(%s) exist" % user)
    user_home = '/home/%s' % user
    if os.path.exists(user_home):
        logger.info('%s exists.' % user)
    else:
        logger.info('%s does not exist. Create...' % user)
        os.mkdir(user_home)
    ute_uid = pwd.getpwnam('ute').pw_uid
    ute_gid = ute_uid
    os.chown(user_home, ute_uid, ute_gid)


def check_container(container_name):
    cmd = '/usr/bin/docker ps -a --no-trunc'
    logger.debug('command : %s' % cmd)
    result = commands.run(cmd)
    logger.info('\n' + result)

    if re.search(r'Up[\t ]+[\w\t ]+%s' % container_name, result):
        logger.info('container(%s) running.' % container_name)
        return 'Running'
    elif re.search(r'Exited[\t ]+[\w\t ]+%s' % container_name, result):
        logger.info('container(%s) stopped.' % container_name)
        return 'Stopped'
    elif re.search(r'Dead[\t ]+[\w\t ]+%s' % container_name, result):
        logger.info('container(%s) dead.' % container_name)
        return 'Dead'
    else:
        logger.info('container(%s) does not exist.' % container_name)
        return 'Not Exist'


def check_ip(ip):
    logger.info("To check if ip(%s) is used." % ip)
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "logs")
        process = pexpect.spawn('ssh ute@%s' % ip)
        process.logfile = open("%s/expect.log" % log_dir, 'w')
        index = process.expect(['yes/no', '[Pp]assword: ', ])
        logger.info('Get index : %s' % index)
        if index == 0:
            process.sendline('yes')
            process.expect('[Pp]assword: ')
        process.sendline('ute')
        process.expect('@([\w-]+):~\$ ')
        result = process.match.group(1)
        logger.info('Get result : %s' % result)
        return result.replace('-nj', '')
    except (TIMEOUT, EOF):
        logger.info('ip %s is not working.' % ip)
        return None


def show_ip_information(container_name):
    logger.info("To show ip configured in container_name.")
    cmd = "docker exec %s sudo -- bash -c 'ifconfig'" % container_name
    result = commands.run(cmd)
    logger.info('\n' + result)


def remove_container(container_name):
    logger.info('To remove container : %s' % container_name)
    cmd = 'docker rm %s' % container_name
    logger.debug('command : %s' % cmd)
    result = commands.run(cmd)
    logger.info(result)
    if 'Error' in result:
        return False
    return True

def stop_container(container_name):
    logger.info('To stop container : %s' % container_name)
    cmd = 'docker stop %s' % container_name
    logger.debug('command : %s' % cmd)
    result = commands.run(cmd)
    logger.info(result)


def start_container(container_name):
    logger.info('To start container : %s' % container_name)
    cmd = 'docker start %s' % container_name
    logger.debug('command : %s' % cmd)
    result = commands.run(cmd)
    logger.info(result)


def create_container(image, container_name,
                     ute_debug_ip, ute_debug_mask, ute_debug_gw, ute_debug_vlan, vnc_resolution='1600x900', **backhaul):
    logger.info('To create container : %s based on %s' % (container_name, image))
    logger.info('backhaul parameters : %s ' % backhaul)
    container_handler.images = image
    container_handler.container_name = container_name
    container_handler.hostname = "{}-nj".format(container_name)
    container_handler.rd_net = ute_debug_ip + "/" + ute_debug_mask
    container_handler.lmt_vtag = ute_debug_vlan
    container_handler.rd_route = ute_debug_gw
    container_handler.vnc_resolution = vnc_resolution
    container_handler.volumes.append("-v /home/%s:/home/ute/backup" % container_name)
    # configure backhaul ip and vlan
    #  {'vtag': 404, 'ip': '10.10.80.20/24'},
    container_handler.s1_infos = []
    for item in backhaul:
        temp = backhaul[item].strip()
        if temp:
            ip = temp.split(':')[0]
            vtag = temp.split(':')[-1]
            container_handler.s1_infos.append({'vtag': int(vtag), 'ip': ip})
    logger.info("s1 infos : %s" % container_handler.s1_infos)

    container_handler.start()


def get_network_mask(ute_debug_mask):
    ute_debug_mask = str(ute_debug_mask).strip()
    if re.search(r'^\d{0,2}$', ute_debug_mask):
        return ute_debug_mask
    if re.search(r'^\d{0,3}\.\d{0,3}\.\d{0,3}\.\d{0,3}$', ute_debug_mask):
        mask = ''
        for i in ute_debug_mask.split('.'):
            mask += str(bin(int(i)))[2:]
        return str(mask.count('1'))
    return None


def configure_ute(ute_debug_ip, shared_dir=''):
    logger.info('Start to configure UTE on %s' % ute_debug_ip)
    result = True
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(base_dir, "logs")
        process = pexpect.spawn('ssh ute@%s' % ute_debug_ip)
        process.logfile = open("%s/expect_config_ute.log" % log_dir, 'w')
        index = process.expect(['yes/no', '[Pp]assword: ', ])
        logger.info('Get index : %s' % index)
        if index == 0:
            process.sendline('yes')
            process.expect('[Pp]assword: ')
        process.sendline('ute')
        process.expect('~\$ ')
        if shared_dir:
            shared_dir = shared_dir.replace("\\", '/')
            logger.info('To mount shared directory : %s' % shared_dir)
            process.sendline('sudo mount -t cifs %s /home/ute/win_share/' % shared_dir)
            process.expect('[Pp]assword: ')
            process.sendline('ute')
            process.expect('~\$ ')
            process.sendline('sudo chmod -R 777 /home/ute/win_share/')
            process.expect('~\$ ')
    except Exception as e:
        logger.error(e)
        result = False
    return result


def check_ute_status(ute_debug_ip, ute_debug_gw):
    logger.info("To check ute status.")
    is_ready = False
    cmd = "ping %s -c 1" % ute_debug_ip
    res = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    logger.info("Get response : %s" % res)
    if '100% packet loss' not in res:
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(base_dir, "logs")
            process = pexpect.spawn('ssh ute@%s' % ute_debug_ip)
            process.logfile = open("%s/expect_ute_status.log" % log_dir, 'w')
            index = process.expect(['yes/no', '[Pp]assword: ', ])
            logger.info('Get index : %s' % index)
            if index == 0:
                process.sendline('yes')
                process.expect('[Pp]assword: ')
            process.sendline('ute')
            process.expect('~\$ ')
            process.sendline('ping %s -c 4' % ute_debug_gw)
            process.expect('~\$ ')
            res = process.before
            logger.info('Get result : %s' % res)
            if '100% packet loss' not in res:
                is_ready = True
        except Exception as e:
            logger.error(e)
    return is_ready


def handle_dead_container(container_name):
    result = True
    #remove /home/docker/overlay/c1bca989ba4e45ed21b0c14f2462f10cfa58b92eb6a28dbc022281e52a7499b1/merged: device or resource busy
    try:
        res = subprocess.check_output("docker rm %s" % container_name, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        res = e.output
    m = re.search(r'overlay/(\w+)/merged', res)
    if m:
        logger.info("Get docker information : %s" % m.group(1))
        try:
            res = subprocess.check_output(r'grep %s /proc/*/mountinfo' % m.group(1), shell=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            res = e.output
        logger.info('Get grep result : %s' % res)
        m = re.search(r'/proc/(\w+)/mountinfo:\w+', res)
        if m:
            logger.info('Get process id : %s' % m.group(1))
            res = subprocess.check_output(r'ps -ef | grep %s' % m.group(1), shell=True, stderr=subprocess.STDOUT)
            logger.info('Get process : %s' % res)
            if 'ntp' in res:
                logger.info('Restart ntp...')
                res = subprocess.check_output(r'systemctl restart ntpd', shell=True, stderr=subprocess.STDOUT)
            else:
                logger.info('To kill it...')
                res = subprocess.check_output(r'kill -9 %s' % m.group(1), shell=True, stderr=subprocess.STDOUT)
            logger.info('Get result : %s' % res)
        else:
            logger.error('Can not get process id!!')
            result = False
    else:
        logger.error('Can not handle dead container!!')
        result = False
    return result


def main():
    logger.info("Get input parameters : %s" % sys.argv)
    if len(sys.argv) < 5:
        logger.info("Wrong parameter numbers.")
        sys.exit(1)
    to_recreate_container = False
    vnc_resolution = '1600x900'
    image = "135.242.139.121:5000/ute_mxo"
    backhaul = {'uplane_ip_vlan': '', 'cplane_ip_vlan': '', 'mplane_ip_vlan': '',}
    opts, args = getopt.getopt(sys.argv[1:], 'fd:g:k:v:i:r:u:c:m:s:')
    shared_dir = ''
    for opt, arg in opts:
        if opt == '-d':
            ute_debug_ip = arg
        elif opt == '-g':
            ute_debug_gw = arg
        elif opt == '-k':
            ute_debug_mask = get_network_mask(arg)
            if ute_debug_mask is None:
                logger.error('Network mask %s has wrong format.' % ute_debug_mask)
                sys.exit(4)
        elif opt == '-r':
            vnc_resolution = arg
        elif opt == '-v':
            ute_debug_vlan = arg
        elif opt == '-i':
            image = arg.replace('http://', '')
        elif opt == '-f':
            to_recreate_container = True
        elif opt == '-u':
            backhaul['uplane_ip_vlan'] = arg
        elif opt == '-c':
            backhaul['cplane_ip_vlan'] = arg
        elif opt == '-m':
            backhaul['mplane_ip_vlan'] = arg
        elif opt == '-s':
            shared_dir = arg
    container_name = check_ip(ute_debug_ip)

    # to check if user exists, else create it.
    expected_container_name = generate_container_name(ute_debug_ip)
    if container_name and expected_container_name not in container_name:
        logger.warn('*' * 10)
        logger.warn('!! Other host is using this IP(%s).' % ute_debug_ip)
        logger.warn('*' * 10)
        sys.exit(5)
    container_name = expected_container_name
    check_user(container_name)

    # to check container state
    state = check_container(container_name)

    if state == 'Not Exist':
        logger.info('To create container.')
        create_container(image, container_name,
                         ute_debug_ip, ute_debug_mask, ute_debug_gw, ute_debug_vlan, vnc_resolution, **backhaul)
    else:
        logger.info('To re-create container? %s' % to_recreate_container)
        if to_recreate_container:
            if state == 'Running':
                stop_container(container_name)
            if state == 'Dead':
                if not handle_dead_container(container_name):
                    sys.exit(6)
            if not remove_container(container_name):
                state = check_container(container_name)
                if state == 'Dead':
                    logger.info('Dead found when rm container! Remove again!')
                    if not handle_dead_container(container_name):
                        sys.exit(6)
            create_container(image, container_name,
                             ute_debug_ip, ute_debug_mask, ute_debug_gw, ute_debug_vlan, vnc_resolution,
                             **backhaul)
        else:
            if state != 'Running':
                start_container(container_name)
    check_container(container_name)

    # check ip information
    show_ip_information(container_name)

    # wait for container ready
    time.sleep(60)

    # check ute status is ready
    timer_counter = 0
    while not check_ute_status(ute_debug_ip, ute_debug_gw):
        time.sleep(5)
        timer_counter += 1
        if timer_counter == 20:
            logger.error("UTE can not be ready in 3 mins.")
            sys.exit(7)

    time.sleep(10)

    # configure ute
    result = configure_ute(ute_debug_ip, shared_dir)
    if not result:
        sys.exit(8)


if __name__ == '__main__':
    logger = init_log('docker_helper')
    logger.info("start %s : %s" % (__file__, __version__))
    main()
