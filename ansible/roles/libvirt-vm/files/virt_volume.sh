#!/bin/bash

# Ensure that a libvirt volume exists, optionally uploading an image.
# On success, output a JSON object with a 'changed' item.

if [[ $# -ne 4 ]] && [[ $# -ne 5 ]]; then
    echo "Usage: $0 <name> <pool> <capacity> <format> [<image>]"
    exit 1
fi

NAME=$1
POOL=$2
CAPACITY=$3
FORMAT=$4
IMAGE=$5

# Check whether a volume with this name exists.
output=$(virsh vol-info --pool $POOL --vol $NAME 2>&1)
result=$?
if [[ $result -eq 0 ]]; then
    echo '{"changed": false}'
    exit 0
elif ! echo "$output" | grep 'Storage volume not found' >/dev/null 2>&1; then
    echo "Unexpected error while getting volume info"
    echo "$output"
    exit $result
fi

# Create the volume.
output=$(virsh vol-create-as --pool $POOL --name $NAME --capacity $CAPACITY --format $FORMAT 2>&1)
result=$?
if [[ $result -ne 0 ]]; then
    echo "Failed to create volume"
    echo "$output"
    exit $result
fi

if [[ -n $IMAGE ]]; then
    # Upload an image to the volume.
    output=$(virsh vol-upload --pool $POOL --vol $NAME --file $IMAGE 2>&1)
    result=$?
    if [[ $result -ne 0 ]]; then
        echo "Failed to upload image $IMAGE to volume $NAME"
        echo "$output"
        virsh vol-delete --pool $POOL --vol $NAME
        exit $result
    fi

    # Resize the volume to the requested capacity.
    output=$(virsh vol-resize --pool $POOL --vol $NAME --capacity $CAPACITY 2>&1)
    result=$?
    if [[ $result -ne 0 ]]; then
        echo "Failed to resize volume $VOLUME to $CAPACITY"
        echo "$output"
        exit $result
    fi
fi

echo '{"changed": true}'
exit 0
