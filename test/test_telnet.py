#import unittest
#from unittest.mock import MagicMock, call
# from hpotter.plugins.telnet import TelnetHandler
# from hpotter.plugins.telnet import start_server, stop_server
# from hpotter.env import start_shell, stop_shell

'''
Leaving for the time being to show socket mocking
class TestTelnet(unittest.TestCase):
    def setUp(self):
        start_shell()

    def tearDown(self):
        stop_shell()

    # pylint: disable=R0201
    def test_creds(self):
        tosend = "root\ntoor\nexit\n"
        request = unittest.mock.Mock()
        request.recv.side_effect = [bytes(i, 'utf-8') for i in tosend]

        server = MagicMock()
        server.socket.getsockname.return_value = ('127.0.0.1', 23)
        TelnetHandler(request, ['127.0.0.1', 23], server)

        # print(request.mock_calls)

        request.sendall.assert_has_calls([ \
            call(b'Username: '), \
            call(b'Password: '), \
            call(b'Last login: Mon Nov 20 12:41:05 2017 from 8.8.8.8\n'), \
            call(b'\n$: ')] \
        )

    # pylint: disable=R0201
    def test_no_creds(self):
        tosend = "\n\n\n\n\n\n"
        request = unittest.mock.Mock()
        request.recv.side_effect = [bytes(i, 'utf-8') for i in tosend]

        server = MagicMock()
        server.socket.getsockname.return_value = ('127.0.0.1', 23)
        TelnetHandler(request, ['127.0.0.1', 23], server)

        request.sendall.assert_has_calls([ \
            call(b'Username: '),
            call(b'Username: '),
            call(b'Username: ')])
'''
