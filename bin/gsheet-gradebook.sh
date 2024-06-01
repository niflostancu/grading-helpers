#!/bin/bash
# Google Sheets-based interactive gradebook utility.
# Easily fetch & modify grades using fzf-based TUI.

set -e
shopt -s extglob
[[ -n "$_GRADING_SCRIPTS_DIR" ]] || {
    echo "No grading environment found! Have you activate.sh'd it?" >&2
    exit 1
}

source "$_GRADING_SCRIPTS_DIR/shell/readline.sh"
source "$_GRADING_SCRIPTS_DIR/shell/interactive_menu.sh"

# parse arguments (TODO: add help msg)
FZF="${FZF:-fzf}"
NO_FETCH=
GSHEET_TOOL="$_GRADING_SCRIPTS_DIR/gsheet/gsheet-tool.py"
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -n|--no-fetch)
            NO_FETCH=1 ;;
    esac; shift
done

# global state variables
S_ROW_A1=
declare -A S_VALUES=()
# interactive menu callbacks
INTERACTIVE_CONFIG[help]="grading_menu_help"
INTERACTIVE_COMMANDS+=(
    [info]=cmd_show_info [i]='!info'
    [refresh]=cmd_refresh [r]='!refresh'
    [update]=cmd_update_cell [set]='!update' [u]='!update'
    [metadata]=cmd_get_metadata
)

function refresh_spreadsheet() {
    "$GSHEET_TOOL" fetch_data
}

function grading_select_row() {
    S_ROW_A1=$1
    _INTERACTIVE_HELP_SHOWN=
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
function cmd_refresh() {
    "$GSHEET_TOOL" fetch_data --filter-range "$S_ROW_A1"
}

function grading_menu_help() {
    echo
    local _CUR_INFO="$(cmd_show_info)"
    echo "[GRADER] Current row: $_CUR_INFO"
    interactive_help
}

# Displays the FZF chooser menu
function chooser_menu() {
    local _OPTION=
    _OPTION="$("$GSHEET_TOOL" fetch_data --cached | $FZF)"
    if [[ -z "$_OPTION" ]]; then
        echo "No choice! Exiting..." >&2; exit 0
    fi
    grading_select_row "${_OPTION%%*( )"|"*}"
}

# Displays the grading prompt (after a spreadsheet row was chosen)
function grading_menu() {
    interactive_menu || {
        local ec="$?"
        if [[ $ec -eq 10 || $ec -eq 11 ]]; then
            # Ctrl+D / quit called
            grading_select_row ""
            return 0
        fi
    }
}

# gradebook entry selected, show interactive menu
[[ "$NO_FETCH" == "1" ]] || refresh_spreadsheet

# enable interactive menu history
read_hist_init "$(pwd)/.grading_history"

while true; do
    if [[ -z "$S_ROW_A1" ]]; then
        chooser_menu
    else
        grading_menu
    fi
done

