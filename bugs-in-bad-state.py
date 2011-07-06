import sys
import datetime
from launchpadlib.launchpad import Launchpad


def erroradd(bb, i, s):
    i = str(i)
    if not (i in bb):
        bb[i] = ''
    bb[i] = bb[i] + s + ', '


if len(sys.argv) != 2:
    print "Usage:\n\t%s projectname" % sys.argv[0]
    sys.exit(1)

projectname = sys.argv[1]

print "Logging in..."

cachedir = '/tmp/launchpadlib-cache'
launchpad = Launchpad.login_anonymously('openstack-lp-scripts', 'production',
                                        cachedir, version='devel')

statuses = ['New', 'Incomplete', 'Confirmed', 'Triaged', 'In Progress',
            'Fix Committed']

print "Retrieving project..."

proj = launchpad.projects[projectname]

print "Filtering open bugs..."

prio1bugs = {}
prio2bugs = {}

bugs = proj.searchTasks(status=statuses[0:5])
for b in bugs:
    # Confirmed but without importance set
    if b.status in statuses[2:5] and b.importance == 'Undecided':
        erroradd(prio1bugs, b.bug.id, 'Importance missing')
    # In progress but without assignee
    if b.status == statuses[4] and b.assignee is None:
        erroradd(prio1bugs, b.bug.id, 'Assignee missing')
    # Been assigned forever
    if b.assignee:
        d = b.bug.date_last_updated
        diff = datetime.date.today() - datetime.date(d.year, d.month, d.day)
        if diff.days > 60 and b.status == statuses[4]:
            erroradd(prio2bugs, b.bug.id, 'Old inprogress assignee')
        else:
            if diff.days > 30 and b.status != statuses[4]:
                erroradd(prio2bugs, b.bug.id, 'Old abusive assignee')

print "Filtering incomplete bugs..."

# Incomplete but with an answer
bugs = proj.searchTasks(status='Incomplete (with response)')
for b in bugs:
    if b.bug.messages[b.bug.message_count - 1].owner.name != 'ttx':
        erroradd(prio2bugs, b.bug.id, 'Answered')

print "Filtering bugs with branches..."

bugs = proj.searchTasks(linked_branches='Show only Bugs with linked Branches',
                        status=statuses[0:5])
for b in bugs:
    # Not in progress but with a branch attached
    if b.status in ['New', 'Confirmed', 'Triaged']:
        erroradd(prio1bugs, b.bug.id, 'Has a branch')
    # Not fix committed, though branch was merged
    for l in b.bug.linked_branches:
        if l.branch.lifecycle_status == "Merged":
            erroradd(prio1bugs, b.bug.id, 'Branch merged!')
            break

# Display results
print "====== Bugs with PRIO1 incorrect status in %s ======" % projectname
for i in prio1bugs.keys():
    print "  https://bugs.launchpad.net/%s/+bug/%s : %s" % \
        (projectname, i, prio1bugs[i][:-2])
print "====== Bugs with PRIO2 incorrect status in %s ======" % projectname
for i in prio2bugs.keys():
    print "  https://bugs.launchpad.net/%s/+bug/%s : %s" % \
        (projectname, i, prio2bugs[i][:-2])
