# This is the Makefile of China Set: Trains, combining WenSim's and Planetmaker's together.
# This makes it possible to do voxel rendering and file compilation by simply typing "make".
# Under GPL v2.

# The displayed name and the filename of the bundled grf shall look like:
#                           mynewgrf-a.b.c.d
# Where d is the REPO_REVISION which never decreases per compilation,
#       c is the MINOR_VERSION which increases by 1 each release and decreases to 0 once b increases by 1,
#       b is the MAJOR_VERSION which increases by 1 each "major" release and decreases to 0 once a increases by 1,
#       a is the BREAKING_VERSION which increases by 1 only if something breakground happens to this NewGRF.

SHELL := /bin/bash

-include ./Makefile.config
-include ./Makefile.dist

FILE_NAME	  ?= mynewgrf
VOX_DIR 	  ?= gfx
DOC_FILES	  ?= docs/changelog.txt docs/readme.txt docs/license.txt
CUSTOM_TAGS   ?= custom_tags.txt
PALETTE 	  ?= ttd_palette.json

GORENDER 	?= renderobject -overwrite
NMLC 		?= nmlc -c
GCC 		:= gcc
MANIFEST 	:= manifest.json

.PHONY: all sprites code bundle_tar clean clean_grf clean_png copy
# default rule
all: sprites code bundle_tar

# voxel paths
VOX_FILES = $(wildcard $(VOX_DIR)/*.vox wildcard $(VOX_DIR)/*/*.vox)

VOX_8BPP_FILES = $(addsuffix _8bpp.png, $(basename $(VOX_FILES)))
VOX_32BPP_FILES = $(addsuffix _32bpp.png, $(basename $(VOX_FILES)))
VOX_MASK_FILES = $(addsuffix _mask.png, $(basename $(VOX_FILES)))

VOX_GENREATED_FILES = $(VOX_8BPP_FILES) $(VOX_32BPP_FILES) $(VOX_MASK_FILES)

%_8bpp.png %_32bpp.png %_mask.png: %.vox
	@echo "Rendering, manifest = $(MANIFEST), palette = $(dir $<)/$(PALETTE), $<"
	@$(GORENDER) -m $(MANIFEST) --palette $(dir $<)/$(PALETTE) $<

# sprites
sprites: $(VOX_GENREATED_FILES)

# code
NML_FILE 	   ?= $(FILE_NAME).nml
INDEX_FILE 	   ?= $(FILE_NAME).pnml
GRF_FILE 	   ?= $(FILE_NAME).grf
CODE_FILES 	   ?= $(INDEX_FILE)
CUSTOM_TAGS	   ?= custom_tags.txt
TEMP_DIR	   ?= temp


$(CUSTOM_TAGS): ./Makefile.dist
	$(GCC) -E -x c -o $@ $<
	$(_V) echo VERSION_STRING :$(REPO_VERSION_STRING) >> $@

$(NML_FILE): $(CUSTOM_TAGS) $(CODE_FILES) $(VOX_GENREATED_FILES)
	$(GCC) -E -x c -D REPO_REVISION=$(REPO_REVISION) -D VERSION_STRING=$(REPO_VERSION_STRING) -o $@ $(INDEX_FILE)

$(GRF_FILE): $(NML_FILE) $(CUSTOM_TAGS)
	$(NMLC) $<
	if [ ! -d $(TEMP_DIR) ]; then mkdir $(TEMP_DIR); fi
	mv -f $(NML_FILE) $(TEMP_DIR)/$(NML_FILE)
	mv -f $(CUSTOM_TAGS) $(TEMP_DIR)/$(CUSTOM_TAGS)
# Rule to run nmlc when the NML file changes
code: $(GRF_FILE)

# clean
clean: clean_grf clean_png clean_bundle clean_bundle_src

clean_grf:
	@echo "Cleaning GRF and NML files"
	@echo "Warning: clean grf won't work when using powershell, please use bash instead."
	@rm -f *.grf
	@rm -f *.nml
	@rm -f $(CUSTOM_TAGS)

clean_png:
	@echo "Cleaning PNG files"
	@echo "Warning: clean png won't work when using powershell, please use bash instead."
	@find $(VOX_DIR)/ -name '*.png' -type f -delete

