FROM debian:latest
EXPOSE 22

RUN apt update && apt -y install openssh-server && mkdir /var/run/sshd
RUN apt install sudo

COPY ./setpasswd /setpasswd
RUN chmod 744 /setpasswd

RUN service ssh restart
RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN service ssh restart

CMD ["/usr/sbin/sshd","-D"]