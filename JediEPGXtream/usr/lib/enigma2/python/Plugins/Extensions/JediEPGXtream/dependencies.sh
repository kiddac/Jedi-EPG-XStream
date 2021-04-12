#!/bin/sh

pyv="$(python3 -V 2>&1)" || pyv="$(python -V 2>&1)"
echo "$pyv"
echo "Checking Dependencies"
echo
if [ -d /etc/opkg ]; then
    echo "updating feeds"
    opkg update
    echo
    if [[ $pyv =~ "Python 3" ]]; then
      
        echo "checking python3-requests"
        opkg install python3-requests
        echo
        echo "checking python3-fuzzywuzzy"
        opkg install python3-fuzzywuzzy
        echo
    else
        echo "checking python-requests"
        opkg install python-requests
        echo
        echo "checking python-fuzzywuzzy"
        opkg install python-fuzzywuzzy
        echo
    fi
else
    echo "updating feeds"
    apt-get update
    echo
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        apt-get -y install python3-requests
        echo
    else
        echo "checking python-requests"
        apt-get -y install python-requests
        echo

    fi
fi
exit 0
