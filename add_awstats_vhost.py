# ---
# python script for adding awstats conf files
# ---

# imports
import sys, argparse
import re
import os

# get args
parser = argparse.ArgumentParser(description='Add a vhost or all enabled vhosts to awstats.',formatter_class=argparse.ArgumentDefaultsHelpFormatter)
group = parser.add_mutually_exclusive_group()
group.add_argument('-s','--site',
        metavar='<vhost>',
		type=str,
		help='Add a single vhost')
group.add_argument('-a','--all',
        help='Add all vhosts',
		action='store_true')
parser.add_argument('-l','--logdir',
        metavar='<logdir>',
		type=str,
		help='Defines the log directory of an other web instance. This is usefull if you have vhosts that are loadbalanced on different servers.',
		default='/home/logs/apache2_remy2/')
parser.add_argument('-d','--dir',
        metavar='<dir>',
		type=str,
		help='Defines the vhost directory.',
		default='/etc/apache2/sites-enabled/')
parser.add_argument('-j','--jaws',
        metavar='<jawsdir>',
		type=str,
		help='Defines the jaws configuration directory.',
		default='/home/sites_web/002-awstats/conf.d/')
parser.add_argument('-w','--aws',
        metavar='<awsdir>',
		type=str,
		help='Defines the awstats configuration directory.',
		default='/etc/awstats/')
args = parser.parse_args()

# functions
# --> checks for log files (web1 and web2)
def check_log(custom_log,vhost):
    """
    @params: custom_log, the full path of the log file; vhost, the vhost we are working on.
    returns: boolean
    Info: checks for the same log in the log directory (can be specified by the -l option). 
          This is for "checking" if a vhost is loadbalanced or not.
    """
    # split
    customlog_basename = os.path.basename(custom_log)
    logfile = custom_log.split('/')

    # check
    web2logfiles = args.logdir + logfile[-2] + '/' + customlog_basename

    if os.path.isfile(web2logfiles) and os.path.isfile(custom_log):
        return 1

# --> creates jaws php conf file
def jaws_conf_file(vhost):
    # php code!
    phpline = '''<?php $aConfig["{revhost}"] = array(
    "statspath" => "/var/lib/awstats/",
    "updatepath" => "/usr/lib/cgi-bin/awstats.pl/",
    "siteurl" => "http://{vvhost}",
    "sitename" => "{vvhost}",
    "theme" => "default",
    "fadespeed" => 250,
    "password" => "my-1st-password",
    "includes" => "",
    "language" => "en-gb") ;?>
'''.format(revhost=re.sub('\.','_',vhost),vvhost=vhost) 

    #rite file
    jawsfile = args.jaws + re.sub('\.','_',vhost) + '.php'
    with open(jawsfile,'w') as jfile:
        jfile.write(phpline)

# --> creates awstats conf file
def awstats_conf_file(islb,servername,customlog):
    # stuff
    mergetool = '/usr/share/awstats/tools/logresolvemerge.pl '
    awsfilename = '%sawstats.%s.conf' % (args.aws, re.sub('\.','_',servername))

    if islb:
        lblogfile = ' %s%s/%s' % (args.logdir,customlog.split('/')[-2],os.path.basename(customlog))
        mergelog = '%s%s*%s* |' % (mergetool,customlog,lblogfile)

        # confline
        confline = '''LogFile="{mergelog}"
SiteDomain="{servername}"
Include "/etc/awstats/default_vars"
'''.format(mergelog=mergelog,servername=servername)

    else:
        confline = '''LogFile="{mergetool} {customlog}* |"
SiteDomain="{servername}"
Include "/etc/awstats/default_vars"
'''.format(mergetool=mergetool,customlog=customlog,servername=servername)

    # writing conf file
    with open(awsfilename,'w') as awsconffile:
        awsconffile.write(confline)
    # calling jawsfile
    jaws_conf_file(servername)

# --> adds a single vhost
def add_vhost(vhost):
    print "adding vhosts from file : %s" % vhost

    vhosts_vars = []
    # parsing vhost file
    with open(args.dir+vhost) as vhostfile:
        servername = customlog = None
        for line in vhostfile:
        # lets lookf for all ServerNames and CustomLogs
            if re.search("^\s*[#]|^#",line): continue

            if re.search("^\s*</Virtual",line):
                vhosts_vars.append({'ServerName': servername, 'CustomLog': customlog})           
                servername = customlog = None
                continue
            
            elif re.search("ServerName",line):
                servername = line.split()[1]
            elif re.search("CustomLog",line):
                customlog = line.split()[1]
    
    # lets do other stuff
    for vhost_info in vhosts_vars:
        custom_log = vhost_info.get('CustomLog')
        server_name = vhost_info.get('ServerName')

        if not custom_log or not server_name:
            print 'No CustomLog found for vhost %s' % server_name
            continue

        if check_log(custom_log, vhost):
            islb=True
        else:
            islb=False

        print 'adding vhost %s ' % server_name
        awstats_conf_file(islb=islb,
                          servername=server_name,
                          customlog=custom_log)

# --> adds all vhosts
def add_all():
    vhostdir = args.dir
    out = os.listdir(vhostdir)
    for l in out:
        if not l.startswith("00") \
        and not l.startswith("php") and not l.startswith("preprod") and not l.endswith("-preprod") and not l.endswith("-preprod2"):
            add_vhost(l)

# main
if args.site:
    add_vhost(args.site)
elif args.all:
    add_all()
else:
    parser.print_help()
