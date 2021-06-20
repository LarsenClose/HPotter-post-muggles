from logging import error
import iptc
import socket
import threading
import ipaddress

from src.logger import logger

# here's the idea. create hpotter chains that mirror the three builtins. add
# drop rules at the end of the hpotter chains. insert a target of each of
# the hpotter chains at the beginning of the builtin chains. this
# overwrites whatever was there. make the process reversable so that we can
# put it back the way it was.

# can only set policies in builtin chains

def create_listen_rules(obj):
    thread_lock.acquire()

    listen_address = obj.listen_address
    if len(listen_address) == 0 or listen_address == '0.0.0.0':
        listen_address = '0.0.0.0/0'

    proto = "tcp"
    if 'UDP' in obj.container:
        proto = "udp"

    obj.to_rule = { \
        'dst': listen_address, \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'dport': str(obj.listen_port)} \
    }
    logger.debug(obj.to_rule)
    iptc.easy.insert_rule('filter', 'hpotter_input', obj.to_rule)

    obj.from_rule = { \
        'src': listen_address, \
        'target': 'ACCEPT', \
        'protocol': proto, \
        proto: {'sport': str(obj.listen_port)} \
    }
    logger.debug(obj.from_rule)
    iptc.easy.insert_rule('filter', 'hpotter_output', obj.from_rule)

    thread_lock.release()

def create_hpotter_chains():
    for name in hpotter_chain_names:
        hpotter_chain = iptc.Chain(filter_table, name)

        if not iptc.easy.has_chain('filter', name):
            hpotter_chain = filter_table.create_chain(name)

        if not hpotter_chain in hpotter_chains:
            hpotter_chains.append(hpotter_chain)

    # create target for all hpotter chains
    for chain in hpotter_chains:
        rule_d = { 'target' : chain.name }
        if not rule_d in hpotter_chain_rules:
            hpotter_chain_rules.append( rule_d )

    # make the hpotter chains the target for all builtin chains
    for rule_d, chain in zip(hpotter_chain_rules, builtin_chains):
        if not iptc.easy.has_rule('filter', chain.name, rule_d):
            iptc.easy.insert_rule('filter', chain.name, rule_d)

def flush_chains():
    for chain, name in zip(builtin_chains, hpotter_chain_names):
        if iptc.easy.has_chain('filter', name):

            #delete hpotter rules in builtins if they exist
            if iptc.easy.has_rule('filter', chain.name, {'target':name}):
                iptc.easy.delete_rule('filter', chain.name, {'target':name})

            #delete hpotter chains if they exist
            iptc.easy.flush_chain('filter', name)
            iptc.easy.delete_chain('filter', name)

def add_drop_rules():
    drop_rule = { 'target': 'DROP' }
    
    # append drop to all hpotter chains
    for chain in hpotter_chains:
        if not iptc.easy.has_rule('filter', chain.name, drop_rule):
            iptc.easy.add_rule('filter', chain.name, drop_rule)

def add_connection_rules():
    connection_rule = { \
        'src': host_ip, \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'NEW,ESTABLISHED,RELATED'
    }
    iptc.easy.insert_rule('filter', 'hpotter_output', connection_rule)

    connection_rule = { \
        'src': '127.0.0.1', \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'NEW,ESTABLISHED,RELATED'
    }
    iptc.easy.insert_rule('filter', 'hpotter_output', connection_rule)

    connection_rule = { \
        'dst': host_ip, \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'ESTABLISHED,RELATED'
    }
    iptc.easy.insert_rule('filter', 'hpotter_input', connection_rule)

    connection_rule = { \
        'dst': '127.0.0.1', \
        'target': 'ACCEPT', \
        'match': 'state', \
        'state': 'ESTABLISHED,RELATED'
    }
    iptc.easy.insert_rule('filter', 'hpotter_input', connection_rule)

def add_dns_rules():
    dns_rule = { \
        'src': '127.0.0.0/8', \
        'dst': '127.0.0.0/8', \
        'target': 'ACCEPT', \
    }
    iptc.easy.insert_rule('filter', 'hpotter_input', dns_rule)
    iptc.easy.insert_rule('filter', 'hpotter_output', dns_rule)

    dns_resolv = { \
        'dst': "1.1.1.1", \
        'target': 'ACCEPT' \
    }
    iptc.easy.insert_rule('filter', 'hpotter_forward', dns_resolv)

    dns_resolv = { \
        'src': "1.1.1.1", \
        'target': 'ACCEPT' \
    }
    iptc.easy.insert_rule('filter', 'hpotter_forward', dns_resolv)

def add_ssh_rules(): #allow LAN/LocalHost IPs, reject all others
    proto = 'tcp'
    port = str(configs.get('ssh_port'))
    subnet = configs.get('lan_subnet', '')

    # then allow ssh connection from private ip's
    lan_d = { \
        'src': subnet, \
        'dst': host_ip, \
        'target':'ACCEPT', \
        'protocol': proto, \
        proto :{'dport':port} \
    }
    logger.debug(lan_d)
    iptc.easy.insert_rule('filter', 'hpotter_input', lan_d)

    # then allow ssh connections from loopback 
    local_d = { \
        'src':'127.0.0.0/8', \
        'dst':'127.0.0.0/8', \
        'target':'ACCEPT', \
        'protocol': proto, \
        proto :{'dport':port} \
    }
    logger.debug(local_d)
    iptc.easy.insert_rule('filter', 'hpotter_input', local_d)

def create_container_rules(obj):
    thread_lock.acquire()
    proto = obj.container_protocol.lower()
    source_addr = obj.container_gateway
    dest_addr = obj.container_ip
    dstport = str(obj.container_port)
    obj.to_rule = { \
            'src': source_addr, \
            'dst': dest_addr, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'dport': dstport} \
    }
    logger.debug(obj.to_rule)
    try:
        iptc.easy.insert_rule('filter', 'hpotter_output', obj.to_rule)
    except Exception as err:
        logger.debug(error)
        pass
    
    obj.from_rule = { \
            'src': dest_addr, \
            'dst': source_addr, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'sport': dstport} \
    }
    logger.debug(obj.from_rule)
    try:
        iptc.easy.insert_rule('filter', 'hpotter_input', obj.from_rule)
    except Exception as err:
        logger.debug(err)
        pass
    thread_lock.release()

def delete_container_rules(obj):
    thread_lock.acquire()

    logger.debug('Removing rules')

    iptc.easy.delete_rule('filter', "hpotter_output", obj.to_rule)
    iptc.easy.delete_rule('filter', "hpotter_input", obj.from_rule)

    thread_lock.release()

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('1.1.1.1', 0))
        ip = s.getsockname()[0]
    except Exception: # pragma: no cover
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

configs = {}

host_ip = get_host_ip()

filter_table = iptc.Table(iptc.Table.FILTER)

input_chain = iptc.Chain(filter_table, 'INPUT')
output_chain = iptc.Chain(filter_table, 'OUTPUT')
forward_chain = iptc.Chain(filter_table, 'FORWARD')
builtin_chains = [input_chain, output_chain, forward_chain]

hpotter_chains = []
hpotter_chain_names = ['hpotter_input', 'hpotter_output', 'hpotter_forward']
    
hpotter_chain_rules = []

thread_lock = threading.Lock()
