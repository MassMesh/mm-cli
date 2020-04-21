from argh import arg, wrap_errors
import socket
import subprocess
from . import util

@arg('client_pub_key', help='public key of the client')
@arg('client_ip', help='client tunnel ip')
@wrap_errors([socket.error, IOError])
def addclient(client_pub_key, client_ip):
    'add a client ip reservation'
    print ('work in progress', util.Hemicarp)
    print('addclient()', client_pub_key, client_ip)
    return util.bpk_to_ipaddr(client_pub_key)
    ## 3. Add IP/Network to yggdrasil interface
    addip(client_ip, "ygg0") # Add gateway_ip to ygg iface

    # ip addr add ${above_network_100.100.0.1/24} dev ygg0

    ## 4. Tell yggdrasil connectng peers IP/Network and PubKey
    # yctl addremotesubnet subnet=${above_network_fetch_100.100.0.10/32} box_pub_key=${above_pubkey_xxxxxx}
    # print('addRoute', ygg_thisbox.addRoute('100.64.0.10/32', 'ygg_thatbox.box_pub_key'))
    # util.addremotesubnet(client_ip + "/32", client_pub_key) # add client ip to ygg running config
    # util.gateway_provision()

@wrap_errors([socket.error, IOError])
def provision():
    'provision the gateway configuration using saved settings'
    util.gateway_provision()


@arg('--foreground', help='run daemon in foreground')
@arg('--killall', help='kill all existing daemons')
@wrap_errors([socket.error, IOError])
def server(foreground=False, killall=False):
    if killall:
        print('...Killed')
        start=subprocess.Popen('kill -9 $(ps w| grep [p]ython3 | grep netdaemon | awk \'{print $1}\') 2>/dev/null', shell=True)
        if foreground:
            pass
        else:
            return

    if foreground:
        start=subprocess.Popen(["/usr/local/bin/netdaemon.py"], shell=True)
        leforge = util.Hemicarp()
        print(leforge.nodeinfo)
        ## blocking
        check = start.communicate()


    else:
        start=subprocess.Popen(["/usr/local/bin/netdaemon.py"], shell=False)
        print("Starting gateway server...")



cmd = [addclient, server]
