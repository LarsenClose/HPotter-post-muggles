from socket import timeout
import unittest
from unittest.mock import call, patch
from src import database
from src.container_thread import ContainerThread

class TestContainer(unittest.TestCase):
    
    @patch('logging.Logger.debug')
    def test_run(self,mock):
        cont = unittest.mock.Mock()
        cont.source = unittest.mock.Mock()
        cont.source.recv.side_effect=[bytes(i,'utf-8') for i in 'a']
        cont.dest = unittest.mock.Mock()
        cont.dest.recv.side_effect=[bytes(i,'utf-8') for i in 'b']
        cont.connection = unittest.mock.Mock()
        cont.container_config = {}
        cont.database = unittest.mock.Mock()

        ContainerThread._start_and_join_threads(cont)
        mock.assert_any_call('Joining thread2')

    def test_init(self):
        source = unittest.mock.Mock()
        source.recv.side_effect=[bytes(i,'utf-8') for i in 'a']
        connection = unittest.mock.Mock()
        database = unittest.mock.Mock()

        ct = ContainerThread(source, connection, {}, database)
        self.assertEqual(ct.container_ip, None)
        self.assertEqual(ct.container_port, None)
        self.assertEqual(ct.container_protocol, None)
        self.assertEqual(ct.dest, None)
        self.assertEqual(ct.thread1, None)
        self.assertEqual(ct.thread2, None)
        self.assertEqual(ct.container, None)

    @patch('logging.Logger.info')
    def test_connect_to_container(self,mock):
        cont = unittest.mock.Mock()
        cont.container.attrs = {'Id': '659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0', 'Created': '2021-03-09T21:52:11.808199279Z', 'Path': 'httpd-foreground', 'Args': [], 'State': {'Status': 'running', 'Running': True, 'Paused': False, 'Restarting': False, 'OOMKilled': False, 'Dead': False, 'Pid': 9870, 'ExitCode': 0, 'Error': '', 'StartedAt': '2021-03-09T21:52:14.613773236Z', 'FinishedAt': '0001-01-01T00:00:00Z'}, 'Image': 'sha256:464fdc577ef4d4ba06050b76a95ffee72d280f7aaa4291f7f4827fca7a00ed0f', 'ResolvConfPath': '/var/lib/docker/containers/659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0/resolv.conf', 'HostnamePath': '/var/lib/docker/containers/659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0/hostname', 'HostsPath': '/var/lib/docker/containers/659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0/hosts', 'LogPath': '/var/lib/docker/containers/659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0/659dad3ca3ac6d5c387a0963caacaf0a6b3caec6b20890394a2b2ecb59a638d0-json.log', 'Name': '/compassionate_blackwell', 'RestartCount': 0, 'Driver': 'btrfs', 'Platform': 'linux', 'MountLabel': '', 'ProcessLabel': '', 'AppArmorProfile': '', 'ExecIDs': None, 'HostConfig': {'Binds': None, 'ContainerIDFile': '', 'LogConfig': {'Type': 'json-file', 'Config': {}}, 'NetworkMode': 'default', 'PortBindings': None, 'RestartPolicy': {'Name': '', 'MaximumRetryCount': 0}, 'AutoRemove': False, 'VolumeDriver': '', 'VolumesFrom': None, 'CapAdd': None, 'CapDrop': None, 'CgroupnsMode': 'host', 'Dns': ['1.1.1.1'], 'DnsOptions': None, 'DnsSearch': None, 'ExtraHosts': None, 'GroupAdd': None, 'IpcMode': 'private', 'Cgroup': '', 'Links': None, 'OomScoreAdj': 0, 'PidMode': '', 'Privileged': False, 'PublishAllPorts': False, 'ReadonlyRootfs': False, 'SecurityOpt': None, 'UTSMode': '', 'UsernsMode': '', 'ShmSize': 67108864, 'Runtime': 'runc', 'ConsoleSize': [0, 0], 'Isolation': '', 'CpuShares': 0, 'Memory': 0, 'NanoCpus': 0, 'CgroupParent': '', 'BlkioWeight': 0, 'BlkioWeightDevice': None, 'BlkioDeviceReadBps': None, 'BlkioDeviceWriteBps': None, 'BlkioDeviceReadIOps': None, 'BlkioDeviceWriteIOps': None, 'CpuPeriod': 0, 'CpuQuota': 0, 'CpuRealtimePeriod': 0, 'CpuRealtimeRuntime': 0, 'CpusetCpus': '', 'CpusetMems': '', 'Devices': None, 'DeviceCgroupRules': None, 'DeviceRequests': None, 'KernelMemory': 0, 'KernelMemoryTCP': 0, 'MemoryReservation': 0, 'MemorySwap': 0, 'MemorySwappiness': None, 'OomKillDisable': False, 'PidsLimit': None, 'Ulimits': None, 'CpuCount': 0, 'CpuPercent': 0, 'IOMaximumIOps': 0, 'IOMaximumBandwidth': 0, 'MaskedPaths': ['/proc/asound', '/proc/acpi', '/proc/kcore', '/proc/keys', '/proc/latency_stats', '/proc/timer_list', '/proc/timer_stats', '/proc/sched_debug', '/proc/scsi', '/sys/firmware'], 'ReadonlyPaths': ['/proc/bus', '/proc/fs', '/proc/irq', '/proc/sys', '/proc/sysrq-trigger']}, 'GraphDriver': {'Data': None, 'Name': 'btrfs'}, 'Mounts': [], 'Config': {'Hostname': '659dad3ca3ac', 'Domainname': '', 'User': '', 'AttachStdin': False, 'AttachStdout': False, 'AttachStderr': False, 'ExposedPorts': {'80/tcp': {}}, 'Tty': False, 'OpenStdin': False, 'StdinOnce': False, 'Env': ['PATH=/usr/local/apache2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'HTTPD_PREFIX=/usr/local/apache2', 'HTTPD_VERSION=2.4.46', 'HTTPD_SHA256=740eddf6e1c641992b22359cabc66e6325868c3c5e2e3f98faf349b61ecf41ea', 'HTTPD_PATCHES='], 'Cmd': ['httpd-foreground'], 'Image': 'httpd:latest', 'Volumes': None, 'WorkingDir': '/usr/local/apache2', 'Entrypoint': None, 'OnBuild': None, 'Labels': {}, 'StopSignal': 'SIGWINCH'}, 'NetworkSettings': {'Bridge': '', 'SandboxID': '34f53ee70c8946c9e1a88accdd5cf00acdac349a5f6791e5da8ac9064ea4344e', 'HairpinMode': False, 'LinkLocalIPv6Address': '', 'LinkLocalIPv6PrefixLen': 0, 'Ports': {'80/tcp': None}, 'SandboxKey': '/var/run/docker/netns/34f53ee70c89', 'SecondaryIPAddresses': None, 'SecondaryIPv6Addresses': None, 'EndpointID': '52bffbdfa60946c000fbde5388cc6eaa007d4c75ec1df88ed0a6a9a329664338', 'Gateway': '172.17.0.1', 'GlobalIPv6Address': '', 'GlobalIPv6PrefixLen': 0, 'IPAddress': '172.17.0.2', 'IPPrefixLen': 16, 'IPv6Gateway': '', 'MacAddress': '02:42:ac:11:00:02', 'Networks': {'bridge': {'IPAMConfig': None, 'Links': None, 'Aliases': None, 'NetworkID': '547e1044475b92ecc0d9205c2b4734d4c07d0b6b88bf804f44d27c8a12265001', 'EndpointID': '52bffbdfa60946c000fbde5388cc6eaa007d4c75ec1df88ed0a6a9a329664338', 'Gateway': '172.17.0.1', 'IPAddress': '172.17.0.2', 'IPPrefixLen': 16, 'IPv6Gateway': '', 'GlobalIPv6Address': '', 'GlobalIPv6PrefixLen': 0, 'MacAddress': '02:42:ac:11:00:02', 'DriverOpts': None}}}}
        ContainerThread._connect_to_container(cont)
        mock.assert_called_with('Unable to connect to 172.17.0.2:80')