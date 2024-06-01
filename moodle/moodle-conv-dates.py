#!/usr/bin/env python3
"""
Moodle workbook date/time conversion script.

Parses the dates from a grading workbook into standard 'YYYY-MM-DD HH:MM' format,
which is easier to parse in scripts.

Invocation: moodle-conv-tool.py [options] INPUT_CSV OUTPUT_CSV 
"""
import sys
import argparse
import csv
from datetime import datetime

# "Friday, 26 May 2023, 12:44 PM"
DEF_DATE_FORMAT = "%A, %d %B %Y, %I:%M %p"
DEF_COLUMN_NAME = "Last modified (submission)"
OUT_DATE_FORMAT = "%Y-%m-%d %H:%M"


def moodle_convert_csv_dates(input_csv, output_csv, column_name=DEF_COLUMN_NAME,
                             format=DEF_DATE_FORMAT):
    """ 
    Opens the input csv and converts the date column to a parseable 'YYYY-MM-DD HH:MM' format.
    """
    date_col_idx = None
    lines = []
    with open(input_csv, newline='') as f:
        csvr = csv.reader(f, delimiter=',')
        for idx, line in enumerate(csvr):
            if idx == 0:  # header row
                try:
                    date_col_idx = line.index(column_name)
                except ValueError:
                    sys.stderr.write("Cannot find column named '%s' in input csv!" % column_name)
                    sys.exit(1)
                lines.append(line)
                continue
            if len(line) < 2:
                continue
            # line = list(line)
            date_str = line[date_col_idx].strip()
            if date_str == "" or date_str == "-":
                date_str = None
            else:
                pdate = datetime.strptime(date_str, format)
                date_str = pdate.strftime(OUT_DATE_FORMAT)
            line[date_col_idx] = date_str
            lines.append(line)
    
    if output_csv == None:
        return lines
    with open(output_csv, "w") as out:
        csvw = csv.writer(out, delimiter=",")
        csvw.writerows(lines)


if __name__ == "__main__":
    # Check arguments
    parser = argparse.ArgumentParser(
            description="Converts the date column of a Moodle Grading Worksheet to a parseable " +
            "'YYYY-MM-DD HH:MM' format.")
    parser.add_argument("input_csv", help="Path to the grading worksheet to read.")
    parser.add_argument("output_csv", help="Path to output csv file.")
    parser.add_argument("--column", nargs=1, default=DEF_COLUMN_NAME,
                        help="Column name which contains the date to be converted.")
    parser.add_argument("--format", nargs=1, default=DEF_DATE_FORMAT,
                        help="Current date format to parse (defaults to 'Weekday, DD Month 20xx, HH:MM AM/PM')")
    args = parser.parse_args()
    moodle_convert_csv_dates(args.input_csv, args.output_csv,
                             column_name=args.column, format=args.format)

