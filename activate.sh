#!/bin/sh
# Adds the grading helpers in your current bash / zsh shell PATH.
# Use as: `source ./path/to/activate.sh`
# vim: set ft=zsh

if [ -z "$BASH" ] && [ -z "$ZSH_NAME" ]; then
    echo "Unsupported shell! Please use zsh or bash!"
    exit 1
fi

if [ -n "$BASH" ]; then
    SCRIPTS_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE}" )" &> /dev/null && pwd )"
elif [ -n "$ZSH_NAME" ]; then
    SCRIPTS_DIR="$( cd -- "$( dirname -- "${(%):-%x}" )" &> /dev/null && pwd )"
fi
SCRIPTS_DIR="$SCRIPTS_DIR"

export _GRADING_SCRIPTS_DIR="$SCRIPTS_DIR"
export PATH="$SCRIPTS_DIR/bin:$SCRIPTS_DIR/moodle:$SCRIPTS_DIR/gsheet:$PATH"

if [[ -f "$SCRIPTS_DIR/grading.config.sh" ]]; then
    # load local grading config file (for customizations)
    source "$SCRIPTS_DIR/grading.config.sh" || return 1
fi

if [[ -z "$GRADING_NO_VENV" ]]; then
    ( cd "$SCRIPTS_DIR"; make ) || return 1
    source "$SCRIPTS_DIR/.venv/bin/activate" || return 1
    echo "VirtualEnv loaded ($(python3 --version))!"
fi

# print the path if debugging is active
if [[ -n "$DEBUG" ]]; then
    echo "Loaded grading scripts from path: '$SCRIPTS_DIR'"
fi

