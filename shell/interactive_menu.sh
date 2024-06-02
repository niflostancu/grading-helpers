#!/bin/bash
# Interactive grading menu framework, with some shell features (history,
# callbacks, multiple command execution)

# interactive menu config + callbacks
declare -g -A INTERACTIVE_CONFIG=(
    [_ignore]=1  # ignore errors
    [help]=interactive_help
    [cmd_process]="interactive_cmd_process"
)
# array with registered commands
# Format: [cmd_name]=callback_func
declare -g -A INTERACTIVE_COMMANDS=(
    [help]="_interactive_help --force"
    [quit]="return 11" [q]='!quit'
    [echo]="builtin echo"
    [history]="builtin history"
)

# state var to show interactive help only once
_INTERACTIVE_HELP_SHOWN=

# Displays help for the interactive menu; may be overridden
function interactive_help() {
    local -A cmds=()
    local scmds=()
    for i in "${!INTERACTIVE_COMMANDS[@]}"; do
        if [[ "${INTERACTIVE_COMMANDS[$i]}" != '!'* ]]; then
            [[ -v "$cmds[$i]" ]] || cmds[$i]=$i
        fi
    done
    for c in "${!cmds[@]}"; do scmds+=("$c"); done
    echo "Enter command (${scmds[*]}):"
}
# Calls the configured help callback
function _interactive_help() {
    [[ -z "$_INTERACTIVE_HELP_SHOWN" || "$1" == "--force" ]] || return 0
    _INTERACTIVE_HELP_SHOWN=1
    ${INTERACTIVE_CONFIG[help]}
}

# Processes an interactive command
function interactive_cmd_process() {
    local cmd=$1; shift
    if [[ -v "INTERACTIVE_COMMANDS[$cmd]" ]]; then
        local target="${INTERACTIVE_COMMANDS[$cmd]}"
        if [[ "$target" == '!'* ]]; then
            target="${INTERACTIVE_COMMANDS[${target:1}]}"
        fi
        $target "$@"
    else
        echo "Invalid command: '$cmd'!" >&2
    fi
}

# Displays an interactive prompt with minor shell features
# Note: requires the readline module to be loaded / configured beforehand
function interactive_menu() {
    local raw_cmd=
    local cmds=()
    # show prompt help
    _interactive_help
    # read command using readline
    read_line raw_cmd || return 10

    # parse multiple commands (separated by ';')
    IFS=";" read -ra cmds <<< "$raw_cmd"
    for cmd in "${cmds[@]}"; do
        local args=()
        eval 'IFS=" " args=('$cmd')'
        ${INTERACTIVE_CONFIG[cmd_process]} "${args[@]}"
    done
}

