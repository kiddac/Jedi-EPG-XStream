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
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python3-requests
        fi
        echo ""

        echo "checking python3-difflib"
        if python -c "import difflib" &> /dev/null; then
            echo "Difflib library already installed"
        else
            opkg install python3-difflib
        fi
        echo ""

        echo "checking python3-fuzzywuzzy"
        if python -c "import fuzzywuzzy" &> /dev/null; then
            echo "Fuzzywuzzy library already installed"
        else
            opkg install python3-fuzzywuzzy
        fi
        echo ""

    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            opkg install python-requests
        fi
        echo ""

        echo "checking python-difflib"
        if python -c "import difflib" &> /dev/null; then
            echo "Difflib library already installed"
        else
            opkg install python-difflib
        fi
        echo ""

        echo "checking python-fuzzywuzzy"
        if python -c "import fuzzywuzzy" &> /dev/null; then
            echo "Fuzzywuzzy library already installed"
        else
            opkg install python-fuzzywuzzy
        fi
        echo ""
    fi
else
    echo "updating feeds"
    apt-get update
    echo
    if [[ $pyv =~ "Python 3" ]]; then
        echo "checking python3-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python3-requests
        fi
        echo ""

        echo "checking python3-difflib"
        if python -c "import difflib" &> /dev/null; then
            echo "Difflib library already installed"
        else
            apt-get -y install python3-requests
        fi
        echo ""

    else
        echo "checking python-requests"
        if python -c "import requests" &> /dev/null; then
            echo "Requests library already installed"
        else
            apt-get -y install python-requests
        fi
        echo ""

        echo "checking python-difflib"
        if python -c "import difflib" &> /dev/null; then
            echo "Difflib library already installed"
        else
            apt-get -y install python-difflib
        fi
        echo ""
    fi
fi
exit 0
