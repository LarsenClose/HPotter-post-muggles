FROM debian:latest
EXPOSE 22

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update && apt-get -y install ssh inetutils-inetd libpam-script sudo 
#RUN service ssh restart

COPY ./pam_script_auth ./pam_script_ses_open ./pam_script_acct   /usr/share/libpam-script/

COPY ./ssh /etc/inetd.d/
RUN chmod +x /usr/share/libpam-script/*

RUN echo 'ssh    stream  tcp nowait  root /usr/sbin/sshd sshd -i' >> /etc/inetd.conf

#RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
#RUN echo 'PermitEmptyPasswords yes' >> /etc/ssh/sshd_config
#RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
#RUN echo 'ChallengeResponseAuthentication no' >> /etc/ssh/sshd_config
RUN echo "export LANGUAGE=en_US.UTF-8"  >> /etc/default/locale
RUN echo "export LC_ALL=en_US.UTF-8" >> /etc/default/locale
RUN echo "export LANGUAGE=en_US.UTF-8" >> /etc/environment
RUN echo "export LC_ALL=en_US.UTF-8" >> //etc/environment
#RUN echo 'PubkeyAuthentication  yes' >> /etc/ssh/sshd_config
#RUN service ssh restart

RUN sed "s/user_unknown=bad/user_unknown=ignore/g" -i /etc/pam.d/*
RUN sed "s/new_authtok_reqd=done/new_authtok_reqd=ignore/g" -i /etc/pam.d/*
RUN sed "s/new_authtok_reqd=ok/new_authtok_reqd=ignore/g" -i /etc/pam.d/*
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
RUN sed "s/required/optional/g" -i /etc/pam.d/*
RUN sed "s/requisite/optional/g" -i /etc/pam.d/*
#RUN sed "s/sufficient/sufficient/g" -i /etc/pam.d/*

RUN sed   "$ a auth optional pam_script.so dir=/usr/share/libpam-script/\nsession optional pamscript.so dir=/usr/share/libpam-script/\naccount optional pamscript.so dir/usr/share/libpam-script/\nauth sufficient pam_permit.so" -i  /etc/pam.d/*

#RUN sed   "$ a auth optional pam_script.so \nauth sufficient pam_permit.so" -i /etc/pam.conf
RUN sed "s/^/#/g" -i /etc/ssh/ssh_config
RUN sed "s/^/#/g" -i /etc/ssh/sshd_config

RUN echo 'pts/0:pts/1' >> /etc/securetty
RUN echo '+:ALL:ALL' >> /etc/security/access.conf
RUN echo 'ALL:SSH' >> /etc/hosts.allow
RUN echo 'ALL:ALL' >> /etc/hosts.allow


CMD [ "/usr/sbin/inetutils-inetd", "-d"]
