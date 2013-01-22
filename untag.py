
#
# Remove a tag from a set of bugs
#
#  python untag.py in-stable-folsom $(cat buglist.txt)
#

import argparse
import string
import sys

from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Remove a tag from a bug")

parser.add_argument('tag', help='the tag to remove')
parser.add_argument('bugs', metavar='BUG', nargs='+',
                    help='A bug number to query')

args = parser.parse_args()

print >>sys.stderr, "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

for bugno in args.bugs:
    bug = launchpad.bugs[bugno]
    tags = bug.tags[:]
    tags.remove(args.tag)
    bug.tags = tags
    bug.lp_save()
