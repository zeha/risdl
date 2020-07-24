#!/bin/bash

page=1

while true; do

echo "index page $page ..."

fn=bundesnormen/index-${page}.xml

if [ \! -e "$fn" ]; then
  break
fi

for url in $(xmllint "${fn}" --format | awk '/<Url>(.*\.xml)</ { FS=">"; $0=$2; print $1; }' | sed -e 's!<.*!!');
do
    echo "$url"
    if [ \! -e $(basename "$url") ]; then 
    (cd bundesnormen; curl -O "$url")
    fi
done

page=$((page+1))

#break

done
