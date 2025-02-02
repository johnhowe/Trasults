#!/usr/bin/env bash

DISK_LIMIT=$((512 * 1024 * 1024))
MAX_FILE_LIMIT=$((99 * 1024 * 1024))

check_disk_usage() {
    local current_usage
    current_usage=$(du -sb ~ | awk '{print $1}')
    echo "$current_usage"
    return $current_usage
}

file_size() {
    local file="$1"
    local file_size
    file_size=$(stat -c%s "$file")
    echo "$file $file_size"
    return $file_size
}

min() {
    if [ "$1" -gt "$2" ]; then
        echo "$2"
    else
        echo "$1"
    fi
}

df=$((DISK_LIMIT - $(check_disk_usage)))
db=$(file_size db.sqlite)

limit=$(min $((df/2)) $MAX_FILE_LIMIT)
echo $limit bytes limit on the next chunk:  $((limit/1024/1024)) MB

