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

  def getRoutes(self):
    return self.yggCaller(json.dumps({"request":"getroutes"}))

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


def get_wan_state_check(ip):
    print('*D*', 'get_wan_state_check(' + str(ip) + ')')
    try:
        assert(netaddr.IPNetwork(ip))
        return '%s' % netaddr.IPNetwork(ip)
    except Exception as e:
        print('*E*', 'error in get_wan_state_check(' + str(ip) + ')', str(e))
        return False
def clean_string(s):
    try:
        if type(s) == subprocess.CompletedProcess:
            return str(s.stdout.decode("utf-8")).strip("\n").strip('"').strip()
        elif type(s) == str:
            return s.strip("\n").strip('"').strip()
    except Exception as e:
        print('error clean_string()', str(e))

def get_cfg_peers():
    # fixme: get this list dynamically from yggdrasil config (?)
    return [
        "108.175.10.127", "45.76.166.128", "198.58.100.240",
        "45.77.107.150",  "50.236.201.218",
    ]

def client_provision():

    try:

        ## Execs
        wan_gw_ip = clean_string(subprocess.run("ubus call network.interface.wan status | jq .route[0].nexthop", shell=True, capture_output=True))
        # validity through: get_wan_state_check(wan_gw_ip)
        primary_wan_up = get_wan_state_check(wan_gw_ip)
        print('*D*', 'primary_wan_up', bool(primary_wan_up))

        client_ip  = clean_string(subprocess.run(["uci", "get", "system.gateway.cl_ip"], capture_output=True)) # prefix
        assert(netaddr.IPNetwork(client_ip))
        addip(client_ip, "ygg0") # Add client_ip to ygg0 iface

        gateway_ip = clean_string(subprocess.run(["uci", "get", "system.gateway.gw_ip"], capture_output=True))
        assert(netaddr.IPAddress(gateway_ip))

        gateway_pub_key = clean_string(subprocess.run(["uci", "get", "system.gateway.key"], capture_output=True))
        assert(bpk_to_ipaddr(gateway_pub_key))

    except Exception as e:
        print("Error in client_provision()", str(e))
        return False

    ## Routes
    # Direct-Peers
    for peer_ip in get_cfg_peers():
        addroute(peer_ip, wan_gw_ip)

    # CKR: allow any traffic 0/0 into CKR via gw-pub-key
    addremotesubnet("0.0.0.0/0", gateway_pub_key)

    # CKR: allow specific (/32) MeshWan Gateway IP to CKR
    addremotesubnet(gateway_ip, gateway_pub_key)

    # Routing: Set the default route
    setdefaultroute(gateway_ip)


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
    # util.addip() # add gateway ip to ygg interface if not already set
    c = list(kwargs)
    print('gateway_provision(**kwargs)', c)

def addroute(dest, gateway, iface=None):
    try:
        assert(netaddr.IPNetwork(dest))

        if gateway == 'null':
            if dest == "0.0.0.0/0":
                # default via 10.42.0.1 dev ygg0  metric 500
                mesh_gw_ip = clean_string(subprocess.run(["uci", "get", "system.gateway.gw_ip"], capture_output=True))
                print('*D*', 'primary wan: down, but added indirect defgw via mesh', mesh_gw_ip)
                c = [ "ip", "route", "replace", dest, "via", mesh_gw_ip, "dev", "ygg0", "metric", "500" ]
                p = subprocess.run(c, shell=False, capture_output=True)
                assert(bool(p.returncode == 0))
                return(bool(p.returncode == 0))
            else:
                # no gateway: null route to prevent direct-peering over CKR
                print('*D*', 'adding null route', dest)
                c = [ "ip", "route", "replace", "blackhole", dest, "metric", "500" ]

                p = subprocess.run(c, shell=False, capture_output=True)
                assert(bool(p.returncode == 0))
                return(bool(p.returncode == 0))
        else:
            if dest == "0.0.0.0/0":
                # not (yet) hit, using setdefaultroute()
                pass
            else:
                assert(netaddr.IPNetwork(gateway))
                print('*D*', 'primary wan: up, adding direct route', dest, 'via', gateway)
                c = [ "ip", "route", "replace", dest, "via", gateway ]
                p = subprocess.run(c, shell=False, capture_output=True)
                assert(bool(p.returncode == 0))
                return(bool(p.returncode == 0))
    except Exception as e:
        print('*E*', 'error in addroute()', str(e))
        return False

def setdefaultroute(gateway):
    try:
        assert(netaddr.IPNetwork(gateway))
        gateway = '%s' % netaddr.IPNetwork(gateway).ip

        c = [ "ip", "route", "replace", "default", "via", gateway ]
        print('*D*', 'setdefaultroute()', c)
        subprocess.run(c, shell=False, capture_output=False)

        mesh_gw_ip = clean_string(subprocess.run(["uci", "get", "system.gateway.gw_ip"], capture_output=True))
        print('*D*', 'backup wan: adding secondary default gateway via mesh', mesh_gw_ip)

        c = [ "ip", "route", "replace", "default", "via", mesh_gw_ip, "dev", "ygg0", "metric", "500" ]
        p = subprocess.run(c, shell=False, capture_output=True)

    except Exception as e:
        print('*D*', 'error in setdefaultroute(' + str(gateway) + ')', str(e))
        return False


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

    try:
        assert(netaddr.IPNetwork(ip))
        ip = '%s' % netaddr.IPNetwork(ip)

        c1 = [ "ip", "-o", "address", "show", "dev", "ygg0" ]
        p1 = subprocess.Popen(c1, stdout=subprocess.PIPE)
        c2 = [ "egrep", '-o', ".+:.+ygg0.+inet.+" + ip ]
        p2 = subprocess.Popen(c2, stdin=p1.stdout, stdout=subprocess.PIPE)

        p1.stdout.close()
        p2.communicate()[0]
        ygg_has_meshwan_ip=bool(p2.returncode == 0)

        if ygg_has_meshwan_ip:
            return True
        else:
            c = ["ip", "address", "add", ip, "dev", iface]
            print('addip()', c)
            cp = subprocess.run(c, shell=False, capture_output=False)
            ygg_has_meshwan_ip=bool(cp.returncode == 0)
            if ygg_has_meshwan_ip:
                return True
            else:
                raise Exception('Failed to add ip to ygg0')
                return False

    except Exception as e:
        print('Error in addip()', str(e))
        return False

def remremotesubnet(subnet, pubkey):
    assert(netaddr.IPNetwork(subnet))
    assert(bpk_to_ipaddr(pubkey))
    subnet = '%s' % netaddr.IPNetwork(subnet)
    c = Hemicarp().removeRoute(subnet, pubkey)


def addremotesubnet(subnet, pubkey):
    try:
        assert(netaddr.IPNetwork(subnet))
        assert(bpk_to_ipaddr(pubkey))

        subnet = '%s' % netaddr.IPNetwork(subnet)
        c = Hemicarp().getRoutes()['response']['routes']

        if subnet in c.keys():
            print('*D*', 'subnet already routed', subnet)
            if c[subnet] == pubkey:
                print('*D*', 'subnet already routed by same subnet', c[subnet])
            else:
                print('*D*', 'replacing subnet routed by pubkey', c[subnet], 'via', pubkey)
                remremotesubnet(subnet, c[subnet]) # routes["0.0.0.0/0"]: 56ebd7c92...
                c = Hemicarp().addRoute(subnet, pubkey)
        else:
            c = Hemicarp().addRoute(subnet, pubkey)
    except Exception as e:
        print('Error in addremotesubnet()', str(e))
        return False

