#/bin/sh
pep8 --exclude=docs streams
nosetests --with-coverage --cover-package=streams
