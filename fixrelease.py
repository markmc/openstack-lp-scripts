
#
# Target a bug to a milestone and mark it as Fix Released
#
#  python fixrelease.py openstack-common 2012.1 $(cat buglist.txt)
#

import argparse
from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Process FixCommitted bugs"
                                 " at release time")
parser.add_argument('project')
parser.add_argument('milestone')
parser.add_argument('bugs', metavar='BUG', nargs='+')

args = parser.parse_args()

# Connect to Launchpad
print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

# Retrieve FixCommitted bugs
print "Retrieving project..."
project = launchpad.projects[args.project]
milestone = project.getMilestone(name=args.milestone)

for bugno in args.bugs:
    b = launchpad.bugs[bugno]

    tasks = filter(lambda t: t.target.name == args.project, b.bug_tasks_collection)

    if not tasks:
        print >>sys.stderr, "No %s task for bug #%s" % (args.project, bugno)
        sys.exit(1)
    elif len(tasks) != 1:
        print >>sys.stderr, "Huh? Multiple %s tasks for bug #%s" % (args.project, bugno)
        sys.exit(1)

    print "Setting milestone=%s and status=FixReleased on %s/%s" % \
        (args.milestone, args.project, bugno)

    t = tasks[0]
    t.milestone = milestone
    t.status = 'Fix Released'
    t.lp_save()
