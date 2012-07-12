#!/usr/bin/perl

use Getopt::Std;

my $ME = $0;

END {
  defined fileno STDOUT or return;
  close STDOUT and return;
  warn "$ME: failed to close standard output: $!\n";
  $? ||= 1;
}

# Get the program name from $0 and strip directory names
$_=$0;
s/.*\///;
my $pname = $_;

$opt_o = 'reset';        # Default fence action
$opt_r = 'rpower';        # Default fence action

# WARNING!! Do not add code bewteen "#BEGIN_VERSION_GENERATION" and 
# "#END_VERSION_GENERATION"  It is generated by the Makefile

#BEGIN_VERSION_GENERATION
$RELEASE_VERSION="";
$REDHAT_COPYRIGHT="";
$BUILD_DATE="";
#END_VERSION_GENERATION


sub usage
{
    print "Usage:\n";
    print "\n";
    print "$pname [options]\n";
    print "\n";
    print "Options:\n";
    print "  -h               usage\n";
    print "  -n <name>        nodename\n";
    print "  -o <string>      Action: on, off, reset (default), status or metadata\n";
    print "  -r <rpower>      rpower command\n";
    print "  -q               quiet mode\n";
    print "  -V               version\n";

    exit 0;
}

sub fail
{
  ($msg) = @_;
  print $msg."\n" unless defined $opt_q;
  $t->close if defined $t;
  exit 1;
}

sub fail_usage
{
  ($msg)=@_;
  print STDERR $msg."\n" if $msg;
  print STDERR "Please use '-h' for usage.\n";
  exit 1;
}

sub version
{
  print "$pname $RELEASE_VERSION $BUILD_DATE\n";
  print "$REDHAT_COPYRIGHT\n" if ( $REDHAT_COPYRIGHT );

  exit 0;
}

sub print_metadata
{
print '<?xml version="1.0" ?>
<resource-agent name="fence_xcat" shortdesc="I/O Fencing agent for xcat environments" >
<longdesc>
fence_xcat is a wrapper to the rpower(1) command that is distributed with the xCAT project available at http://www.xcat.org. Use of fence_xcat requires that xcat has already been properly configured for your environment. Refer to xCAT(1) for more information on configuring xCAT.

NOTE: It is recommended that fence_bladecenter(8) is used instead of fence_xcat if the bladecenter firmware supports telnet.  This interface is much cleaner and easier to setup.
</longdesc>
<vendor-url>http://www.xcat.org</vendor-url>
<parameters>
        <parameter name="action" unique="1" required="1">
                <getopt mixed="-o &lt;action&gt;" />
                <content type="string" default="restart" />
                <shortdesc lang="en">Fencing Action</shortdesc>
        </parameter>
        <parameter name="nodename" unique="1" required="1">
                <getopt mixed="-n &lt;nodename&gt;" />
                <content type="string"  />
                <shortdesc lang="en">The nodename as defined in nodelist.tab of the xCAT setup.</shortdesc>
        </parameter>
        <parameter name="rpower" unique="1" required="0">
                <getopt mixed="-r &lt;rpower&gt;" />
                <content type="string"  />
                <shortdesc lang="en">The path to the rpower binary.</shortdesc>
        </parameter>
        <parameter name="help" unique="1" required="0">
                <getopt mixed="-h" />           
                <content type="string"  />
                <shortdesc lang="en">Display help and exit</shortdesc>                    
        </parameter>
</parameters>
<actions>
        <action name="on" />
        <action name="off" />
        <action name="status" />
        <action name="metadata" />
</actions>
</resource-agent>
';
}


sub get_options_stdin
{
    my $opt;
    my $line = 0;
    while( defined($in = <>) )
    {
        $_ = $in;
        chomp;

	# strip leading and trailing whitespace
        s/^\s*//;
        s/\s*$//;

	# skip comments
        next if /^#/;

        $line+=1;
        $opt=$_;
        next unless $opt;

        ($name,$val)=split /\s*=\s*/, $opt;

        if ( $name eq "" )
        {  
           print STDERR "parse error: illegal name in option $line\n";
           exit 2;
	}
	
        # DO NOTHING -- this field is used by fenced
	elsif ($name eq "agent" ) { } 

        elsif ($name eq "action" )
        {
            $opt_o = $val;
        }
	elsif ($name eq "nodename" ) 
	{
            $opt_n = $val;
        } 
	elsif ($name eq "rpower" ) 
	{
            $opt_r = $val;
        } 

    }
}

######################################################################33
# MAIN

if (@ARGV > 0) {
   getopts("hn:o:r:qV") || fail_usage ;

   usage if defined $opt_h;
   version if defined $opt_V;

   fail_usage "Unknown parameter." if (@ARGV > 0);

   if ((defined $opt_o) && ($opt_o =~ /metadata/i)) {
     print_metadata();
     exit 0;
   }

   fail_usage "No '-n' flag specified." unless defined $opt_n;
   $opt_o=lc($opt_o);
   fail_usage "Unrecognised action '$opt_o' for '-o' flag"
      unless $opt_o =~ /^(on|off|reset|stat|status)$/;

} else {
   get_options_stdin();

   if ((defined $opt_o) && ($opt_o =~ /metadata/i)) {
     print_metadata();
     exit 0;
   }
   
   fail "failed: no plug number" unless defined $opt_n;
   $opt_o=lc($opt_o);
   fail "failed: unrecognised action: $opt_o"
      unless $opt_o =~ /^(on|off|reset|stat|status)$/;
}

pipe (RDR,WTR);

if ( $pid=fork() == 0 )
{
   close RDR;

   open STDOUT, ">&WTR";
   exec "$opt_r $opt_n $opt_o" or die "failed to exec \"$opt_r\"\n";
}

close WTR;

wait;

if ( $? != 0 )
{
   die "failed: rpower error: exit $?\n"
}

$found=0;
$status="";
while (<RDR>)
{
   chomp;

   if ( $_ =~ /^(\S+): (\S+)$/)
   {
      if ($opt_n eq $1) 
      {
         $status = $2;

         if (($opt_o eq $2) || ($opt_o =~ /stat/i) || ($opt_o =~ /status/i))
         {
            $found=1;
            last;
         }
      }
   }
}

print (($found ? "success":"failed") . ": $opt_n $status\n")
   unless defined $opt_q;

exit ($found ? 0 : 1 );









