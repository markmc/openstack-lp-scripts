import os.path
import datetime
import urllib
import sys
import subprocess
from launchpadlib.launchpad import Launchpad

# Argument parsing
if len(sys.argv) != 5:
    prog = sys.argv[0]
    print >> sys.stderr, '''Upload a release tgz to a Launchpad project.

    Usage: %s <project> <version> <revision> <milestone>
    Example: %s nova 2011.3~d2 20110702.r1234 diablo-3''' % (prog, prog)
    sys.exit(1)
    # TODO Get milestone codename from LP ?

(project, version, revision, milestone) = sys.argv[1:]

# Connect to LP
try:
    launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')
except Exception, error:
    print >> sys.stderr, 'Could not connect to Launchpad:', str(error)
    sys.exit(2)

# Retrieve milestone
lp_proj = launchpad.projects[project]
for ms in lp_proj.all_milestones:
    if ms.name == milestone:
        lp_milestone = ms
        break
else:
    print >> sys.stderr, 'Could not retrieve milestone'
    sys.exit(2)

# Retrieve tgz
base_tgz = "%s-%s~%s.tar.gz" % (project, version, revision)
url_tgz = "http://%s.openstack.org/tarballs/%s" % (project, base_tgz)
(tgz, message) = urllib.urlretrieve(url_tgz)

# Check and MD5 retrieved tgz
subprocess.check_call(['tar', 'ztf', tgz])  # TODO could be less verbose
md5 = subprocess.check_output(['md5sum', tgz]).split()[0]

# Sign tgz
sig = tgz + '.asc'
if not os.path.exists(sig):
    print 'Calling GPG to create tgz signature...'
    subprocess.check_call(['gpg', '--armor', '--sign', '--detach-sig', tgz])
    # TODO fix tmpfile vuln !

# Read contents
with open(tgz) as tgz_file:
    tgz_content = tgz_file.read()
with open(sig) as sig_file:
    sig_content = sig_file.read()

# Mark milestone released
release_notes = "This is the second milestone (diablo-2) on the road to Glance 2011.3."  # TODO fix message
lp_release = lp_milestone.createProductRelease(
            date_released=datetime.datetime.utcnow(),
            release_notes=release_notes)

# Upload file
final_tgz = "%s-%s.tar.gz" % (project, version)
lp_file = lp_release.add_file(file_type='Code Release Tarball',
    description='%s "%s" milestone' % (project, milestone),
    file_content=tgz_content, filename=final_tgz,
    signature_content=sig_content, signature_filename=final_tgz + '.asc',
    content_type="application/x-gzip; charset=binary")

# Check LP-reported MD5
result_md5_url = "%s/+download/%s/+md5" % (lp_release.web_link, final_tgz)
result_md5_file = urllib.urlopen(result_md5_url)
result_md5 = result_md5_file.read().split()[0]
result_md5_file.close()
if md5 != result_md5:
    print >> sys.stderr, 'MD5sums do not match !'
    sys.exit(3)
