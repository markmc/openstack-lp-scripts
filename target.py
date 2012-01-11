
#
# Target a set of bugs to a given milestone and set to FixCommitted
#
#  python target.py nova diablo 2011.3.1 $(cat buglist.txt)
#
# See http://wiki.openstack.org/StableBranchRelease
#

import argparse
import sys

from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Target a bug to a milestone")

parser.add_argument('project', help='the project to act on')
parser.add_argument('series', help='the series to nominate the bug for')
parser.add_argument('milestone', help='the milestone to target the bug to')
parser.add_argument('bugs', metavar='BUG', nargs='+',
                    help='A bug number to query')

args = parser.parse_args()

print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

project = launchpad.projects[args.project]
milestone = project.getMilestone(name=args.milestone)
tgt = args.project + '/' + args.series

for bugno in args.bugs:
    b = launchpad.bugs[bugno]

    tasks = filter(lambda t: t.bug_target_name == tgt, b.bug_tasks_collection)

    if not tasks:
        print >>sys.stderr, "No %s task for bug #%s" % (tgt, bugno)
        sys.exit(1)
    elif len(tasks) != 1:
        print >>sys.stderr, "Huh? Multiple %s tasks for bug #%s" % (tgt, bugno)
        sys.exit(1)

    print "Setting milestone=%s and status=FixCommitted on %s/%s" % \
        (args.milestone, tgt, bugno)

    t = tasks[0]
    t.milestone = milestone
    t.status = 'Fix Committed'
    t.lp_save()
