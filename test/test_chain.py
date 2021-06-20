import unittest
import iptc
from src.chain import *
from unittest.mock import patch

unittest.TestLoader.sortTestMethodsUsing = None

table = iptc.Table(iptc.Table.FILTER)

class TestChain(unittest.TestCase):
    def setup(self):
        pass
    def tearDown(self):
        pass

    def test01_create_hpotter_chains(self):
        #flush_chains()
        create_hpotter_chains()
        for name in ['hpotter_input','hpotter_output','hpotter_forward']: 
            if iptc.is_table_available(iptc.Table.FILTER):
                self.assertTrue( table.is_chain(name) )
    
    def test_add_drop_rules(self):
        add_drop_rules()
        #check for drop rules in hpotter chains
        for chain in hpotter_chains:
            self.assertTrue(iptc.easy.has_rule('filter', chain.name, { 'target': 'DROP' }))
        
        #check for targets to hpotter chains in builtins
        for chain, rule_d in zip(builtin_chains, hpotter_chain_rules):
            self.assertTrue(iptc.easy.has_rule('filter', chain.name, rule_d))

    def test_create_listen_rules(self):
        thread_mock = unittest.mock.Mock()
        thread_mock.listen_address = '192.168.12.15'
        thread_mock.listen_port = 33000
        thread_mock.container = {'container': 'httpd:latest', 'listen_address': '0.0.0.0','listen_port': '443','request_length': '4096','TLS': 'true','threads': '2'}
        create_listen_rules(thread_mock)
        proto = 'tcp'
        rule_i = { \
            'dst': thread_mock.listen_address, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'dport': str(thread_mock.listen_port)} \
        }
        rule_o = { \
            'src': thread_mock.listen_address, \
            'target': 'ACCEPT', \
            'protocol': proto, \
            proto: {'sport': str(thread_mock.listen_port)} \
        }
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rule_i) )
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule_o) )

    @patch('src.chain.host_ip', '172.16.0.88')
    def test_add_connection_rules(self):
        r1 = { \
            'src':'172.16.0.88', \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'NEW,ESTABLISHED,RELATED'
        }
        r2 = { \
            'src':'127.0.0.1', \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'NEW,ESTABLISHED,RELATED'
        }
        r3 = { \
            'dst':'172.16.0.88', \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'ESTABLISHED,RELATED'
        }
        r4 = { \
            'dst':'127.0.0.1', \
            'target': 'ACCEPT', \
            'match': 'state', \
            'state': 'ESTABLISHED,RELATED'
        }
        add_connection_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', r3))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', r4))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', r1))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', r2))
   
    @patch('src.chain.host_ip', '192.168.0.199')
    @patch('src.chain.configs', {'ssh_port': 22, 'lan_subnet': '192.168.0.0/16', 'docker_subnet': '172.17.0.0/16'})
    def test_add_ssh_rules(self):
        proto = 'tcp'
        port = '22'
        lan = { \
            'src': '192.168.0.0/16', \
            'dst': '192.168.0.199', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
        }
        lcl = { \
            'src':'127.0.0.0/8', \
            'dst':'127.0.0.0/8', \
            'target':'ACCEPT', \
            'protocol': proto, \
            proto :{'dport':port} \
        }
        add_ssh_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', lan))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', lcl))
    
    def test_add_dns_rules(self):
        rule ={ \
            'src': '127.0.0.0/8', \
            'dst': '127.0.0.0/8', \
            'target': 'ACCEPT', \
        }
        resolv1 = { \
            'dst': "1.1.1.1", \
            'target': 'ACCEPT' \
        }
        resolv2 = dns_resolv = { \
            'src': "1.1.1.1", \
            'target': 'ACCEPT' \
        }
        add_dns_rules()
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rule))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_forward', resolv1))
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_forward', resolv2))
    
    def test_create_container_rules(self):
        cont_mock = unittest.mock.Mock()
        cont_mock.container_protocol = 'tcp'
        cont_mock.container_gateway = "71.88.115.9"
        cont_mock.container_ip = "192.188.72.83"
        cont_mock.container_port = 202
        create_container_rules(cont_mock)
        source = cont_mock.container_gateway
        dest = cont_mock.container_ip
        proto = cont_mock.container_protocol
        port = str(cont_mock.container_port)
        rule_t = { \
                'src': source, \
                'dst': dest, \
                'target': 'ACCEPT', \
                'protocol': proto, \
                proto: {'dport': port} \
        }
        rule_f = { \
                'src': dest, \
                'dst': source, \
                'target': 'ACCEPT', \
                'protocol': proto, \
                proto: {'sport': port} \
        }
    
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_output', rule_t) )
        self.assertTrue(iptc.easy.has_rule('filter', 'hpotter_input', rule_f) )

        cont_mock.to_rule = rule_t
        cont_mock.from_rule = rule_f
        delete_container_rules(cont_mock)
        self.assertTrue(not iptc.easy.has_rule('filter', 'hpotter_output', rule_t) )
        self.assertTrue(not iptc.easy.has_rule('filter', 'hpotter_input', rule_f) )

    def test_flush(self):
        flush_chains()
        for chain in builtin_chains:
            rule = {}
            self.assertTrue(not iptc.easy.has_rule('filter', chain.name, rule))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_output'))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_input'))
        self.assertTrue(not iptc.easy.has_chain('filter', 'hpotter_forward'))