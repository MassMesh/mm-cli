import subprocess
import json
import socket
import re
import netaddr


class Hemicarp:
  """
  Admin API accessible with tcp or unix socket
    - admin_endpoint=("127.0.0.2", 3959)
    - admin_endpoint="/pirates/microprovision/remote-ygg.sock"
  """

  def __init__(self, name=None, admin_endpoint='/var/run/yggdrasil.sock'):
    self.name = name
    self.admin_endpoint = admin_endpoint
    self.list = self.yggCaller(json.dumps({"request":"list"}))
    self.nodeinfo = self.yggCaller(json.dumps({"request":"getself"}))['response']['self']
    self.ipv6 = list(self.nodeinfo.keys())[0]
    self.build_version = self.nodeinfo[self.ipv6]['build_version']
    self.box_pub_key = self.nodeinfo[self.ipv6]['box_pub_key']
    self.coords = self.nodeinfo[self.ipv6]['coords']
    self.subnet = self.nodeinfo[self.ipv6]['subnet']
  # /init

  def allowSource(self, subnet):
    return self.yggCaller(json.dumps({"request":"addlocalsubnet", "subnet": subnet}))

  def addRoute(self, subnet, pubkey):
    return self.yggCaller(json.dumps({"request":"addremotesubnet", "subnet": subnet, "box_pub_key": pubkey}))

  def removeRoute(self, subnet, pubkey):
    return self.yggCaller(json.dumps({"request":"removeremotesubnet", "subnet": subnet, "box_pub_key": pubkey}))

  def addPeer(self, uri):
    return self.yggCaller(json.dumps({"request":"addpeer", "uri": uri}))

  def getPeers(self):
    return self.yggCaller(json.dumps({"request":"getpeers"}))['response']['peers']

  def enableTunnel(self):
    return self.yggCaller(json.dumps({"request":"settunnelrouting", "enabled": True}))['response']['enabled']

  def disableTunnel(self):
    return self.yggCaller(json.dumps({"request":"settunnelrouting", "enabled": False}))['response']['enabled']


  def yggCaller(self, pqrs):
    try:
      if (type(self.admin_endpoint) == str):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
      elif (type(self.admin_endpoint) == tuple):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      else:
        print ('unknown yggdrasil endpoint type', type(self.admin_endpoint))
      s.connect(self.admin_endpoint)
      s.send(pqrs.encode('utf-8'))
      f = s.makefile('r')

    except PermissionError as e:
      print('error:: Permission Error AF_UNIX: ' + self.admin_endpoint)
      print('        Try: chown root:$(whoami) ' + self.admin_endpoint)
      exit()


    while True:
      data = f.read();
      if (data == ""):
        break
      else:
        try:
          gatos += data
        except NameError as e:
          gatos = data

    s.close()

    try:
      return json.loads(gatos)
    except:
      return {"status": "error"}
  #<!-- end caller-->


def client_provision():

    ## Execs
        # TODO: pass a verified ready-to-provision struct to this def
    wan_gw = subprocess.run("ubus call network.interface.wan status | jq .route[0].nexthop", shell=True, capture_output=True)
    gateway_pub_key = subprocess.run(["uci", "get", "system.gateway.key"], capture_output=True)
    client_ip       = subprocess.run(["uci", "get", "system.gateway.cl_ip"], capture_output=True) # prefix
    gateway_ip      = subprocess.run(["uci", "get", "system.gateway.gw_ip"], capture_output=True)


    wan_gw = str(wan_gw.stdout.decode("utf-8")).strip("\n").strip('"')
    gateway_pub_key = str(gateway_pub_key.stdout.decode("utf-8")).strip()
    client_ip       = str(client_ip.stdout.decode("utf-8")).strip()
    gateway_ip      = str(gateway_ip.stdout.decode("utf-8")).strip()

    print('----- stephen reports bug here -----')
    print('wan_gw', wan_gw)
    print('gateway_pub_key', gateway_pub_key)
    print('client_ip', client_ip)
    print('gateway_ip', gateway_ip)
    print('----- /stephen reports bug here (dupe wan_gw and gateway_ip) -----')
    # default gw for all peers go on ygg0 dOh

    try:
        assert(netaddr.IPAddress(wan_gw))
        # for ipa in [ "50.236.201.218", "45.76.166.128", "45.77.107.150", "108.175.10.127", "198.58.100.240" ]:
        #     addroute(ipa, wan_gw)
    except:
        # for ipa in [ "50.236.201.218", "45.76.166.128", "45.77.107.150", "108.175.10.127", "198.58.100.240" ]:
        #     addroute(ipa, '127.0.0.1')
        pass


    try:
        assert(bpk_to_ipaddr(gateway_pub_key))
        assert(netaddr.IPNetwork(client_ip))
        assert(netaddr.IPAddress(gateway_ip))
    except Exception as e:
        c = [ wan_gw, gateway_pub_key, client_ip, gateway_ip ]
        print("Error in client_provision(wan_gw, gateway_pub_key, client_ip, gateway_ip)", c, 'err:', str(e))
        return None

    wan_gw     = '%s' % netaddr.IPAddress(wan_gw)
    client_ip  = '%s' % netaddr.IPNetwork(client_ip)
    gateway_ip = '%s' % netaddr.IPAddress(gateway_ip)

    print('wan_gw', wan_gw)
    print('gateway_pub_key', gateway_pub_key)
    print('client_ip', client_ip)
    print('gateway_ip', gateway_ip)

    addip(client_ip, "ygg0") # Add gateway_ip to ygg iface
    addremotesubnet("0.0.0.0/0", gateway_pub_key) # add remote subnet to ygg running config
    addremotesubnet(gateway_ip, gateway_pub_key) # add remote subnet to ygg running config

    # fixme: get this list dynamically from yggdrasil config (?)
    # for ipa in [ "50.236.201.218", "45.76.166.128", "45.77.107.150", "108.175.10.127", "198.58.100.240" ]:
        # addroute(ipa, wan_gw)

    setdefaultroute(gateway_ip) # set default route to gateway_ip


