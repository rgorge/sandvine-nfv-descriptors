#!/usr/bin/env python

import argparse
import logging
import os
import subprocess
import sys
import time
from pysvapi.elementdriver.sshdriver import sshdriver
from pysvapi.svapiclient import client
import yaml
import re

def get_vnfr(yaml_cfg):
    for index, vnfr in yaml_cfg['vnfr'].items():
        if yaml_cfg['vnfr_name'] in vnfr['name']:
            return vnfr
    return None

def configure(yaml_cfg,logger):
    tse_vnfr = get_vnfr(yaml_cfg)

    if tse_vnfr is None:
        logger.info("NO vnfr record found")
        sys.exit(1)

    logger.debug("TSE YAML: {}".format(tse_vnfr))

    sess=sshdriver.ElementDriverSSH(tse_vnfr['mgmt_ip_address'],private_key_file=os.path.join(os.environ['RIFT_INSTALL'], "usr/bin/tse_vnfd-key"))

    #if yaml_cfg['parameter']['license_server'] is not 'None':
    #    cli = client.Client(sess)
    #    cli.configure_license_server( yaml_cfg['parameter']['license_server'] )

    sess.add_cmd('add config traffic-steering service-group group pts-group balancing-algorithm static fail-mode skip')
    sess.add_cmd('add config traffic-steering terminator 1-3 type interface')
    sess.add_cmd('add config traffic-steering terminator 1-4 type interface')

    sess.add_cmd('add config traffic-steering forwarding-table-interface 1-3 forwarding-table default')
    sess.add_cmd('add config traffic-steering forwarding-table-interface 1-4 forwarding-table default')
    sess.add_cmd('add config traffic-steering forwarding-table-interface 1-5 forwarding-table default')

    sess.add_cmd('add config traffic-steering interface-terminator 1-3 egress-interface 1-3')
    sess.add_cmd('add config traffic-steering interface-terminator 1-4 egress-interface 1-4')
    sess.add_cmd('add config traffic-steering service-path bg1upstream forwarding-table default path-id 0 starting-index 2')
    sess.add_cmd('add config traffic-steering service-path bg1downstream forwarding-table default path-id 0 starting-index 254')
    sess.add_cmd('add config traffic-steering service-path-hop 2 path bg1upstream forwarding-table default destination pts-group destination-type service-group')
    sess.add_cmd('add config traffic-steering service-path-hop 254 path bg1downstream forwarding-table default destination pts-group destination-type service-group')
    sess.add_cmd('add config traffic-steering service-path-hop 253 path bg1downstream forwarding-table default destination 1-3 destination-type terminator')
    sess.add_cmd('add config traffic-steering service-path-hop 1 path bg1upstream forwarding-table default destination 1-4 destination-type terminator')
    sess.add_cmd('add config traffic-steering classifier interface 1-3 path bg1upstream')
    sess.add_cmd('add config traffic-steering classifier interface 1-4 path bg1downstream')
    sess.add_cmd('set config interface 1-3 enabled true')
    sess.add_cmd('set config interface 1-4 enabled true')
    sess.add_cmd('set config interface 1-5 enabled true')

    if not sess.wait_for_api_ready():
        logger.info("API did not become ready")
        sys.exit(1)
    sess.configuration_commit()

def main(argv=sys.argv[1:]):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument("-q", "--quiet", dest="verbose", action="store_false")
        parser.add_argument("-r", "--rundir", dest='run_dir', action='store')
        args = parser.parse_args()

        yaml_str = args.yaml_cfg_file.read()
        yaml_cfg = yaml.load(yaml_str)

        run_dir = args.run_dir
        if not run_dir:
            run_dir = os.path.join(os.environ['RIFT_INSTALL'], "var/run/rift")
            if not os.path.exists(run_dir):
                os.makedirs(run_dir)
        log_file = "{}/initial-configuration-{}-{}.log".format(run_dir, yaml_cfg['vnfr_name'], time.strftime("%Y%m%d%H%M%S"))
        logging.basicConfig(filename=log_file, level=logging.DEBUG)
        logger = logging.getLogger()

    except Exception as e:
        print("Exception in {}: {}".format(__file__, e))
        sys.exit(1)

    try:
        ch = logging.StreamHandler()
        if args.verbose:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.INFO)

        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    except Exception as e:
        logger.exception(e)
        raise e

    try:
        logger.debug("Input YAML: {}".format(yaml_cfg))
        configure(yaml_cfg,logger)

    except Exception as e:
        logger.exception(e)
        raise e

if __name__ == "__main__":
    main()
