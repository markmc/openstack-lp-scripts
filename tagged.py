
#
# Search for bugs with a tag
#
#  python tagged.py nova in-stable-folsom
#

import argparse
import string
import sys

from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Search for bugs with a tag")

parser.add_argument('project', help='the project to act on')
parser.add_argument('tag', help='the tag to search for')

args = parser.parse_args()

print >>sys.stderr, "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

proj = launchpad.projects[args.project]

bugtasks = proj.searchTasks(tags=args.tag, status=['Fix Released', 'Fix Committed', 'In Progress', 'Confirmed', 'Triaged', 'New'])
for b in bugtasks:
    print b.bug.id
