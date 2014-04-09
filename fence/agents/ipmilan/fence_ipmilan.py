#!/usr/bin/python

import sys, shlex, subprocess, re, os
import logging
import atexit
from pipes import quote
sys.path.append("@FENCEAGENTSLIBDIR@")
from fencing import *
from fencing import SUDO_PATH, LOG_MODE_VERBOSE, fail_usage, is_executable

#BEGIN_VERSION_GENERATION
RELEASE_VERSION=""
REDHAT_COPYRIGHT=""
BUILD_DATE=""
#END_VERSION_GENERATION

def get_power_status(_, options):
	cmd = create_command(options, "status")

	try:
		logging.info("Executing: %s\n" % cmd)
		process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError:
		fail_usage("Ipmitool not found or not accessible")

	process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))

	match = re.search('[Cc]hassis [Pp]ower is [\\s]*([a-zA-Z]{2,3})', str(out))
	status = match.group(1) if match else None

	return status

def set_power_status(_, options):
	cmd = create_command(options, options["--action"])

	try:
		logging.debug("Executing: %s\n" % cmd)
		process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError:
		fail_usage("Ipmitool not found or not accessible")

	process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))

	return

def reboot_cycle(_, options):
	cmd = create_command(options, "cycle")

	try:
		logging.debug("Executing: %s\n" % cmd)
		process = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	except OSError:
		fail_usage("Ipmitool not found or not accessible")

	process.wait()

	out = process.communicate()
	process.stdout.close()
	process.stderr.close()
	logging.debug("%s\n" % str(out))

	return bool(re.search('chassis power control: cycle', str(out).lower()))

def create_command(options, action):
	cmd = options["--ipmitool-path"]

	# --lanplus / -L
	if options.has_key("--lanplus") and options["--lanplus"] in ["", "1"]:
		cmd += " -I lanplus"
	else:
		cmd += " -I lan"
	# --ip / -a
	cmd += " -H " + options["--ip"]

	# --username / -l
	if options.has_key("--username") and len(options["--username"]) != 0:
		cmd += " -U " + quote(options["--username"])

	# --auth / -A
	if options.has_key("--auth"):
		cmd += " -A " + options["--auth"]

	# --password / -p
	if options.has_key("--password"):
		cmd += " -P " + quote(options["--password"])

	# --cipher / -C
	cmd += " -C " + options["--cipher"]

	# --port / -n
	if options.has_key("--ipport"):
		cmd += " -p " + options["--ipport"]

	if options.has_key("--privlvl"):
		cmd += " -L " + options["--privlvl"]

	# --action / -o
	cmd += " chassis power " + action

	# --use-sudo / -d
	if options.has_key("--use-sudo"):
		cmd = SUDO_PATH + " " + cmd

	return cmd

def define_new_opts():
	all_opt["lanplus"] = {
		"getopt" : "P",
		"longopt" : "lanplus",
		"help" : "-P, --lanplus                  Use Lanplus to improve security of connection",
		"required" : "0",
		"default" : "0",
		"shortdesc" : "Use Lanplus to improve security of connection",
		"order": 1
	}
	all_opt["auth"] = {
		"getopt" : "A:",
		"longopt" : "auth",
		"help" : "-A, --auth=[auth]              IPMI Lan Auth type (md5|password|none)",
		"required" : "0",
		"shortdesc" : "IPMI Lan Auth type.",
		"choices" : ["md5", "password", "none"],
		"order": 1
	}
	all_opt["cipher"] = {
		"getopt" : "C:",
		"longopt" : "cipher",
		"help" : "-C, --cipher=[cipher]          Ciphersuite to use (same as ipmitool -C parameter)",
		"required" : "0",
		"shortdesc" : "Ciphersuite to use (same as ipmitool -C parameter)",
		"default" : "0",
		"order": 1
	}
	all_opt["privlvl"] = {
		"getopt" : "L:",
		"longopt" : "privlvl",
		"help" : "-L, --privlvl=[level]          "
				"Privilege level on IPMI device (callback|user|operator|administrator)",
		"required" : "0",
		"shortdesc" : "Privilege level on IPMI device",
		"default" : "administrator",
		"choices" : ["callback", "user", "operator", "administrator"],
		"order": 1
	}
	all_opt["ipmitool_path"] = {
		"getopt" : "i:",
		"longopt" : "ipmitool-path",
		"help" : "--ipmitool-path=[path]         Path to ipmitool binary",
		"required" : "0",
		"shortdesc" : "Path to ipmitool binary",
		"default" : "@IPMITOOL_PATH@",
		"order": 200
	}

def main():
	atexit.register(atexit_handler)

	device_opt = ["ipaddr", "login", "no_login", "no_password", "passwd",
		"lanplus", "auth", "cipher", "privlvl", "sudo", "ipmitool_path", "method"]
	define_new_opts()

	if os.path.basename(sys.argv[0]) == "fence_ilo3":
		all_opt["power_wait"]["default"] = "4"
		all_opt["method"]["default"] = "cycle"
		all_opt["lanplus"]["default"] = "1"
	elif os.path.basename(sys.argv[0]) == "fence_ilo4":
		all_opt["lanplus"]["default"] = "1"

	all_opt["ipport"]["default"] = "623"

	options = check_input(device_opt, process_input(device_opt))

	docs = { }
	docs["shortdesc"] = "Fence agent for IPMI"
	docs["longdesc"] = "fence_ipmilan is an I/O Fencing agent\
which can be used with machines controlled by IPMI.\
This agent calls support software ipmitool (http://ipmitool.sf.net/)."
	docs["vendorurl"] = ""
	docs["symlink"] = [("fence_ilo3", "Fence agent for HP iLO3"),
		("fence_ilo4", "Fence agent for HP iLO4"),
		("fence_imm", "Fence agent for IBM Integrated Management Module"),
		("fence_idrac", "Fence agent for Dell iDRAC")]
	show_docs(options, docs)

	if not is_executable(options["--ipmitool-path"]):
		fail_usage("Ipmitool not found or not accessible")

	result = fence_action(None, options, set_power_status, get_power_status, None, reboot_cycle)
	sys.exit(result)

if __name__ == "__main__":
	main()
