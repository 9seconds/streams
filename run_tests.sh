#/bin/sh
pep8 --exclude=docs streams tests
nosetests --with-coverage --cover-package=streams
