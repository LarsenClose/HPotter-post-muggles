FROM debian:latest

#EXPOSE 53
EXPOSE 53/udp

RUN apt-get update && apt-get install -y --no-install-recommends --no-install-suggests bind9 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /var/run/named /etc/bind/zones
RUN chmod 775 /var/run/named
RUN chown root:bind /var/run/named

COPY /etc_bind/* /etc/bind/
COPY /var_named/* /var/named/
RUN sed 's/OPTIONS=.*/OPTIONS="-4 -u bind"/' -i /etc/default/bind9
VOLUME ['var/cache/bind', '/etc/bind', '/var/lib/bind', '/var/log', '/var/run/named']


CMD ["/usr/sbin/named", "-g", "-c", "/etc/bind/named.conf", "-u", "bind"]