from argh import arg, wrap_errors
import socket
import json
import urllib.parse
import urllib.request

from . import util
import subprocess

@arg('gateway_pub_key', help='public key of the gateway')
@arg('client_ip', help='client tunnel ip')
@arg('gateway_ip', help='gateway tunnel ip')
@wrap_errors([socket.error, IOError])
def setgateway(gateway_pub_key, client_ip, gateway_ip):
    'initiate the gateway configuration'
    print('Gateway Mesh IP:\t', util.bpk_to_ipaddr(gateway_pub_key))
    print('Gateway Public Key:\t', gateway_pub_key)
    print('Your Network:\t\t', client_ip)
    print('Default Gateway IP:\t', gateway_ip, '\n')
    subprocess.run(["uci", "set", "system.gateway=gateway"])
    subprocess.run(["uci", "set", "system.gateway.key="   + gateway_pub_key])
    subprocess.run(["uci", "set", "system.gateway.cl_ip=" + client_ip])
    subprocess.run(["uci", "set", "system.gateway.gw_ip=" + gateway_ip])
    subprocess.run(["uci", "commit"])


@wrap_errors([socket.error, IOError])
def provision():
    'provision the client configuration using saved settings'
    util.client_provision()


@arg('gateway_pub_key', help='public key of the gateway')
@wrap_errors([socket.error, IOError])
def info():
    'fetch server information from given gateway public key'
    ()

####################################################################
# rpi3
# 201:1dc6:90e4:1c1a:bba4:b5ba:82:1948
# 6ac222cd81ef3446832b9aef2b0d2c8920ded440f68495a43544ecee99ad4045
#
# rpi4
# 200:9687:30ef:13d:57b1:f7a7:b69f:72c4
# 170b3b5642771016a9feecbece89283466c69d230c863812c4208d6af255b479
####################################################################



@arg('gateway_pub_key', help='public key of the gateway')
@wrap_errors([socket.error, IOError])
def renew(gateway_pub_key):
    'renew the lease with gateway'

    ## getSelf: box_pub_key
    self_box_pub_key = util.Hemicarp().box_pub_key

    ## Test against x1n
    # mm cl renew cb29621f501e9de68aca856c1e90dba58406aa9f4918f845bc12c1c6756e1453
    ## Test against selfdaemon
    # mm cl renew 170b3b5642771016a9feecbece89283466c69d230c863812c4208d6af255b479

    ## Gateway: via input: box_pub_key
    gateway_addr = util.bpk_to_ipaddr(gateway_pub_key)

    if gateway_addr:
        url_base = 'http://[' + gateway_addr + ']:1617'
        print('\nGateway Endpoint:\t', url_base)
    else:
        print('Error: Invalid Gateway Public Key:', gateway_pub_key)
        return

    ## Recreate Database
    url = url_base + '/wip_make_pool_database'
    urllib.request.urlopen(url)

    ## /register: get a new network
    url  = url_base + '/wip_make_register'
    data = urllib.parse.urlencode({'box_pub_key': self_box_pub_key.replace("\\n", "")})
    data = data.encode('utf-8')

    with urllib.request.urlopen(url, data) as f:
        res = json.loads(f.read().decode('utf-8'))

    gateway = res['gateway']
    citizen = res['citizen'] + '/' + res['pfxlen']

    ## /renew: set a new network
    #   'network_long': '1684276225',
    #   'network_cidr': '100.100.4.0/24',
    #   'public_enckey': '170b3b5642771016a9feecbece89283466c69d230c863812c4208d6af255b479',
    #   'status_blob': 'None',
    #   'ident_blob': "{'cloud': 'cloud-s51cleh9', 'remote_addr': '200:9687:30ef:13d:57b1:f7a7:b69f:72c4'}"

    setgateway(gateway_pub_key, client_ip=citizen, gateway_ip=gateway)
    util.client_provision()

    print('Renew: EOF')
    # util.client_provision()


cmd = [setgateway, provision, renew]
