#!/bin/bash
DIR=`dirname $0`
# Where pyinstaller puts the bundled executable
output_file="dist/rtt-logger"
# Where we want to put the executable
bin_dir="bin"

echo "DIR="$DIR

if !hash pip 2>/dev/null; then
  echo "You need to have 'pip' installed."
  exit 1
fi

if hash virtualenv 2>/dev/null; then
  # Set up virtualenv, unless it is already set up.
  if [[ ! -a $DIR/venv ]]; then
    virtualenv $DIR/venv
  fi
  source $DIR/venv/bin/activate
else
  # Prompt the user for installing all dependencies globally.
  read -p "Did not find 'virtualenv'. Install dependencies globaly? [y/n]" yn
  case ${yn:0:1} in
    y|Y ) ;;
    *) exit 1;;
  esac
fi

pip install -r $DIR/requirements.txt

pyinstaller -F $DIR/src/rtt-logger.py

if [[ ! -a $DIR/$bin_dir ]]; then
  mkdir $DIR/$bin_dir
fi

# Overwrite file, or should we check and prompt?
mv $DIR/$output_file $DIR/$bin_dir/
