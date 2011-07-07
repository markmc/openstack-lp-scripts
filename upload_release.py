import os.path
import datetime
import urllib
import sys
import subprocess
import tempfile
from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


# Argument parsing
if len(sys.argv) != 5:
    prog = sys.argv[0]
    abort(1, '''Grab tarball and release it on LP as milestone.

    Usage: %s <project> <version> <revision> <milestone>
    Example: %s nova 2011.3 20110702.r1234 diablo-3''' % (prog, prog))

(project, version, revision, milestone) = sys.argv[1:]

# Connect to LP
print "Connecting to Launchpad..."
try:
    launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')
except Exception, error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve milestone
print "Checking milestone..."
try:
    lp_proj = launchpad.projects[project]
except KeyError:
    abort(2, 'Could not find project: %s' % project)

for lp_milestone in lp_proj.all_milestones:
    if lp_milestone.name == milestone:
        if lp_milestone.release:
            abort(2, 'Milestone %s was already released !' % milestone)
        codename = lp_milestone.code_name.lower()
        if len(codename) != 2:
            abort(2, 'Bad code name for milestone: %s' % codename)
        break
else:
    abort(2, 'Could not find milestone: %s' % milestone)

# Retrieve tgz, check contents and MD5
print "Downloading tarball..."
tmpdir = tempfile.mkdtemp()
base_tgz = "%s-%s~%s~%s.tar.gz" % (project, version, codename, revision)
url_tgz = "http://%s.openstack.org/tarballs/%s" % (project, base_tgz)
tgz = os.path.join(tmpdir, base_tgz)

(tgz, message) = urllib.urlretrieve(url_tgz, filename=tgz)

try:
    subprocess.check_call(['tar', 'ztf', tgz])
except subprocess.CalledProcessError, e:
    abort(2, '%s is not a tarball. Bad revision specified ?' % base_tgz)

md5 = subprocess.check_output(['md5sum', tgz]).split()[0]

# Sign tgz
print "Signing tarball..."
sig = tgz + '.asc'
if not os.path.exists(sig):
    print 'Calling GPG to create tgz signature...'
    subprocess.check_call(['gpg', '--armor', '--sign', '--detach-sig', tgz])

# Read contents
with open(tgz) as tgz_file:
    tgz_content = tgz_file.read()
with open(sig) as sig_file:
    sig_content = sig_file.read()

# Mark milestone released
print "Marking milestone released..."
release_notes = "This is another milestone (%s) on the road to %s %s." \
    % (milestone, project.capitalize(), version)
lp_release = lp_milestone.createProductRelease(
            date_released=datetime.datetime.utcnow(),
            release_notes=release_notes)

# Upload file
print "Uploading release files..."
final_tgz = "%s-%s~%s.tar.gz" % (project, version, codename)
lp_file = lp_release.add_file(file_type='Code Release Tarball',
    description='%s "%s" milestone' % (project, milestone),
    file_content=tgz_content, filename=final_tgz,
    signature_content=sig_content, signature_filename=final_tgz + '.asc',
    content_type="application/x-gzip; charset=binary")

# Check LP-reported MD5
print "Checking MD5s..."
result_md5_url = "%s/+download/%s/+md5" % (lp_release.web_link, final_tgz)
result_md5_file = urllib.urlopen(result_md5_url)
result_md5 = result_md5_file.read().split()[0]
result_md5_file.close()
if md5 != result_md5:
    abort(3, 'MD5sums (%s/%s) do not match !' % (md5, result_md5))

print "Done!"
