#!/bin/sh

# pass your volume name or leave it blank to use default
disk_name=${1:-HIIBOT}

disky=`df | grep $disk_name | cut -d" " -f1`
sudo umount /Volumes/$disk_name
sudo mkdir /Volumes/$disk_name
sleep 2
sudo mount -v -o noasync -t msdos $disky /Volumes/$disk_name
