#!/bin/sh

# check that we are in the right directory
if [ ! -d src ]; then
    echo 'This script must be launched from the SLAM root directory.'
    exit 1
fi

cd slam

# create the django database
echo 'Creation and initialization of the database...'
python manage.py migrate || exit 1

echo "Done. SLAM is ready."
