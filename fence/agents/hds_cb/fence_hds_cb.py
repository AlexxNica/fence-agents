#!/usr/bin/python

#####
##
## The Following Agent Has Been Tested On:
##
##  Model                 Modle/Firmware
## +--------------------+---------------------------+
## (1) Main application	  CB2000/A0300-E-6617
##
#####

import sys, re, pexpect, exceptions
sys.path.append("@FENCEAGENTSLIBDIR@")
from fencing import *

#BEGIN_VERSION_GENERATION
RELEASE_VERSION="New Compute Blade 2000 Agent - test release on steroids"
REDHAT_COPYRIGHT=""
BUILD_DATE="November, 2012"
#END_VERSION_GENERATION

def get_power_status(conn, options):
	try:
		#### Maybe should put a conn.log_expect here to make sure
		#### we have properly entered into the main menu
		conn.sendline("S")	# Enter System Command Mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("PC")	# Enter partition control
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		result = {}
		# Status can now be obtained from the output of the PC
		# command. Line looks like the following:
		# "P Power        Condition     LID lamp Mode  Auto power on"
		# "0 On           Normal        Off      Basic Synchronized"
		# "1 On           Normal        Off      Basic Synchronized"
		for line in conn.before.splitlines():
			# populate the relevant fields based on regex
			partition=re.search("^([0-9]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+).*$", line)
			if( partition != None):
				# find the blade number defined in args
				if( partition.group(1) == options["-n"] ):
					result = partition.group(2).lower()
		# We must make sure we go back to the main menu as the
		# status is checked before any fencing operations are
		# executed. We could in theory save some time by staying in
		# the partition control, but the logic is a little cleaner
		# this way.
		conn.sendline("Q")	# Back to system command mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("EX")	# Back to system console main menu
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		return result
	except pexpect.EOF:
		fail(EC_CONNECTION_LOST)
	except pexpect.TIMEOUT:
		fail(EC_TIMED_OUT)

	return status.lower().strip()

def set_power_status(conn, options):
	action = {
		'on' : "P",
		'off': "F",
		'reboot' : "H",
	}[options["-o"]]
	

	try:
		conn.sendline("S")	# Enter System Command Mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("PC")	# Enter partition control
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline("P")	# Enter power control menu
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline(action)	# Execute action from array above
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline(options["-n"]) # Select blade number from args
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline("Y")	# Confirm action
		i = conn.log_expect(options, "Hit enter key.", int(options["-Y"]))
		conn.sendline("")	# Press the any key
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline("Q")	# Quit back to partition control
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		conn.sendline("Q")	# Quit back to system command mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("EX")	# Quit back to system console menu
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
	except pexpect.EOF:
		fail(EC_CONNECTION_LOST)
	except pexpect.TIMEOUT:
		fail(EC_TIMED_OUT)

def get_blades_list(conn, options):
	outlets = { }
	try:
		conn.sendline("S")	# Enter System Command Mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("PC")	# Enter partition control
		i = conn.log_expect(options, "\) :", int(options["-Y"]))
		result = {}
		# Status can now be obtained from the output of the PC
		# command. Line looks like the following:
		# "P Power        Condition     LID lamp Mode  Auto power on"
		# "0 On           Normal        Off      Basic Synchronized"
		# "1 On           Normal        Off      Basic Synchronized"
		for line in conn.before.splitlines():
			partition=re.search("^([0-9]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+).*$", line)
			if( partition != None):
				outlets[partition.group(1)] = (partition.group(2), "")	
		conn.sendline("Q")	# Quit back to system command mode
		i = conn.log_expect(options, "SVP>", int(options["-Y"]))
		conn.sendline("EX")	# Quit back to system console menu
		i = conn.log_expect(options, "\) :", int(options["-Y"]))

	except pexpect.EOF:
		fail(EC_CONNECTION_LOST)
	except pexpect.TIMEOUT:
		fail(EC_TIMED_OUT)

	return outlets

def main():
	device_opt = [  "help", "version", "agent", "quiet", "verbose", "debug",
			"action", "ipaddr", "login", "passwd", "passwd_script",
			"cmd_prompt", "secure", "port", "identity_file", "separator",
			"inet4_only", "inet6_only", "ipport",
			"power_timeout", "shell_timeout", "login_timeout", "power_wait", "missing_as_off" ]

	atexit.register(atexit_handler)

	all_opt["power_wait"]["default"] = "5"
	all_opt["cmd_prompt"]["default"] = "\) :"

	options = check_input(device_opt, process_input(device_opt))

	docs = { }        
	docs["shortdesc"] = "Fence agent for Hitachi Compute Blade systems"
	docs["longdesc"] = "fence_hds_cb is an I/O Fencing agent \
which can be used with Hitachi Compute Blades with recent enough firmware that \
includes telnet support."
	docs["vendorurl"] = "http://www.hds.com"
	show_docs(options, docs)
	
	##
	## Operate the fencing device
	######
	conn = fence_login(options)
	result = fence_action(conn, options, set_power_status, get_power_status, get_blades_list)

	##
	## Logout from system
	######
	try:
		conn.sendline("X")
		conn.close()
	except exceptions.OSError:
		pass
	except pexpect.ExceptionPexpect:
		pass
	
	sys.exit(result)

if __name__ == "__main__":
	main()
