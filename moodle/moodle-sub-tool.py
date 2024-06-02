#!/usr/bin/env python3
"""
Moodle assignment directory rename script: renames student submission
directories to the user ID / email and optionally extracts the archives inside.

Note: requires a grading CSV exported for the assignment. You need to enable it
in Assignment Settings -> Feedback Types -> Offline Grading Worksheet, then
download it from View All Submission -> Download Grading Worksheet.

Grading directories must be named as '<Full Name>_<ID>_<submission suffix>'.

Invocation: moodle-sub-tool.py [options] <submissions dir> <grading csv>
"""

import sys
import os
import os.path
import shutil
import csv
import re
import traceback
import zipfile
import unicodedata
import argparse


submission_dir_re = re.compile(r'^(?P<lname>[a-zA-Z0-9 -]+)\s+(?P<fname>[A-Z0-9-]+)_(?P<id>[0-9]+)_')
archive_formats = ['zip', 'tar', 'tar.gz', 'tar.bz', 'tar.xz']  # avoid students trolling


def strip_accents(s):
    """ Strips the unicode accents (diacritics) from a string. """
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def read_grading_worksheet(csv_filename):
    """ 
    Reads the grading worksheet CSV and returns the students map containing
    id, fullname and email.
    """
    students_map = {}
    with open(csv_filename, newline='') as f:
        csvr = csv.reader(f, delimiter=',')
        for idx, line in enumerate(csvr):
            if idx == 0:  # first row is a header
                idx += 1
                continue
            idx += 1
            if len(line) < 3:
                continue
            student_id = re.sub(r'[^0-9]', '', line[0].strip())
            email = line[2].strip()
            students_map[str(student_id)] = {
                # note: ID column contains a text prefix, so exract just the number
                "id": student_id,
                "fullname": line[1].strip(),
                "email": email,
            }
    return students_map


def search_moodle_username(user_id, students_map):
    """
    Searches for the submission username inside the grading worksheet.
    """
    search_id = str(user_id)
    if search_id in students_map:
        return students_map[search_id]
    return None


def extract_archive(archive_file, dest_dir):
    """
    Extracts a .zip archive to the specified path with smart operation:
    if the extraction process results in a single child directory, it automatically
    flattens it.
    """
    shutil.unpack_archive(archive_file, dest_dir)
    os.remove(archive_file)
    dir_contents = os.listdir(dest_dir)
    if len(dir_contents) == 1:
        subdir_full = os.path.join(dest_dir, dir_contents[0])
        if os.path.isdir(subdir_full):
            # move all files to the root path
            with os.scandir(subdir_full) as it:
                for entry in it:
                    shutil.move(entry.path, dest_dir)


def main(args):
    rdir = args.directory

    if not os.path.isdir(rdir):
        print("Invalid directory: '{}'".format(rdir))
        sys.exit(1)

    # Load the exported grading worksheet CSV
    students_map = None
    rename_type = args.rename
    if args.sheet:
        students_map = read_grading_worksheet(args.sheet)
        if not rename_type:
            rename_type = 'email'
    if not rename_type:
        rename_type = 'fname'

    if rename_type == 'email' and not students_map:
        raise Exception("Cannot rename with emails without a grading worksheet!")

    # iterate through all directories and rename / extract them
    sub_dirs = os.listdir(rdir)
    for sub_dir in sub_dirs:
        full_path = os.path.join(rdir, sub_dir)
        if not os.path.isdir(full_path):
            continue
        norm_name = strip_accents(sub_dir)
        re_matches = submission_dir_re.match(norm_name)
        if re_matches:
            new_name = None
            student_obj = search_moodle_username(re_matches.group("id"), students_map)
            email = None
            if student_obj:
                email = student_obj["email"]
            if rename_type in ("email", "username"):
                if email:
                    if rename_type == "username":
                        email = re.sub(r'@\S+$', '', email)
                    new_name = email
            elif rename_type == "fname":
                # rename to  first_name + last_name
                new_name = re_matches["fname"] + " " + re_matches["lname"]
            elif rename_type == "fname_user":
                # rename to  first_name + last_name + (username)
                new_name = re_matches["fname"] + " " + re_matches["lname"]
                if email:
                    email = re.sub(r'@\S+$', '', email)
                    new_name += " (" + email + ")"
            if new_name:
                print("Renaming '{}' to '{}'".format(sub_dir, new_name))
                if not args.dry_run:
                    new_path = os.path.join(rdir, new_name)
                    os.rename(full_path, new_path)
                    full_path = new_path
            if not new_name:
                print("NOT renaming '{}'".format(sub_dir))
        else:
            print("NOT renaming '{}'".format(sub_dir))
        if args.extract:
            # find archive file
            subdir_files = os.listdir(full_path)
            if len(subdir_files) != 1:
                print("unzip: IGNORE '{}' (multiple files found)".format(sub_dir))
                continue
            archive_file = os.path.join(full_path, subdir_files[0])
            _, archive_ext = os.path.splitext(archive_file)
            if not archive_ext[1:]:
                print("unzip: IGNORE '{}' (not an archive)".format(archive_file))
                continue
            print("unzip: '{}'".format(archive_file))
            if not args.dry_run:
                try:
                    extract_archive(archive_file, full_path)
                except:
                    traceback.print_exc()


if __name__ == "__main__":
    # Check arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", "-w", help="Path to the grading worksheet to use for renaming (csv format)")
    parser.add_argument("--extract", "-x", action='store_true', help="Extract archives")
    parser.add_argument(
        "--rename", "-r", nargs="?", choices=['none', 'fname', 'email', 'username', "fname_user"],
        help="Rename directories using the given method " +
        "(default is 'fname', 'email' if --sheet is given)")
    parser.add_argument("--dry-run", "-n", action='store_true', help="Do a dry run (take no disk actions)")
    parser.add_argument("directory", help="The submissions directory.")
    args = parser.parse_args()
    main(args)