clean_bundle:
	@echo "Warning: clean bundle won't work when using powershell, please use bash instead."
	$(_V) -rm -rf $(DIR_NAME)
	$(_V) -rm -rf $(DIR_NAME).tar
	$(_V) -rm -rf $(DIR_NAME).tar.zip
	$(_V) -rm -rf $(DIR_NAME).tar.gz
	$(_V) -rm -rf $(DIR_NAME).tar.bz2
	$(_V) -rm -rf $(DIR_NAME).tar.xz

clean_bundle_src:
	$(_V) -rm -rf $(DIR_NAME_SRC)
	$(_V) -rm -rf $(DIR_NAME_SRC).tar
	$(_V) -rm -rf Makefile.fordist

BUNDLE_FILES   ?= $(GRF_FILE) $(DOC_FILES)

TAR            ?= tar
TAR_FLAGS      ?= -cf

ZIP            ?= zip
ZIP_FLAGS      ?= -9rq

GZIP           ?= gzip
GZIP_FLAGS     ?= -9f

BZIP           ?= bzip2
BZIP_FLAGS     ?= -9fk

XZ             ?= xz
XZ_FLAGS       ?= -efk

# OSX has nice extended file attributes which create their own file within tars. We don't want those, thus don't copy them
CP_FLAGS       ?= $(shell [ "$(OSTYPE)" = "Darwin" ] && echo "-rfX" || echo "-rf")

# Use the grfID programme to find the checksum which OpenTTD checks
GRFID          ?= grfid
GRFID_FLAGS    ?= -m

# Common to all filenames
DIR_NAME            := $(FILE_NAME)-$(REPO_VERSION_STRING)
DIR_NAME_SRC        := $(DIR_NAME)-source

TAR_FILENAME       := $(DIR_NAME).tar
BZIP_FILENAME      := $(TAR_FILENAME).bz2
GZIP_FILENAME      := $(TAR_FILENAME).gz
XZ_FILENAME        := $(TAR_FILENAME).xz
ZIP_FILENAME       := $(DIR_NAME).zip
MD5_FILENAME       := $(DIR_NAME).md5
MD5_SRC_FILENAME   ?= $(DIR_NAME).check.md5

# Creating file with checksum
%.md5: $(GRF_FILE)
	$(_V) $(GRFID) $(GRFID_FLAGS) $< > $@

# Bundle directory
$(DIR_NAME): $(BUNDLE_FILES)
	$(_V) if [ -e $@ ]; then rm -rf $@; fi
	$(_V) mkdir "$@"
	$(_V) for i in $(BUNDLE_FILES); do cp $(CP_FLAGS) $$i $@; done

$(DIR_NAME).tar: $(DIR_NAME)
	$(_V) $(TAR) $(TAR_FLAGS) $@ $<

bundle_tar: $(DIR_NAME).tar
bundle_zip: $(ZIP_FILENAME)
%.zip: $(DIR_NAME).tar
	$(_V) $(ZIP) $(ZIP_FLAGS) $@ $< >/dev/null
bundle_bzip: $(DIR_NAME).tar.bz2
%.tar.bz2: %.tar
	$(_V) $(BZIP) $(BZIP_FLAGS) $^
bundle_gzip: $(DIR_NAME).tar.gz
# gzip has no option -k, so we cat the tar to keep it
%.tar.gz: %.tar
	$(_V) cat $^ | $(GZIP) $(GZIP_FLAGS) > $@
bundle_xz: $(DIR_NAME).tar.xz
%.tar.xz: %.tar
	$(_V) $(XZ) $(XZ_FLAGS) $^

################################################################
# Bundle source targets
# target 'bundle_src which builds source bundle
################################################################
bundle_src: $(DIR_NAME_SRC).tar

bundle_bsrc: $(DIR_NAME_SRC).tar.bz2
bundle_gsrc: $(DIR_NAME_SRC).tar.gz
bundle_xsrc: $(DIR_NAME_SRC).tar.xz
bundle_zsrc: $(DIR_NAME_SRC).tar.zip

maintainer-clean::
	$(_V) -rm -rf $(MD5_SRC_FILENAME)


help::
	$(_E) "Default targets:"
	$(_E)
	$(_E) "all:         Build the entire NewGRF and its documentation"
