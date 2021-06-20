FROM debian:latest
EXPOSE 23

RUN apt update && apt -y install inetutils-telnetd libpam-script sudo

COPY ./pam_script_auth /usr/share/libpam-script/

RUN chmod +x /usr/share/libpam-script/pam_script_auth
RUN echo 'telnet stream tcp nowait root /usr/sbin/tcpd     /usr/sbin/telnetd' >> /etc/inetd.conf

RUN sed "s/default=die/default=ignore/g" -i /etc/pam.d/*
RUN sed "s/default=bad/default=ignore/g" -i /etc/pam.d/*
RUN sed "s/close/open/g" -i /etc/pam.d/*
RUN sed "s/nullok_secure//g" -i /etc/pam.d/*
RUN sed "s/force//g" -i /etc/pam.d/*
RUN sed "s/revoke//g" -i /etc/pam.d/*
RUN sed "s/use_authtok//g" -i /etc/pam.d/*
RUN sed "s/try_first_pass//g" -i /etc/pam.d/*
RUN sed "s/obscure//g" -i /etc/pam.d/*
RUN sed "s/sha512//g" -i /etc/pam.d/*
RUN sed "s/\bpam_.*\.so\b/pam_permit.so/g" -i /etc/pam.d/*
RUN sed "s/requisite/optional/g" -i /etc/pam.d/*
RUN sed "s/required/optional/g" -i /etc/pam.d/*
RUN sed "s/sufficient/optional/g" -i /etc/pam.d/*
RUN sed   "$ a auth optional pam_script.so /dir/usr/share/libpam-script/\nauth sufficient pam_permit.so" -i  /etc/pam.d/*

RUN echo 'pts/0:pts/1' >> /etc/securetty

CMD [ "/usr/sbin/inetutils-inetd", "-d"]
