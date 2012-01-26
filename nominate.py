
#
# Nominate a set of bugs for a given series
#
#  python nominate.py nova diablo $(cat buglist.txt)
#
# See http://wiki.openstack.org/StableBranchRelease
#

import argparse

from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Nominate a bug for series")

parser.add_argument('project', help='the project to act on')
parser.add_argument('series', help='the series to nominate the bug for')
parser.add_argument('bugs', metavar='BUG', nargs='+',
                    help='A bug number to query')

args = parser.parse_args()

print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

project = launchpad.projects[args.project]
series = project.getSeries(name=args.series)

for bugno in args.bugs:
    bug = launchpad.bugs[bugno]

    print "Nominating #%s for %s series on %s" % \
        (bugno, args.project, args.series)
    bug.addNomination(target=series)

    print "Approving the nomination"
    bug.getNominationFor(target=series).approve()
