import os.path
import datetime
import urllib
import sys
import subprocess
import tempfile
import time
from launchpadlib.launchpad import Launchpad


def abort(code, errmsg):
    print >> sys.stderr, errmsg
    sys.exit(code)


# Argument parsing
if len(sys.argv) < 4 or len(sys.argv) > 7:
    prog = sys.argv[0]
    abort(1, '''Grab tarball and release it on LP as milestone or version.

    Usage: %s [--into <LPproject>] <project> <version> <revision> [milestone]
    Example: %s nova 2011.3 20110702.r1234 diablo-3''' % (prog, prog))

if sys.argv[1] == '--into':
    into = True
    lpproject = sys.argv[2]
    sys.argv.pop(1)
    sys.argv.pop(1)
else:
    into = False

(project, version, revision) = sys.argv[1:4]
if not into:
    lpproject = project
if len(sys.argv) == 5:
    milestone = sys.argv[4]
else:
    milestone = version


# Connect to LP
print "Connecting to Launchpad..."
try:
    launchpad = Launchpad.login_with('openstack-lp-scripts', 'production')
except Exception, error:
    abort(2, 'Could not connect to Launchpad: ' + str(error))

# Retrieve milestone
print "Checking milestone..."
try:
    lp_proj = launchpad.projects[lpproject]
except KeyError:
    abort(2, 'Could not find project: %s' % lpproject)

for lp_milestone in lp_proj.all_milestones:
    if lp_milestone.name == milestone:
        if lp_milestone.release and not into:
            abort(2, 'Milestone %s was already released !' % milestone)
        if not lp_milestone.release and into:
            abort(2, 'Milestone %s was not released yet !' % milestone)
        if milestone != version:
            codename = "~" + lp_milestone.code_name.lower()
            if len(codename) != 3:
                abort(2, 'Bad code name for milestone: %s' % codename)
        else:
            codename = ""
        break
else:
    abort(2, 'Could not find milestone: %s' % milestone)

# Retrieve tgz, check contents and MD5
print "Downloading tarball..."
tmpdir = tempfile.mkdtemp()
base_tgz = "%s-%s%s~%s.tar.gz" % (project, version, codename, revision)
url_tgz = "http://%s.openstack.org/tarballs/%s" % (lpproject, base_tgz)
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
if not into:
    print "Marking milestone released..."
    if codename:
        release_notes = "This is another milestone (%s) on the road to %s %s." \
            % (milestone, project.capitalize(), version)
    else:
        release_notes = "This is %s %s release." \
            % (project.capitalize(), version)

    lp_release = lp_milestone.createProductRelease(
                date_released=datetime.datetime.utcnow(),
                release_notes=release_notes)
else:
    lp_release = lp_milestone.release

# Mark milestone inactive
if not into:
    print "Marking milestone inactive..."
    lp_milestone.is_active = False
    lp_milestone.lp_save()

# Upload file
print "Uploading release files..."
final_tgz = "%s-%s%s.tar.gz" % (project, version, codename)
if codename:
    description='%s "%s" milestone' % (project.capitalize(), milestone)
else:
    description='%s %s release' % (project.capitalize(), milestone)
lp_file = lp_release.add_file(file_type='Code Release Tarball',
    description=description,
    file_content=tgz_content, filename=final_tgz,
    signature_content=sig_content, signature_filename=final_tgz + '.asc',
    content_type="application/x-gzip; charset=binary")

# Check LP-reported MD5
print "Checking MD5s..."
time.sleep(2)
result_md5_url = "http://launchpad.net/%s/+download/%s/+md5" % \
    (lp_release.self_link[30:], final_tgz)
result_md5_file = urllib.urlopen(result_md5_url)
result_md5 = result_md5_file.read().split()[0]
result_md5_file.close()
if md5 != result_md5:
    abort(3, 'MD5sums (%s/%s) do not match !' % (md5, result_md5))

print "Done!"
