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

vnfd_names={"tse": "TSE", 
            "pts": "PTS",
            "spb": "SPB"}

class TSEConfigTool():

    def __init__(self,_logger):
        self.logger=_logger;

    def get_vnfr(self,yaml_cfg,name):
	for item in yaml_cfg:
	  if name in item['name']:
	      return item
	return None

    def get_vnf_record_from_initial(self,vnfd_name,yaml_cfg,record):
        self.logger.debug("get {} from initial".format(vnfd_name))
        for index, vnfr in yaml_cfg['vnfr'].items():
            self.logger.debug("VNFR {}: {}".format(index, vnfr))
            if re.search(vnfd_name,vnfr['name']):
                print("record: {}".format(vnfr))
                mgmt=vnfr[record]
                self.logger.debug("{} {} {}".format(vnfd_name,record,mgmt))
                return mgmt
        self.logger.info("ERROR: cannot find {}".format(vnfd_name))
        sys.exit(1)

    def get_pts_mgmt(self,yaml_cfg):
        if 'vnfrs_in_group' in yaml_cfg:
            self.logger.debug("get_pts: from scale")
            mgmt = yaml_cfg['vnfrs_in_group'][0]['rw_mgmt_ip']
            self.logger.debug("pts mgmt {}".format(mgmt))
            return mgmt
        else:
            return self.get_vnf_record_from_initial(vnfd_names['pts'],yaml_cfg,'mgmt_ip_address')

    def get_pts_name(self,yaml_cfg):
        if 'vnfrs_in_group' in yaml_cfg:
            self.logger.debug("get_pts: from scale")
            name = yaml_cfg['vnfrs_in_group'][0]['name']
            self.logger.debug("pts name {}".format(name))
            return name
        else:
            return self.get_vnf_record_from_initial(vnfd_names['pts'],yaml_cfg,'name')

    def get_vnf_mgmt(self,yaml_cfg,vnf_name):
        if 'vnfrs_others' in yaml_cfg:
            vnfr = self.get_vnfr(yaml_cfg['vnfrs_others'],vnfd_names[vnf_name])
            if vnfr is None:
                return None
            mgmt = vnfr['rw_mgmt_ip']
            self.logger.debug("vnf name {} mgmt {}".format(vnfr['name'],mgmt))
            return mgmt
        else:
            return self.get_vnf_record_from_initial(vnfd_names[vnf_name],yaml_cfg,'mgmt_ip_address')

    def configure(self,yaml_cfg):
        pts_mgmt=self.get_pts_mgmt(yaml_cfg)
        tse_mgmt=self.get_vnf_mgmt(yaml_cfg,'tse')
        spb_mgmt=self.get_vnf_mgmt(yaml_cfg,'spb')

        if pts_mgmt is None:
	    self.logger.info("pts mgmt None")
	    sys.exit(1)

        if tse_mgmt is None:
	    self.logger.info("tse mgmt None")
	    sys.exit(1)

        pts_sess=sshdriver.ElementDriverSSH(pts_mgmt,private_key_file=os.path.join(os.environ['RIFT_INSTALL'], "usr/bin/pts_vnfd-key"))
        tse_sess=sshdriver.ElementDriverSSH(tse_mgmt,private_key_file=os.path.join(os.environ['RIFT_INSTALL'], "usr/bin/tse_vnfd-key"))

	self.logger.info("connecting to pts {}".format(self.get_pts_mgmt(yaml_cfg)))
	if not pts_sess.wait_for_api_ready():
	    self.logger.info("PTS API did not become ready")
	    sys.exit(1)
	self.logger.info("pts api is ready")

	if not tse_sess.wait_for_api_ready():
	    logger.info("TSE API did not become ready")
	    sys.exit(1)
	self.logger.info("tse api is ready")

	pts_cli = client.Client(pts_sess)
	tse_cli = client.Client(tse_sess)
	
	# get the pts mac address
	mac=pts_cli.get_interface_mac('1-3')

	cli_pts_name = self.get_pts_name(yaml_cfg).replace(' ','_')
	self.logger.debug("retrieved pts {} interface 1-3 mac {}".format(cli_pts_name,mac))

	#need a name without spaces

	tse_sess.add_cmd('add config traffic-steering service-locator mac-nsh-locator ' +  cli_pts_name + ' mac ' + mac )
	tse_sess.add_cmd('add config traffic-steering service-function ' + cli_pts_name + ' transport mac-nsh locator ' + cli_pts_name )
	tse_sess.add_cmd('add config traffic-steering service-group-member ' + cli_pts_name + ' service-group pts-group' )

        if spb_mgmt is not None:
            spb_cmd='set config service spb servers {}'.format(spb_mgmt)
            tse_sess.add_cmd(spb_cmd)
            pts_sess.add_cmd(spb_cmd)
            pts_sess.configuration_commit()

	tse_sess.configuration_commit()
	self.logger.info("configuration complete")

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
        log_file = "{}/pts-scale-{}.log".format(run_dir, time.strftime("%Y%m%d%H%M%S"))
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
        config_tool=TSEConfigTool(logger)
        config_tool.configure(yaml_cfg)

    except Exception as e:
        logger.exception(e)
        raise e

if __name__ == "__main__":
    main()
