#!/bin/bash

check_deadsnakes_ppa() {
    # Search for "deadsnakes" in sources.list.d or sources.list
    if grep -Rq "ppa:deadsnakes/ppa" /etc/apt/sources.list.d/ || grep -q "ppa.launchpad.net/deadsnakes/ppa" /etc/apt/sources.list; then
        echo "DeadSnakes PPA is already added."
        return 0
    else
        echo "DeadSnakes PPA is not added."
        return 1
    fi
}

if [ ! -x /usr/bin/python3.11 ] ; then
  if check_deadsnakes_ppa; then
      echo "Skipping add-apt-repository."
  else
      echo "Adding DeadSnakes PPA."
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      sudo apt update
  fi
  sudo apt install -y python3.11 python3.11-venv
fi
