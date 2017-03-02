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

def configure_license_servers(yaml_cfg,logger):
    # walk through vnf records 
    for index, vnfr in yaml_cfg['vnfr'].items():
        logger.debug("VNFR {}: {}".format(index, vnfr))

        if re.search('PTS|TSE',vnfr['name']):

            if not yaml_cfg.has_key('parameter'):
                logger.info("No parameters passed in")
                continue

            if not yaml_cfg['parameter'].has_key('license_server'):
                logger.info("No license server provided")
                continue

            logger.info("Setting license server on {}:{} license server = {}".format(vnfr['name'],vnfr['mgmt_ip_address'], yaml_cfg['parameter']['license_server']))
            sess=sshdriver.ElementDriverSSH(vnfr['mgmt_ip_address'])
            cli = client.Client(sess)
            cli.configure_license_server( yaml_cfg['parameter']['license_server'] )


def main(argv=sys.argv[1:]):
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("yaml_cfg_file", type=argparse.FileType('r'))
        parser.add_argument("-q", "--quiet", dest="verbose", action="store_false")
        parser.add_argument("-r", "--rundir", dest='run_dir', action='store')
        args = parser.parse_args()

        run_dir = args.run_dir
        if not run_dir:
            run_dir = os.path.join(os.environ['RIFT_INSTALL'], "var/run/rift")
            if not os.path.exists(run_dir):
                os.makedirs(run_dir)
        log_file = "{}/set_license_server-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))
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
        yaml_str = args.yaml_cfg_file.read()
        # logger.debug("Input YAML file:\n{}".format(yaml_str))
        yaml_cfg = yaml.load(yaml_str)
        logger.debug("Input YAML: {}".format(yaml_cfg))
        configure_license_servers(yaml_cfg,logger)

    except Exception as e:
        logger.exception(e)
        raise e

if __name__ == "__main__":
    main()
