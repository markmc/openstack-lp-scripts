import argparse
from launchpadlib.launchpad import Launchpad

# Parameters
parser = argparse.ArgumentParser(description="Process FixCommitted bugs"
                                 " at release time")
parser.add_argument('projectname', help='the project to act on')
parser.add_argument('--milestone',
                    help='include bugs targeted to the specified milestone')
parser.add_argument('--onlymilestone',
                    help='only include bugs targeted to specified milestone')
parser.add_argument('--check', action='store_true',
                    help='ACTION: check merge revnos')
parser.add_argument('--between', type=int, nargs=2,
                    help='ACTION: check merge revnos')
parser.add_argument('--settarget',
                    help='ACTION: set the milestone to specified target')
parser.add_argument('--fixrelease', action='store_true',
                    help='ACTION: mark bugs fix released')
parser.add_argument('exceptions', type=int, nargs='*', help='bugs to ignore')

args = parser.parse_args()

if args.settarget:
    milestonelink = "https://api.launchpad.net/1.0/%s/+milestone/%s" \
                % (args.projectname, args.settarget)

# Connect to Launchpad
print "Connecting to Launchpad..."
launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')

# Retrieve FixCommitted bugs
print "Retrieving project..."
proj = launchpad.projects[args.projectname]
#series = proj.getSeries(name='folsom')
#bugtasks = series.searchTasks(status='Fix Committed', omit_targeted=False)

bugtasks = proj.searchTasks(status='Fix Committed')

# Process bugs
for b in bugtasks:
    bug = b.bug
    if args.onlymilestone:
        if b.milestone:
            if b.milestone.name != args.onlymilestone:
                continue
        else:
            continue
    else:
        if b.milestone and b.milestone.name != args.milestone:
            continue
    print bug.id,
    if bug.id in args.exceptions:
        print " - excepted"
        continue
    if args.check:
        try:
            merge_prop = bug.linked_branches[0].branch.landing_targets[0]
            print merge_prop.merged_revno,
            if args.between:
                if not (args.between[0] <= merge_prop.merged_revno
                        <= args.between[1]):
                    print 'https://launchpad.net/bugs/' + str(bug.id),
        except Exception, e:
            print '? https://launchpad.net/bugs/' + str(bug.id),
    if args.settarget:
        b.milestone = milestonelink
        print " - milestoned",
    if args.fixrelease:
        print " - fixreleased",
        b.status = 'Fix Released'
    b.lp_save()
    print
