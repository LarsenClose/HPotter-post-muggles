# Dynamic Firewall Rules
HPotter features dynamic firewall rules which are created
once the application is launched. These rules block traffic coming from
Docker containers created by HPotter to the host, as well as any requests 
the host does not initiate, in order to keep the host machine secure.
These rules are removed from the system once the application is closed.

### firewall.yml
* ssh\_port, default: 22
* lan\_subnet, default: 192.168.0.0/16
* docker\_subnet, default: 172.17.0.0/16

## Docker network subnet
Docker containers use the subnet 172.17.0.0/16 by default.
If your home network is already using this subnet, you must change the
default Docker subnet in order for the firewall to function properly.

## iptables vs nftables
Newer linux distributions are adopting nftables as the primary firewall manager.
HPotter uses uses python-iptables which in turn uses iptables 
(denoted as iptables-legacy in distributions which use nftables).
There are no known conflicts with rules created by HPotter. 

To view these rules when HPotter is running, use the command:
```
iptables -L # On distributions which do not use nftables
iptables-legacy -L # On distributions which use both
```

### Remote access setup
The dynamic firewall rules require some initial setup on your host machine.

* Remote SSH connection: 
    The firewall rules block all incoming connections by default.
    In order to enable ssh connections to the host machine you must first specify
    a port number and a LAN subnet.

    By default, port 22 is opened for local network connections. If you intend to run
    an ssh Docker image on HPotter, you must change this port in the configuration file.

    If you want to access your machine with a remote ssh connection; you must also
    change the port number located in /etc/ssh/sshd_config on your system:
    ```
    <nano/vim/etc> /etc/ssh/sshd_config # May require root permissions
    ```
    In the file, locate the line:
    ```
    Port 22
    ```
    and change it to the number you specified in chain.py.
    
    Then, restart the ssh daemon with:
    ```
    sudo systemctl restart sshd
    ```

    Now, when you want to connect to the device:
    ```
    ssh user@ip_address -p <port number>
    ```