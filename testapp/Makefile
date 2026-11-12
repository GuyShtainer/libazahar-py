# SPDX-License-Identifier: GPL-3.0-or-later
# libazahar-py test app: a .3dsx only, built with devkitARM (devkitARM must be first in PATH).
.SUFFIXES:

ifeq ($(strip $(DEVKITARM)),)
$(error "Set DEVKITARM, and put devkitARM first in PATH")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITARM)/3ds_rules

TARGET      := testapp
BUILD       := build
SOURCES     := source
INCLUDES    := source
APP_TITLE   := lazpy test app
APP_DESCRIPTION := libazahar-py test app
APP_AUTHOR  := libazahar-py
OUTDIR      := $(CURDIR)/../build

ARCH    := -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft
CFLAGS  := -g -std=gnu11 -Wall -Wextra -Werror -O2 -mword-relocations -ffunction-sections $(ARCH)
CFLAGS  += $(INCLUDE) -D__3DS__
ASFLAGS := -g $(ARCH)
LDFLAGS  = -specs=3dsx.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)
LIBS    := -lcitro2d -lcitro3d -lctru -lm
LIBDIRS := $(PORTLIBS) $(CTRULIB)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT := $(OUTDIR)/$(TARGET)
export TOPDIR := $(CURDIR)
export VPATH  := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR := $(CURDIR)/$(BUILD)

CFILES    := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
PICAFILES := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.v.pica)))
export LD := $(CC)
export OFILES_SOURCES := $(CFILES:.c=.o)
export OFILES_BIN := $(PICAFILES:.v.pica=.shbin.o)
export OFILES := $(OFILES_BIN) $(OFILES_SOURCES)
export HFILES := $(PICAFILES:.v.pica=_shbin.h)

# libctru and citro headers by -isystem so their own warnings cannot fail our build
export INCLUDE := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) \
                  $(foreach dir,$(LIBDIRS),-isystem $(dir)/include) \
                  -I$(CURDIR)/$(BUILD)
export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

# no icon given: smdhtool takes libctru's default_icon.png (zlib licence)
export _3DSXDEPS := $(OUTPUT).smdh
export _3DSXFLAGS += --smdh=$(OUTPUT).smdh

.PHONY: all clean

all: $(BUILD)
	@mkdir -p $(OUTDIR)
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

$(BUILD):
	@mkdir -p $@

clean:
	@echo clean ...
	@rm -fr $(BUILD) $(OUTPUT).3dsx $(OUTPUT).smdh $(OUTPUT).elf

else

$(OUTPUT).3dsx : $(OUTPUT).elf $(_3DSXDEPS)
$(OFILES_SOURCES) : $(HFILES)
$(OUTPUT).elf : $(OFILES)

.PRECIOUS : %.shbin
%.shbin.o %_shbin.h : %.shbin
	$(SILENTMSG) $(notdir $<)
	$(bin2o)

-include $(DEPSDIR)/*.d

endif
