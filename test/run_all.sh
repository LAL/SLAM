#!/bin/sh

# check that we are in the right directory
if [ ! -d src ]; then
    echo 'This script must be launched from the SLAM root directory.'
    exit 1
fi

cd src/

# write the test configuration
echo 'Configuring the application...'
mv configuration.py configuration.py.bak
echo '
DEBUG = True
ADMINS = ()
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": "/tmp/slam-fulltest.db"
    }}
TIME_ZONE = "Europe/Paris"
LANGUAGE_CODE = "fr-FR"
SECRET_KEY = "random"
' > configuration.py

cd ..
echo 'ROOT_DIR = r"'"$(pwd)"'"' >> ./src/configuration.py

# create the django database
echo 'Creation and initialization of the database...'
python ./src/manage.py syncdb --noinput || exit 1

# check that the database have been correctly created
echo 'Verification that the database is correctly initialized...'
./src/slam_cli.py -a list || exit 1

# launch pylint
echo 'Launching code checker...'
cd src
pylint --rcfile=../test/pylintrc slam webinterface/views.py slam_cli.py
cd ..

# launch the NOSE test-suite
echo 'Launching full test-suite...'
python src/manage.py runserver --nothreading 8737 &
# pkill is used to kill the `manage.py runserver` and all of its children
nosetests --with-cov --cov-report term-missing --cov src/ --with-xunit --xunit-file=./test/nosetests.xml || { pkill -P $!; exit 1; }
pkill -P $!

# generate the whole SPHINX documentation
echo 'Generation of the documentation...'
make -C doc html || exit 1

# clean-up
make -C doc clean
mv src/configuration.py.bak src/configuration.py
