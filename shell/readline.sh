#!/bin/bash
# Readline helpers (parsing, history, autocompletion, bindings etc.)

READLINE_PROMPT="> "

# Initializes the custom readline history integration
function read_hist_init() {
    # persistent prompt history
    HISTFILE=${1:-"$(pwd)/.history"}
    HISTCONTROL=ignoreboth:erasedups
    # clear current history list & reload from file
    history -c
    history -r || true
    trap 'history -a; exit' 0 1 2 3 4 5 6 7 8
}

# Uses bash's readline to input a user command, with shell history &
# autocompletion features
# Usage: read_line DEST_VAR_NAME
function read_line() {
    local -n line=$1
    read -rep"$READLINE_PROMPT" line || return 1
    [[ -z "$line" ]] || builtin history -s "$line"
    echo "$line"
}

