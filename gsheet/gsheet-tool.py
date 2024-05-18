#!/usr/bin/env python3
# Google Sheets-based simple retrieve / set CLI utility.
# Allows fetching ranges and setting specific cells using Google Sheets API.

import argparse
import math
import yaml
import json
import stat
import os
import os.path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

CONFIG_FILE = "grading-config.yaml"
CACHE_FILE = ".index.csv"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def parse_sheet_range(range_str):
    """ Parses a Google Sheet A1-notation range. """
    sheet_match = re.match(r'^(\'?.+\'?!)?(.+)$', range_str)
    if not sheet_match:
        raise ValueError("Unable to parse range '%s'" % (range_str,))
    sheet = sheet_match.group(1).strip("'!")
    ranges = []
    for a1str in sheet_match.group(2).split(":"):
        r_match = re.match("^([A-Z]+)?([0-9]+)?$", a1str)
        if not r_match:
            raise ValueError("Unable to parse A1 notation: '%s'" % (a1str,))
        a1obj = (r_match.group(1), int(r_match.group(2)) if r_match.group(2) else None)
        ranges.append(a1obj)
    return [sheet] + ranges

def build_a1notation(range_obj):
    """ Builds a A1 notation string from a range object. """
    prefix = f"{range_obj[0]}!" if range_obj[0] else ''
    components = []
    for a1obj in range_obj[1:]:
        components.append(str(a1obj[0]) + (str(a1obj[1]) if a1obj[1] else ''))
    return prefix + ':'.join(components)

def remap_row(row, columnMap):
    """ Remaps rows to a dict based on column mapping. """
    obj = {}
    for name, idx in columnMap.items():
        if len(row) <= idx: continue
        obj[name] = row[idx].strip()
    return obj

def column_letter_to_idx(letter):
    column = 0
    for idx, c in enumerate(letter):
        column += (ord(c) - 64) * int(math.pow(26, len(letter) - idx - 1));
    return column

def column_idx_to_letter(column):
    letter = ''
    while (column > 0):
        temp = (column - 1) % 26
        letter = chr(temp + 65) + letter
        column = (column - temp - 1) // 26
    return letter

def auth_credentials(authConfig):
    """ Returns authentication object for Google Sheets. """
    creds = None
    if "serviceAccount" in authConfig and authConfig["serviceAccount"]:
        # use a service account for auth
        saFile = os.path.expanduser(authConfig["serviceAccount"])
        creds = service_account.Credentials.from_service_account_file(
            filename=saFile, scopes=SCOPES)
    else:
        tokenFile = os.path.expanduser(authConfig.get("token", ".token.json"))
        if os.path.exists(tokenFile):
            creds = Credentials.from_authorized_user_file(tokenFile, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("Credentials expired, please re-authenticate...")
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    os.path.expanduser(
                        authConfig.get("credentials", "credentials.json")), SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(tokenFile, "w") as token:
                token.write(creds.to_json())
                os.chmod(tokenFile, stat.S_IRUSR | stat.S_IWUSR)
    return creds

def get_spreadsheet(creds, spreadsheet_id, range_str):
    """ Returns the requested Spreadsheet object. """
    service = build("sheets", "v4", credentials=creds)
    spreadsheet = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_str)
        .execute()
    )
    return spreadsheet

def update_spreadsheet(creds, spreadsheet_id, data_map):
    """ Modifies a SpreadSheet range. """
    service = build("sheets", "v4", credentials=creds)
    data = [{"range": key, "values": val} for key, val in data_map.items()]
    body = {"valueInputOption": "USER_ENTERED", "data": data}
    spreadsheet = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
    return spreadsheet


def fetch_data(sheetsCfg, creds, force=False, cached=False, filter_range=None):
    ranges = sheetsCfg.get("sheetRanges")
    cacheFile = sheetsCfg.get("cache", ".cache.json")
    data = None
    if cached: force = False
    if os.path.exists(cacheFile) and not force:
        with open(cacheFile, "r") as f:
            data = json.load(f)
    elif cached:
        raise FileNotFoundError("Cached data not found:" + cacheFile)
    if not data:
        data = {"values": [], "meta": {}}
        patterns = sheetsCfg.get("columnPatterns")
        for range_str in ranges:
            # record metadata for current range object
            sheet_info = {"obj": parse_sheet_range(range_str), "columnMap": None}
            spreadsheet = get_spreadsheet(creds, sheetsCfg.get("id"), range_str)
            rows = spreadsheet.get("values", [])
            row_num = sheet_info["obj"][1][1]
            for row in rows:
                # map columns based on configured regex
                if not sheet_info["columnMap"]:  ## first row is the header
                    columnMap = {}
                    for idx, val in enumerate(row):
                        val = val.strip()
                        if not val:
                            continue
                        name = None
                        for pat_name, pat_re in patterns.items():
                            re_patterns = pat_re if isinstance(pat_re, list) else [pat_re]
                            for rpat in re_patterns:
                                col_matches = re.match(rpat, val, re.I | re.S)
                                if not col_matches: continue
                                if pat_name == "_":
                                    if len(col_matches.groups()) > 0: name = col_matches.group(1)
                                    else: name = val
                                elif pat_name[0] == "_":
                                    name = col_matches.expand(pat_name[1:])
                                else:
                                    name = pat_name
                                break
                            if name: break
                        if not name:
                            continue
                        columnMap[name] = idx
                    for pat_name, pat_re in patterns.items():
                        if pat_name[0] != "_" and pat_name not in columnMap:
                            raise IndexError(f"Column not found: {{{pat_name}: {pat_re}}}")
                    sheet_info["columnMap"] = columnMap
                else:
                    if row and row[0]:
                        obj = {"row": row, "row_num": row_num, "parent_sheet": sheet_info["obj"][0]}
                        data["values"].append(obj)
                row_num += 1
            data["meta"][sheet_info["obj"][0]] = sheet_info
        # cache the data into a JSON for further retrieval
        with open(cacheFile, "w") as f:
            json.dump(data, f)
    if filter_range:
        filter_range_obj = parse_sheet_range(filter_range)
        filter_sheet = filter_range_obj[0]
        filter_row_idx = filter_range_obj[1][1]
        for obj in data["values"]:
            if (obj["parent_sheet"] == filter_sheet) and (obj["row_num"] == filter_row_idx):
                sheet_info = data["meta"][obj["parent_sheet"]]
                return (obj, sheet_info)
    return data

