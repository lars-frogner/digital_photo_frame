#!/bin/bash
for FILE_PATH in "$@"; do
    TIME=$(sudo exiftool -b -DateTimeOriginal "$FILE_PATH" 2> /dev/null | sed -n 's/^\([0-9]\{4\}\):\([0-9]\{2\}\):\([0-9]\{2\}\)\(.*\)$/\1-\2-\3\4/p')
    if [[ -z $TIME ]]; then
        TIME=$(sudo stat -c '%y' "$FILE_PATH" | sed -n "s/^\(.*\)\..*$/\1/p")
    fi
    echo "$TIME"
done
