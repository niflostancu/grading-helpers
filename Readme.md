# OmniGrader - Helper scripts for grading / assignments

This repository contains a series of utility scripts which can be used by
technically-proficient teachers to automate their activity / assignment grading
workflows (Google Sheets; Moodle is WIP).

**Features:**

- FZF (fuzzy finder) TUI for quickly searching names in a gradebook;
- customizable terminal-based prompt for editing grades;
- Regex-based columns to property / alias mappings;
- integration with Google Sheets via API;
- more stuff planned (e.g., Moodle tooling)!


## Requirements:

- A Linux-based system (or WSL) with `make` installed;
- [Python3](https://www.python.org/) with `python3-pip` and `python3-venv` installed;
- [FZF](https://github.com/junegunn/fzf)

## Preparation and usage

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

Open it with your favorite editor (e.g., `vim`) and change its values (also see
the instructions inside).

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
# run the grader (it should be inside your PATH)!
gsheet-gradebook.sh
# hope it worked, enjoy!
```

_Note:_ first time authentication needs to open a browser. If you use WSL and it
complains that no browser was installed, you can easily define the following
variable and point it to your windows browser, e.g.:
```sh
export BROWSER="/mnt/c/Program Files/Mozilla Firefox/firefox.exe"
```