def do_fetch_data(sheetsCfg, creds, cached=False, filter_range=None):
    data = fetch_data(sheetsCfg, creds, force=(not cached),
                      cached=cached, filter_range=filter_range)
    if filter_range:
        infoFormat = sheetsCfg.get("infoFormat", "{a1_str}: {username}: {obj_str}")
        if not data:
            print("Object not found!")
            return
        dataObj = data[0]
        sheet_info = data[1]
        rowObj = remap_row(dataObj["row"], sheet_info["columnMap"])
        obj_str = str(rowObj)
        a1_str = build_a1notation([sheet_info["obj"][0],
                                  (sheet_info["obj"][1][0], dataObj["row_num"])])
        print(infoFormat.format(
            row_num=dataObj["row_num"], a1_str=a1_str, obj_str=obj_str, **rowObj))
        return

    displayFormat = sheetsCfg.get("listFormat", "{a1_str} | {obj_str}")
    for dataObj in data["values"]:
        sheet_info = data["meta"][dataObj["parent_sheet"]]
        rowObj = remap_row(dataObj["row"], sheet_info["columnMap"])
        obj_str = str(rowObj)
        a1_str = build_a1notation([sheet_info["obj"][0],
                                  (sheet_info["obj"][1][0], dataObj["row_num"])])
        print(displayFormat.format(
            row_num=dataObj["row_num"], a1_str=a1_str, obj_str=obj_str, **rowObj))

def do_print_metadata(sheetsCfg, creds):
    data = fetch_data(sheetsCfg, creds, cached=True)
    print(data["meta"])

def do_update_cell(args, sheetsCfg, creds):
    data = fetch_data(sheetsCfg, creds, cached=True)
    range_obj = parse_sheet_range(args.a1)
    data_map = {}
    for val_str in args.value:
        new_range_obj = list(range_obj)
        val_split = val_str.split("=", 1)
        if len(val_split) == 2:
            col_idx = column_letter_to_idx(range_obj[1][0])
            col_idx += data["meta"][range_obj[0]]["columnMap"][val_split[0]]
            new_range_obj[1] = (column_idx_to_letter(col_idx), range_obj[1][1])
            val_str = val_split[1]
        new_range_str = build_a1notation(new_range_obj)
        data_map[new_range_str] = [[val_str]]
    print("set", data_map)
    if not args.dry_run:
        update_spreadsheet(creds, sheetsCfg.get("id"), data_map=data_map)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("gsheet-tool.py",
                                     "")
    parser.add_argument("--config", "-c", help="Path to config file", default=CONFIG_FILE)
    subparsers = parser.add_subparsers(dest="command", required=True,
                                       title='commands', description='valid commands')
    subparsers.add_parser("auth", help="authenticates the Google API")
    p_fetch = subparsers.add_parser("fetch_data", help="fetches & caches all ranges from the spreadsheet")
    p_fetch.add_argument("--cached", action="store_true", help="always fetches data from cache")
    p_fetch.add_argument("--filter-range", required=False, help="only return a specific range")
    subparsers.add_parser("get_metadata", help="prints spreadsheet's detected metadata")
    p_update = subparsers.add_parser("update", help="sets a specific cell value")
    p_update.add_argument("--a1", required=True,
                          help="A1 identifier of row/cell to change (including sheet name)")
    p_update.add_argument("--value", "--val", required=True, action="append",
                          help="'[column=]value' to update. May be specified multiple times!")
    p_update.add_argument("--dry-run", "-n", action="store_true", required=False, help="Do a dry run (dont update live sheet)")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
    else:
        creds = None
        config = None
        with open(os.path.expanduser(args.config), "r") as f:
            config = yaml.safe_load(f)
        creds = auth_credentials(config.get("google_auth", {}))
        sheetsCfg = config.get("google_sheets", {})
        if args.command == "auth":
            print("Authentication successful (token saved)!")
        elif args.command == "fetch_data":
            do_fetch_data(sheetsCfg, creds, cached=args.cached,
                          filter_range=args.filter_range)
        elif args.command == "get_metadata":
            do_print_metadata(sheetsCfg, creds)
        elif args.command == "update":
            do_update_cell(args, sheetsCfg, creds)

