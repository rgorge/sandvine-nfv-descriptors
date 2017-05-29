VNFD_DIRS:= server_vnfd tse_vnfd pts_vnfd cc_vnfd spb_vnfd pktgen_dpdk_vnfd
NSD_DIRS:= tse_nsd cc_nsd tse_pktgen_nsd

PKG_TAR := $(addprefix build/,$(addsuffix .tar.gz, $(VNFD_DIRS) $(NSD_DIRS) ))

VNFD_BUILD_DIR := $(addprefix build/,$(VNFD_DIRS))
NSD_BUILD_DIR := $(addprefix build/,$(NSD_DIRS))

PKG_CHECKSUMS:= $(addsuffix /checksums.txt, $(VNFD_DIRS) $(NSD_DIRS) )
PKG_YAML:= $(addsuffix .yaml, $(VNFD_DIRS) $(NSD_DIRS) )

server_vnfd_IMAGE ?= "Ubuntu 16.04.1 LTS - Xenial Xerus - 64-bit - Cloud Based Image"
pktgen_dpdk_vnfd_IMAGE ?= $(server_vnfd_IMAGE)
cc_vnfd_IMAGE     ?= "Ubuntu 16.04.1 LTS - Xenial Xerus - 64-bit - Cloud Based Image"
tse_vnfd_IMAGE    ?= tse
pts_vnfd_IMAGE    ?= pts
spb_vnfd_IMAGE    ?= spb
LICENSE_SERVER    ?= license.sandvine.rocks

all:  $(VNFD_BUILD_DIR) $(NSD_BUILD_DIR)
	@$(MAKE) $(PKG_TAR)

BUILD_TARGET = build/$(TARGET)

%.tar.gz: TARGET=$(notdir $*)

%.tar.gz:
	@cat $(BUILD_TARGET)/template/$(TARGET).yaml | sed -e 's/vnfd:image:.*/vnfd:image: $($(TARGET)_IMAGE)/g' > $(BUILD_TARGET)/$(TARGET).yaml
	@cd $(BUILD_TARGET); find . -type f -not -path "*/template" -not -path "*/template/*" | xargs md5sum | sed -e 's/\.\///g' > checksums.txt; cd ..
	@tar --exclude=template -cvf build/$(TARGET).tar -C build $(TARGET)/ > /dev/null
	@gzip $(BUILD_TARGET).tar

%.yaml.clean:
	@rm -f $*/$*.yaml

$(VNFD_BUILD_DIR): TEMPLATE_NAME=$(shell basename $@)
$(VNFD_BUILD_DIR): CLOUD_INIT=$@/cloud_init/cloud_init.cfg
$(VNFD_BUILD_DIR):
	@mkdir -p $@
	@cp -R $(TEMPLATE_NAME)/* $@
	@mkdir -p $@/cloud_init
	@cat $@/template/cloud_init.cfg | sed -e 's/license_server_primary=.*/license_server_primary="$(LICENSE_SERVER)"/g' > $(CLOUD_INIT)
	@echo "" >> $(CLOUD_INIT)
	@mkdir -p $@/scripts
	@ssh-keygen -N "" -f $@/scripts/$(TEMPLATE_NAME)-key > /dev/null
	@echo "ssh_authorized_keys:" >> $(CLOUD_INIT)
	@echo -n "  - " >> $(CLOUD_INIT)
	@cat $@/scripts/$(TEMPLATE_NAME)-key.pub >> $(CLOUD_INIT)

$(NSD_BUILD_DIR):
	@mkdir -p $@
	@cp -R $(shell basename $@)/* $@ 

.PHONY: build_dir

clean:
	@rm -rf build
