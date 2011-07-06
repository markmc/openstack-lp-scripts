from launchpadlib.launchpad import Launchpad

# This script finds blueprints targeted to a current milestone but not
# accepted for the series (which therefore do not appear in release status)

# List of project/series combinations to consider
seriesname = 'diablo'
productlist = ['nova', 'glance', 'swift']


# Log into LP
lp = Launchpad.login_anonymously('openstack-lp-scripts', 'production',
    '~/.launchpadlib-cache', version='devel')

# Get the blueprints
for productname in productlist:
    milestones = []
    blueprints = []
    product = lp.projects[productname]
    series = product.getSeries(name=seriesname)
    for ms in series.active_milestones_collection:
        milestones.append(ms)
    for bp in series.valid_specifications:
        blueprints.append(bp)
    for bp in product.valid_specifications:
        if bp.milestone in milestones:
            if bp not in blueprints:
                print "(%s/%s) %s" % (productname, bp.milestone.name,
                    bp.web_link)
