#
#   Copyright 2016 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Author(s): Austin Cormier
# Creation Date: 2016/05/23
#
BUILD_DIR = build

JUJU_BUILD_DIR = ../juju-charms/builds

NSDS := sandvine_pts_ns sandvine_spb_ns
NSD_SRC_DIR := src/nsd
NSD_BUILD_DIR := $(BUILD_DIR)/nsd

NSD_SRC_DIRS := $(addprefix $(NSD_SRC_DIR)/, $(NSDS))
NSD_BUILD_DIRS := $(addprefix $(NSD_BUILD_DIR)/, $(NSDS))
NSD_PKGS := $(addsuffix .tar.gz, $(NSDS))
NSD_BUILD_PKGS := $(addprefix $(NSD_BUILD_DIR)_pkgs/, $(NSD_PKGS))
KEY_DIR := $(BUILD_DIR)/keys

VNFDS := sandvine_pts_vnfd sandvine_spb_vnfd
VNFD_SRC_DIR := src/vnfd
VNFD_BUILD_DIR := $(BUILD_DIR)/vnfd

Q=@
VNFD_SRC_DIRS := $(addprefix $(VNFD_SRC_DIR)/, $(VNFDS))
VNFD_BUILD_DIRS := $(addprefix $(VNFD_BUILD_DIR)/, $(VNFDS))
VNFD_PKGS := $(addsuffix .tar.gz, $(VNFDS))
VNFD_BUILD_PKGS := $(addprefix $(VNFD_BUILD_DIR)_pkgs/, $(VNFD_PKGS))
VNFD_CONFIG_KEY_NAME := config-key
VNFD_CONFIG_KEY_STRING := keystring
VNFD_CONFIG_KEYS := $(addsuffix /$(VNFD_CONFIG_KEY_NAME), $(addprefix $(KEY_DIR)/, $(VNFDS)))
CLOUD_INIT_FILE := cloud_init/cloud_init.cfg

all: $(VNFD_CONFIG_KEYS) $(VNFD_BUILD_PKGS) $(NSD_BUILD_PKGS)

clean:
	-$(Q) $(RM) -rf $(BUILD_DIR)

$(NSD_BUILD_DIR)/%: $(NSD_SRC_DIR)/%
	$(Q)mkdir -p $(NSD_BUILD_DIR)
	$(Q)cp -rf $< $(NSD_BUILD_DIR)
	$(Q)src/gen_nsd_pkg.sh $< $@

$(BUILD_DIR)/nsd_pkgs/%.tar.gz: $(NSD_BUILD_DIR)/%
	$(Q)src/generate_descriptor_pkg.sh -d $(BUILD_DIR)/nsd_pkgs $<

$(KEY_DIR):
	$(Q)mkdir -p $@

$(VNFD_CONFIG_KEYS): $(KEY_DIR)
	$(Q)mkdir -p $(shell dirname $@)
	$(Q)ssh-keygen -N '' -f $@ > /dev/null
	$(Q)cat $@ | sed -e ':a;N;$$!ba;s/\n/\\\\n/g' > $@.$(VNFD_CONFIG_KEY_STRING)

$(VNFD_BUILD_DIRS): TARGET=$(notdir $@)
$(VNFD_BUILD_DIRS): $(VNFD_CONFIG_KEYS)
	$(Q)mkdir -p $(VNFD_BUILD_DIR) 
	$(Q)cp -rf $(VNFD_SRC_DIR)/$(TARGET)/ $(VNFD_BUILD_DIR)
	$(Q)KEYSTRING=$$(cat $(KEY_DIR)/$(TARGET)/$(VNFD_CONFIG_KEY_NAME).$(VNFD_CONFIG_KEY_STRING)); \
	sed -i "s%__SSH_PRIVATE_KEY__%$$KEYSTRING%g" $(VNFD_BUILD_DIR)/$(TARGET)/$(TARGET).yaml
	$(Q)CHARM_NAME=$$(cat $(VNFD_SRC_DIR)/$(TARGET)/$(TARGET).yaml | awk '/charm/{print $$2}'); \
	mkdir -p $(VNFD_BUILD_DIR)/$(TARGET)/charms; \
	cp -rf $(JUJU_BUILD_DIR)/$$CHARM_NAME $(VNFD_BUILD_DIR)/$(TARGET)/charms
	$(Q)echo "ssh_authorized_keys:" >> $(VNFD_BUILD_DIR)/$(TARGET)/$(CLOUD_INIT_FILE)
	$(Q)echo -n "  - " >> $(VNFD_BUILD_DIR)/$(TARGET)/$(CLOUD_INIT_FILE)
	$(Q)cat $(KEY_DIR)/$(TARGET)/$(VNFD_CONFIG_KEY_NAME).pub >> $(VNFD_BUILD_DIR)/$(TARGET)/$(CLOUD_INIT_FILE)

$(BUILD_DIR)/vnfd_pkgs/%.tar.gz: $(VNFD_BUILD_DIR)/%
	$(Q)src/generate_descriptor_pkg.sh -d $(BUILD_DIR)/vnfd_pkgs $<
