#!/bin/bash

# Script to create a tagged release of a deliverable and push the tag to
# Gerrit.

set -eu

function usage {
    echo "Usage"
    echo "$0 <repo> <version> <ref> <series>"
    echo
    echo "Example:"
    echo "$0 kayobe 4.0.0 origin/stable/queens queens"
}

function get_last_tag {
    # Print the most recent tag for a ref. If no ref is specified, the
    # currently checked out branch is examined.
    local ref="$1"
    if ! git describe --abbrev=0 --first-parent ${ref} >/dev/null 2>&1; then
        echo ""
    else
        git describe --abbrev=0 --first-parent ${ref}
    fi
}

[[ $# -eq 4 ]] || (usage; exit 1)

REPO=$1
VERSION=$2
REF=$3
SERIES=$4

[[ -n $REPO ]] || (echo "Repo not specified"; exit 1)
[[ -n $VERSION ]] || (echo "Version not specified"; exit 1)
[[ -n $REF ]] || (echo "Ref not specified"; exit 1)
[[ -n $SERIES ]] || (echo "Series not specified"; exit 1)

pre_release_pat='\.[[:digit:]]+[ab][[:digit:]]+'
rc_release_pat='\.[[:digit:]]+rc[[:digit:]]+'
if [[ $VERSION =~ $pre_release_pat ]]; then
    RELEASETYPE="development milestone"
elif [[ $VERSION =~ $rc_release_pat ]]; then
    RELEASETYPE="release candidate"
else
    RELEASETYPE="release"
fi

TARGETSHA=`git log -1 $REF --format='%H'`

# Determine the most recent tag before we add the new one.
PREVIOUS=$(get_last_tag $TARGETSHA)

echo "Tagging $TARGETSHA as $VERSION"
if git show-ref "$VERSION"; then
    echo "$REPO already has a version $VERSION tag, skipping further processing"
    continue
fi

# WARNING(mgoddard): announce.sh expects to be able to parse this
# commit message, so if you change the format you may have to
# update announce.sh as well.
TAGMSG="$REPO $VERSION $RELEASETYPE

meta:version: $VERSION
meta:diff-start: -
meta:series: $SERIES
meta:release-type: $RELEASETYPE
meta:pypi: no
meta:first: no
"
git tag -m "$TAGMSG" -s "$VERSION" $TARGETSHA
git push gerrit "$VERSION"
