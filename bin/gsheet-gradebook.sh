#!/bin/bash
# Google Sheets-based interactive gradebook utility.
# Easily fetch & modify grades using fzf-based TUI.

set -e
shopt -s extglob
[[ -n "$_GRADING_SCRIPTS_DIR" ]] || {
    echo "No grading environment found! Have you activate.sh'd it?" >&2
    exit 1
}

# parse arguments (TODO: add help msg)
FZF="${FZF:-fzf}"
NO_FETCH=
INFINITE=
GSHEET_TOOL="$_GRADING_SCRIPTS_DIR/gsheet/gsheet-tool.py"
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -n|--no-fetch)
            NO_FETCH=1 ;;
        -i|--infinite)
            INFINITE=1 ;;
    esac; shift
done

# persistent prompt history
HISTFILE="$(pwd)"/.grading_history
history -c
history -r || true
trap 'history -a; exit' 0 1 2 3 4 5 6 7 8

# global state variables
S_ROW_A1=
declare -A S_VALUES=()

function refresh_spreadsheet() {
    "$GSHEET_TOOL" fetch_data
}

function cmd_update_cell() {
    local _ARGS=()
    for arg in "$@"; do
        _ARGS+=(--value "$arg")
    done
    "$GSHEET_TOOL" update --a1 "$S_ROW_A1" "${_ARGS[@]}"
}

# Shows info about current range
function cmd_show_info() {
    "$GSHEET_TOOL" fetch_data --cached --filter-range "$S_ROW_A1"
}

function cmd_get_metadata() {
    "$GSHEET_TOOL" get_metadata
}

function cmd_fetch_row() {
    "$GSHEET_TOOL" fetch_data --filter-range "$S_ROW_A1"
}

# Displays the FZF chooser menu
function chooser_menu() {
    local _OPTION=
    _OPTION="$("$GSHEET_TOOL" fetch_data --cached | $FZF)"
    if [[ -z "$_OPTION" ]]; then
        echo "No choice! Exiting..." >&2; exit 0
    fi
    S_ROW_A1="${_OPTION%%*( )"|"*}"
}

# Displays the grading prompt (after a spreadsheet row was chosen)
function grading_menu() {
    echo
    local _CUR_INFO="$(cmd_show_info)"
    echo "[GRADER] Current row: $_CUR_INFO"
    echo "[GRADER] Enter command ([i]nfo | [g]et | [u]pdate | [q]uit):"
    read -e -p "> " raw_cmd || {
        # Ctrl+D pressed
        S_ROW_A1= 
        return 0
    }
    history -s "$raw_cmd"
    # split multi-command strings
    local cmds=()
    IFS=";" read -ra cmds <<< "$raw_cmd"
    for cmd in "${cmds[@]}"; do
        local args=()
        eval 'IFS=" " args=('$cmd')'
        cmd=${args[0]}; args=("${args[@]:1}")
        case "$cmd" in
            i|info)
                cmd_show_info "${args[@]}" || true ;;
            metadata)
                cmd_get_metadata "${args[@]}" || true ;;
            g|get)
                cmd_fetch_row "${args[@]}" || true ;;
            u|update)
                cmd_update_cell "${args[@]}" || true ;;
            q|quit*)
                S_ROW_A1= 
                return 0 ;;
            "echo")
                echo "${args[@]}" ;;
            *) echo "Invalid command: '$cmd'!" >&2 ;;
        esac
    done
}

# gradebook entry selected, show interactive menu
refresh_spreadsheet
while true; do
    if [[ -z "$S_ROW_A1" ]]; then
        chooser_menu
    else
        grading_menu
    fi
done

