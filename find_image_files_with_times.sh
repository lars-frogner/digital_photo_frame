#!/bin/bash
./find_image_files.sh "$@" | xargs -n1 -d '\n' ./find_image_time.sh
