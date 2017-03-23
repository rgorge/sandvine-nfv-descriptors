from charms.reactive import when, when_not, set_state
from charms.reactive.bus import get_state
from pysvapi.elementdriver.sshdriver import sshdriver

from charmhelpers.core.hookenv import log
from charmhelpers.core.hookenv import config
from charmhelpers.core.hookenv import status_set

@when_not('sandvine-pts-proxy.installed')
def install_sandvine_pts_proxy():
    status_set('maintenance','Installing')
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_state('sandvine-pts-proxy.installed')
    status_set('active','ready')

def configure_port(sess_pci,sess_port,port,role):
    if port:
        log('adding {} port: {}'.format(role,port), 'INFO')
        pci="0000:00:0{}.0".format(port)
        interface='1-'+port
        sess_pci.add_cmd('add config interface pci-address {} interface {} type fastpath'.format(pci,interface))
        sess_port.add_cmd('set config interface {} enabled true'.format(interface))
        sess_port.add_cmd('set config interface {} function {}'.format(interface,role))

        if role is not 'service':
            sess_port.add_cmd('set config interface {} bridge-group {}'.format(interface,1))

@when('config.changed')
def setup_ports():

    cfg = config()
    status_set('maintenance','configuring ssh connection')
    if not cfg['ssh-hostname'] or not cfg['ssh-private-key']:
        status_set('blocked','need sshproxy configured')
        log('sshproxy not yet fully configured', 'DEBUG')
        return


    #hostname could contain a dual ip, one for floating and non-floating.
    #appears that the floating is always the first entry.
    host=cfg['ssh-hostname'].split(';')[0]

    sess_pci=sshdriver.ElementDriverSSH(host,private_key=cfg['ssh-private-key'].replace('\\n','\n'))
    sess_port=sshdriver.ElementDriverSSH(host,private_key=cfg['ssh-private-key'].replace('\\n','\n'))

    do_commit=False
    if get_state('config.changed.fastpath-service-ports',False) is None:
        for port in cfg['fastpath-service-ports'].split(','):
            do_commit=True
            configure_port(sess_pci,sess_port,port,'service')

    if get_state('config.changed.fastpath-subscriber-ports',False) is None:
        for port in cfg['fastpath-subscriber-ports'].split(','):
            do_commit=True
            configure_port(sess_pci,sess_port,port,'subscriber')

    if get_state('config.changed.fastpath-internet-ports',False) is None:
        for port in cfg['fastpath-internet-ports'].split(','):
            do_commit=True
            configure_port(sess_pci,sess_port,port,'internet')

    if do_commit:
        status_set('maintenance','configuring ports')
        try:
            sess_pci.configuration_commit()
            sess_port.configuration_commit()
        except: 
            status_set('blocked','failed to commit')
            return

    status_set('active','ready')
    set_state('sandvine-pts-proxy.configured')
