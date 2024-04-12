# OmniGrader - Helper scripts for grading / assignments

This repository contains a series of utility scripts that can be used by
_somewhat technically-proficient_ teachers to automate their activity
/ assignment grading workflows (for Google Sheets only; Moodle script is WIP).

**Features:**

- FZF (fuzzy finder) TUI tool for quickly searching names in a gradebook and
  marking grades (or setting any tabular data, actually);
- customizable terminal-based prompt for editing grades;
- Regex-based columns to property / alias mappings;
- integration with Google Sheets via API;
- more stuff planned (e.g., Moodle tooling)!


## Requirements:

- A Linux-based system (or WSL) with `make` installed;
- [Python3](https://www.python.org/) with `python3-pip` and `python3-venv` installed;
- [FZF](https://github.com/junegunn/fzf)

## Preparation

### Google Sheets API credentials

In order to use the Google Sheets API, you must first create a personal project
on [Google Cloud](https://console.cloud.google.com/).
In there, make sure to enable the [Google Sheets API](https://console.cloud.google.com/apis/enableflow?apiid=sheets.googleapis.com).

Next must obtain a Google OAuth client credentials by [following this
tutorial](https://developers.google.com/workspace/guides/configure-oauth-consent).
Save the client credentials `.json` file somewhere safe.

### Script setup & activation

Copy the `grading-config.sample.yaml` example file and rename it to
`grading-config.yaml`.

You can have the configuration in separate directory (e.g., one for each course)
anywhere inside your filesystem (read below: you will have to include the script's
environment in your shell).

Open it with your favorite editor and change its values (also see the
instructions inside).

- Make sure to enter the path to your client credentials you obtained in the
earlier steps;
- You may obtain your Spreadsheet ID by following the guide here:
https://stackoverflow.com/questions/36061433/how-do-i-locate-a-google-spreadsheet-id
- Also update the fetch range, the columns you want to view / edit and the display
format strings!

Finally, you must activate the environment in your current shell:
```
# ofc, change this:
source ~/path/to/omnigrader/activate.sh
# Note: a Python VirtualEnv is created the first time it's activated

# Afterwards, run the grader (was added in PATH by `activate.sh`)!
gsheet-gradebook.sh
# check the usage help below & enjoy!
```

_Note:_ first time authentication needs to open a browser. If you use WSL and it
complains that no browser was installed, you can easily define the following
variable and point it to your Windows browser, e.g.:
```sh
export BROWSER="/mnt/c/Program Files/Mozilla Firefox/firefox.exe"
```

## Gradebook Usage

Make sure to source the _omnigrader_'s `activate.sh` script inside your current
shell (or make an alias).

The gradebook tool is actually a tabular search & modify utility: first, using
a FuZzy Finder (`fzf`), you choose an entry from your gradebook to view/edit.

After selecting a subject (simply use `<enter>`), it then displays all mapped
columns' values and an inner command prompt appears.

The following commands are available (note the _"`[a]bbreviation`"_ syntax!):

- `[i]nfo`: [re]displays all key/value fields of the current entry (row);
- `[r]efresh`: refreshes the entire row from server and displays it;
- `[u]pdate` (alias `set`): changes a specific cell; accepts multiple
  `key=value` arguments where `key` is the name of the column (mapped inside the
  config file) and `value` is the new value to set to the corresponding cell
  (for the current user); quoting has the same rules as `bash`!

  Example: `u assistant="Florin" lab01=7 lab02=9`

- `[q]uit`: quits the command prompt, going back to the FZF screen;
- `metadata`: displays the Python script's metadata (use for debugging
  purposes);

Note that the inner CLI prompt has rudimentary shell features such as history
and multiple command chaining using `;`. For example, you may quickly issue the
previous command using `<up>` arrow, which could be a one-liner: `update lab01=10
lab2=10; quit` (set these values and immediately exit to the `fzf` screen).

To exit the TUI tool, simply press `<C-d>` to quit the prompt and/or `<C-c>`
when inside the `fzf` page.

## Troubleshooting

Unfortunately, the private OAuth key expires after several days of unuse and a
Bad Request HTTP error (`invalid_grant`) is thrown.
To fix this, simply delete the file where `google_auth.token` points to and
retry (you will have to re-authenticate the script, though).

This will be fixed once [and if] a public shared API key is obtained.

