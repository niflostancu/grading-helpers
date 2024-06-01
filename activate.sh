#!/bin/sh
# Adds the grading helpers in your current bash / zsh shell PATH.
# Use as: `source ./path/to/activate.sh`
# vim: set ft=zsh

if [ -z "$BASH" ] && [ -z "$ZSH_NAME" ]; then
    echo "Unsupported shell! Please use zsh or bash!"
    exit 1
fi

if [[ -n "$GRADING_SCRIPTS_DIR" ]]; then
    true
elif [ -n "$BASH" ]; then
    GRADING_SCRIPTS_DIR="$( builtin cd -- "$( dirname -- "${BASH_SOURCE}" )" &> /dev/null && pwd )"
elif [ -n "$ZSH_NAME" ]; then
    GRADING_SCRIPTS_DIR="$( builtin cd -- "$( dirname -- "${(%):-%x}" )" &> /dev/null && pwd )"
fi

export _GRADING_SCRIPTS_DIR="$GRADING_SCRIPTS_DIR"
export PATH="$GRADING_SCRIPTS_DIR/bin:$GRADING_SCRIPTS_DIR/moodle:$GRADING_SCRIPTS_DIR/gsheet:$PATH"

if [[ -f "$GRADING_SCRIPTS_DIR/grading.config.sh" ]]; then
    # load local grading config file (for customizations)
    source "$GRADING_SCRIPTS_DIR/grading.config.sh" || return 1
fi

if [[ -z "$GRADING_NO_VENV" ]]; then
    ( cd "$GRADING_SCRIPTS_DIR"; make ) || return 1
    source "$GRADING_SCRIPTS_DIR/.venv/bin/activate" || return 1
    echo "VirtualEnv loaded ($(python3 --version))!"
fi

# print the path if debugging is active
if [[ -n "$DEBUG" ]]; then
    echo "Loaded grading scripts from path: '$GRADING_SCRIPTS_DIR'"
fi

