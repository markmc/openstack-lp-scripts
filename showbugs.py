
#
# Show description and merges/targets for a bunch of bugs e.g.
#
#  python showbugs.py $(cat buglist.txt)
#
# Useful for checking that a set of bugs have actually been
# merged into a branch or targeted at the appropriate series
#
# See http://wiki.openstack.org/StableBranchRelease
#

import argparse
import string
import sys

from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Nominate a bug for series")

parser.add_argument('bugs', metavar='BUG', nargs='+',
                    help='A bug number to query')

args = parser.parse_args()

print >>sys.stderr, "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

for bugno in args.bugs:
    bug = launchpad.bugs[bugno]

    notes = []
    for msg in bug.messages_collection:
        if not msg.subject.startswith("Fix merged to "):
            continue
        notes.append(msg.subject[14:])

    if not notes:
        notes = [task.bug_target_name for task in bug.bug_tasks]

    targets = [task.milestone.name for task in bug.bug_tasks if task.milestone]

    print "%s %s [%s] [%s]" % (bugno, bug.title,
                               string.join(notes, ','),
                               string.join(targets, ','))