def bpk_to_ipaddr(box_pub_key=False):
    try:
        assert(box_pub_key)
        assert(re.match('(^[a-z0-9]{64}$)', box_pub_key)[0])

        bpk_lookup = subprocess.check_output([ 'yggdrasil', "-address", "-useconf"],
                        input=bytes(json.dumps({'EncryptionPublicKey': box_pub_key}), 'utf-8'))
        bpk_lookup = bpk_lookup.decode('utf-8').replace("\n", "")
        assert(netaddr.IPAddress(bpk_lookup))

        return bpk_lookup
    except:
        return None

def gateway_provision(**kwargs):
    print("fixme: gateway_provision")

    # config rule
    #   option dest_port '1617'
    #   option src '*'
    #   option name 'Network Daemon'
    #   option family 'ipv6'
    #   option target 'ACCEPT'
    #   option proto 'tcp'
    #   util.addip() # add gateway ip to ygg interface if not already set


    c = list(kwargs)
    print('gateway_provision(**kwargs)', c)

def addroute(dest, gateway, iface=None):
    assert(netaddr.IPNetwork(dest))
    assert(netaddr.IPNetwork(gateway))
    dest    = '%s' % netaddr.IPNetwork(dest).ip
    gateway = '%s' % netaddr.IPNetwork(gateway).ip

    c = ["ip", "route", "replace", dest, "via", gateway]
    print('addroute()', c)
    subprocess.run(c, shell=False, capture_output=True)


def setdefaultroute(gateway):
    assert(netaddr.IPNetwork(gateway))
    gateway = '%s' % netaddr.IPNetwork(gateway).ip

    c = ["ip", "route", "replace", "default", "via", gateway]
    print('setdefaultroute()', c)
    subprocess.run(c, shell=False, capture_output=False)


def deleteprefix(pfx, iface):
    assert(netaddr.IPNetwork(pfx))
    pfx = '%s' % netaddr.IPNetwork(pfx).ip

    c = ["ip", "address", "delete", pfx, "dev", iface]
    print('deleteprefix()', c)
    subprocess.run(c, shell=False, capture_output=True)


def addprefix(pfx, iface):
    assert(netaddr.IPNetwork(pfx))
    pfx = '%s' % netaddr.IPNetwork(pfx).ip

    c = ["ip", "address", "add", pfx, "dev", iface]
    print('addprefix()', c)
    subprocess.run(c, shell=False, capture_output=False)

def deleteip(ip, iface):
    assert(netaddr.IPNetwork(ip))
    ip = '%s' % netaddr.IPNetwork(ip)

    c = ["ip", "address", "delete", ip, "dev", iface]
    print('deleteip()', c)
    subprocess.run(c, shell=False, capture_output=False)


def addip(ip, iface):
    assert(netaddr.IPNetwork(ip))
    ip = '%s' % netaddr.IPNetwork(ip)
    deleteip(ip, iface)

    c = ["ip", "address", "add", ip, "dev", iface]
    print('addip()', c)
    subprocess.run(c, shell=False, capture_output=False)


def remremotesubnet(subnet, pubkey):
    assert(netaddr.IPNetwork(subnet))
    assert(bpk_to_ipaddr(pubkey))
    subnet = '%s' % netaddr.IPNetwork(subnet)

    c = Hemicarp().removeRoute(subnet, pubkey)
    print('remremotesubnet()', c)


def addremotesubnet(subnet, pubkey):
    assert(netaddr.IPNetwork(subnet))
    assert(bpk_to_ipaddr(pubkey))
    subnet = '%s' % netaddr.IPNetwork(subnet)
    remremotesubnet(subnet, pubkey)

    c = Hemicarp().addRoute(subnet, pubkey)
    print('addremotesubnet()', c)


