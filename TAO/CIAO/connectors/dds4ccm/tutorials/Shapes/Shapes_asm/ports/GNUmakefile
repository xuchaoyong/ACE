# -*- makefile -*-
#----------------------------------------------------------------------------
#       GNU ACE Workspace
#
# $Id: GNUACEWorkspaceCreator.pm 94635 2011-10-06 12:59:23Z johnnyw $
#
# This file was generated by MPC.  Any changes made directly to
# this file will be lost the next time it is generated.
#
# MPC Command:
# /home/build/DOC_ROOT/stage-644/ACE_wrappers/bin/mwc.pl -type gnuace -exclude "TAO/TAO_*.mwc,TAO/CIAO/CIAO_*.mwc" -workers 10 -recurse -hierarchy -relative ACE_ROOT=/home/build/DOC_ROOT/stage-644/ACE_wrappers -relative TAO_ROOT=/home/build/DOC_ROOT/stage-644/ACE_wrappers/TAO -relative CIAO_ROOT=/home/build/DOC_ROOT/stage-644/ACE_wrappers/TAO/CIAO -relative DANCE_ROOT=/home/build/DOC_ROOT/stage-644/ACE_wrappers/TAO/DAnCE
#
#----------------------------------------------------------------------------

MAKEFILE = GNUmakefile

ifeq ($(findstring k,$(MAKEFLAGS)),k)
  KEEP_GOING = -
endif

include $(ACE_ROOT)/include/makeinclude/macros.GNU

all: Shapes_Control_obj_idl_gen Shapes_Control_obj_lem_gen Shapes_defn_idl_gen Shapes_defn_stub Shapes_Control_obj_stub Shapes_Control_obj_lem_stub Shapes_Control_obj_svnt Shapes_ShapeType_msg_stub

REMAINING_TARGETS := $(filter-out all,$(TARGETS_NESTED:.nested=)) $(CUSTOM_TARGETS)

$(REMAINING_TARGETS):
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_idl_gen $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_lem_gen $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_defn_idl_gen $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_defn_stub $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_stub $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_lem_stub $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_svnt $(@)
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_ShapeType_msg_stub $(@)

.PHONY: Shapes_Control_obj_idl_gen
Shapes_Control_obj_idl_gen:
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_idl_gen all

.PHONY: Shapes_Control_obj_lem_gen
Shapes_Control_obj_lem_gen: Shapes_Control_obj_idl_gen
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_lem_gen all

.PHONY: Shapes_defn_idl_gen
Shapes_defn_idl_gen:
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_defn_idl_gen all

.PHONY: Shapes_defn_stub
Shapes_defn_stub: Shapes_defn_idl_gen
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_defn_stub all

.PHONY: Shapes_Control_obj_stub
Shapes_Control_obj_stub: Shapes_Control_obj_idl_gen Shapes_defn_idl_gen Shapes_defn_stub
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_stub all

.PHONY: Shapes_Control_obj_lem_stub
Shapes_Control_obj_lem_stub: Shapes_Control_obj_lem_gen Shapes_Control_obj_stub
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_lem_stub all

.PHONY: Shapes_Control_obj_svnt
Shapes_Control_obj_svnt: Shapes_defn_idl_gen Shapes_defn_stub Shapes_Control_obj_stub Shapes_Control_obj_lem_stub
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_Control_obj_svnt all

.PHONY: Shapes_ShapeType_msg_stub
Shapes_ShapeType_msg_stub:
	$(KEEP_GOING)@$(MAKE) -f GNUmakefile.Shapes_ShapeType_msg_stub all

project_name_list:
	@echo Shapes_Control_obj_idl_gen
	@echo Shapes_Control_obj_lem_gen
	@echo Shapes_Control_obj_lem_stub
	@echo Shapes_Control_obj_stub
	@echo Shapes_Control_obj_svnt
	@echo Shapes_ShapeType_msg_stub
	@echo Shapes_defn_idl_gen
	@echo Shapes_defn_stub
