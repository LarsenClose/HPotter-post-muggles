# bindd:latest
Public facing containerized DNS server.
### Build container
    docker build -t bindd .
### Run container
    sudo docker run --name=bind9 \
    --restart=always \
    --publish 53:53/udp \
    --publish 127.0.0.1:953:953/tcp \
    bindd

### Testing the server (from a different CLI)
    nslookup www.example.com 127.0.0.1

Result should look something like this: 

    pi@Yamu4:~ $ nslookup www.example.com 127.0.0.1
    Server:         127.0.0.1
    Address:        127.0.0.1#53
    Non-authoritative answer:
    Name:   www.example.com
    Address: 93.184.216.34
    Name:   www.example.com
    Address: 2606:2800:220:1:248:1893:25c8:1946

### Attributions:
* https://gitlab.isc.org/isc-projects/bind9-docker/-/blob/master/bind/Dockerfile
* http://books.gigatux.nl/mirror/linuxcookbook/0596006403/linuxckbk-CHP-24-SECT-18.html
