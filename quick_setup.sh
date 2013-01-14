#!/bin/sh

# check that we are in the right directory
if [ ! -d src ]; then
    echo 'This script must be launched from the SLAM root directory.'
    exit 1
fi

# write the default basic configuration
echo 'Configuring the application...'
mv ./src/configuration.py ./src/configuration.py.bak
echo '
import sys
DEBUG = True
ADMINS = ()
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": sys.path[0] + "/../slam.db"
    }}
TIME_ZONE = "Europe/Paris"
LANGUAGE_CODE = "fr-FR"
RELOAD_SCRIPT = ""
' > ./src/configuration.py

echo 'SECRET_KEY = r"""'"`</dev/urandom tr -dc '[:graph:]' | head -c50`"'"""' \
    >> ./src/configuration.py

echo 'ROOT_DIR = r"'"$(pwd)"'"' >> ./src/configuration.py

# create the django database
echo 'Creation and initialization of the database...'
python ./src/manage.py syncdb --noinput || exit 1

# create the translation file for the web interface
echo 'Compilation of the translation files...'
cd ./src/webinterface
python ../manage.py compilemessages

echo "Done. SLAM is ready."
