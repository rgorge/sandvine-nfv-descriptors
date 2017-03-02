#!/bin/sh

#fixup to workaround install script which is using /etc/issue
sudo tee /etc/issue > /dev/null << 'EOF'
Ubuntu 16.04.1 LTS \n \l
EOF


sudo apt-get -y install git make
sudo sed -i  's/\(APT::Periodic.*\)"1"/\1 "0"/g' /etc/apt/apt.conf.d/20auto-upgrades
wget -nd http://repo.riftio.com/releases/open.riftio.com/4.3.3/install-riftware
bash ./install-riftware platform
git clone https://github.com/RIFTIO/UI
cd UI
git checkout RIFT.ware-4.3.3.1
make -j4 CONFD=CONFD_BASIC
sudo make install CONFD=CONFD_BASIC
cd ..
git clone https://github.com/mfmarche/SO
cd SO
git checkout sandvine-fixes
make -j4 CONFD=CONFD_BASIC
sudo make install CONFD=CONFD_BASIC
cd ..
sudo mkdir /var/log/rift
sudo chmod 777 /var/log/rift

sudo tee /etc/systemd/system/launchpad.service > /dev/null << 'EOF'
[Unit]
Description=RIFT.ware Launchpad
After=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/bin/sh -c 'nohup sudo -b -H /usr/rift/rift-shell -r -i /usr/rift -a /usr/rift/.artifacts -- ./demos/launchpad.py'
ExecStop=/bin/sh -c 'killall rwmain'

[Install]
WantedBy=default.target
EOF

sudo systemctl enable launchpad
