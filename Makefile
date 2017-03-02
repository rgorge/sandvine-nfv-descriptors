SUBDIRS =  osm \
           rift

SUBDIRS_CLEAN = $(addsuffix .clean, $(SUBDIRS))

.PHONY: $(SUBDIRS) $(SUBDIRS_CLEAN) clean

all: $(SUBDIRS)

clean: $(SUBDIRS_CLEAN)

$(SUBDIRS_CLEAN): %.clean:
	@$(MAKE) -C $* clean

$(SUBDIRS):
	@$(MAKE) -C $@

