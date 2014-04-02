#!/usr/bin/python

import sys, re, pexpect, exceptions
sys.path.append("@FENCEAGENTSLIBDIR@")
from fencing import *

#BEGIN_VERSION_GENERATION
RELEASE_VERSION=""
REDHAT_COPYRIGHT=""
BUILD_DATE=""
#END_VERSION_GENERATION

# --plug should include path to the outlet # such as port 1:
# /system1/outlet1

def get_power_status(conn, options):
	conn.send_eol("show -d properties=powerState %s" % options["--plug"])
	re_status = re.compile(".*powerState is [12].*")
	conn.log_expect(options, re_status, int(options["--shell-timeout"]))
	status = {
		#"0" : "off",
		"1" : "on",
		"2" : "off",
	}[conn.after.split()[2]]

	return status

def set_power_status(conn, options):
	action = {
		"on" : "on",
		"off" : "off",
	}[options["--action"]]

	conn.send_eol("set %s powerState=%s" % (options["--plug"], action))

def main():
	device_opt = [ "ipaddr", "login", "passwd", "port" ]

	atexit.register(atexit_handler)

	opt = process_input(device_opt)

	all_opt["ipport"]["default"] = "23"

	opt["eol"] = "\r\n"
	options = check_input(device_opt, opt)

	docs = { }
	docs["shortdesc"] = "I/O Fencing agent for Raritan Dominion PX"
	docs["longdesc"] = "fence_raritan is an I/O Fencing agent which can be \
used with the Raritan DPXS12-20 Power Distribution Unit. It logs into \
device via telnet and reboots a specified outlet. Lengthy telnet connections \
should be avoided while a GFS cluster is running because the connection will \
block any necessary fencing actions."
	docs["vendorurl"] = "http://www.raritan.com/"
	show_docs(options, docs)

	#  add support also for delay before login which is very useful for 2-node clusters
	if options["--action"] in ["off", "reboot"]:
                time.sleep(int(options["--delay"]))

	##
	## Operate the fencing device
	## We can not use fence_login(), username and passwd are sent on one line
	####
	try:
		conn = fspawn(options, TELNET_PATH)
		conn.send("set binary\n")
		conn.send("open %s -%s\n"%(options["--ip"], options["--ipport"]))
		screen = conn.read_nonblocking(size=100, timeout=int(options["--shell-timeout"]))
		conn.log_expect(options, "Login.*", int(options["--shell-timeout"]))
		conn.send_eol("%s" % (options["--username"]))
		conn.log_expect(options, "Password.*", int(options["--shell-timeout"]))
		conn.send_eol("%s" % (options["--password"]))
		conn.log_expect(options, "clp.*", int(options["--shell-timeout"]))
	except pexpect.EOF:
		fail(EC_LOGIN_DENIED)
	except pexpect.TIMEOUT:
		fail(EC_LOGIN_DENIED)
	result = fence_action(conn, options, set_power_status, get_power_status)

	##
	## Logout from system
	##
	## In some special unspecified cases it is possible that
	## connection will be closed before we run close(). This is not
	## a problem because everything is checked before.
	######
	try:
		conn.send("exit\n")
		conn.close()
	except:
		pass

	sys.exit(result)

if __name__ == "__main__":
	main()
