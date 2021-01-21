#!/bin/bash
FILE_PATH=$1
TIME=$(sudo exiftool -b -DateTimeOriginal "$FILE_PATH" 2> /dev/null)
if [[ -z $TIME ]]; then
    TIME=$(sudo stat -c '%y' "$FILE_PATH" | sed -n "s/^\(.*\)\..*$/\1/p" | tr - :)
fi
echo "($FILE_PATH) $TIME"
