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
        metavar='<vhost>',type=str,help='add a single vhost')
group.add_argument('-a','--all',
        help='add all vhosts',action='store_true')
parser.add_argument('-d','--dir',
        metavar='<dir>',type=str,help='define vhost directory',default='/etc/apache2/sites-enabled/')
parser.add_argument('-l','--logdir',
        metavar='<logdir>',type=str,help='define log directory',default='/home/logs/apache2/')
parser.add_argument('-j','--jaws',
        metavar='<jawsdir>',type=str,help='define jaws conf.d directory',default='/home/sites_web/002-awstats/')
args = parser.parse_args()

# functions
# --> checks for log files (web1 and web2)
def check_log(logfilearg,vhost):
    # split
    logfile = logfilearg.split('/')

    # check
    web2logfiles = '/home/logs/apache2_remy2/' + logfile[-2] + '/' + logfile[-1]

    if os.path.isfile(web2logfiles) and os.path.isfile(logfilearg):
        return 1

# --> creates jaws php conf file
def jaws_conf_file(vhost):
    jaws_dir = '/home/sites_web/002-awstats/conf.d/'

# --> creates awstats conf file
def awstats_conf_file(islb,servername,customlog):
    # merge tool
    mergetool = "/usr/share/awstats/tools/logresolvemerge.pl "
    
    if islb:
        web2logfiles = ' /home/logs/apache2_remy2/' + customlog.split('/')[-2] + '/' + customlog.split('/')[-1]
        mergelog = mergetool + customlog + web2logfiles + ' |'
        print 'LogFile="',mergelog,'"'
        print 'SiteDomain="',servername,'"'
    else:
        print 'LogFle="',customlog,'"'
        print 'Servername="',servername,'"'

# --> adds a single vhost
def add_vhost(vhost):
    print "adding vhosts from file : %s" % vhost

    vhosts_vars = []
    # parsing vhost file
    with  open(vhostdir+vhost) as vhostfile:
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
    for dico in vhosts_vars:
        if dico['CustomLog'] and dico['ServerName']:
            if check_log(dico['CustomLog'],vhost):
                print 'adding vhost ',dico['ServerName']
                awstats_conf_file(1,dico['ServerName'],dico['CustomLog'])
            else:
                print 'adding vhost ',dico['ServerName']
                awstats_conf_file(0,dico['ServerName'],dico['CustomLog'])
        else:
            print 'No CustomLog found for vhost ', dico['ServerName']

# --> adds all vhosts
def add_all():
    out = os.listdir(vhostdir)
    for l in out:
        if not l.startswith("00") and not l.startswith("php") and not l.startswith("preprod") and not l.endswith("-preprod") and not l.endswith("-preprod2"):
            add_vhost(l)

# main
if args.dir:
    vhostdir = args.dir
elif args.logdir:
    logdir = args.logdir
else:
    logdir = "/home/logs/apache2/"
    #vhostdir = "/etc/apache2/sites-enabled/"
    vhostdir = "/root/scripts/remy/"

if args.site:
    add_vhost(args.site)
elif args.all:
    add_all()
else:
    parser.print_help()
