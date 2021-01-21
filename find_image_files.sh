#!/bin/bash
find "$@" -maxdepth 1 -type f -exec file --mime-type {} \+ | awk -F: '{if ($2 ~/image\//) print $1}'
