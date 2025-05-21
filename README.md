# Google Contacts Birthdays to ICS

This script fetches birthday data from your Google Contacts and generates `.ics` calendar files that can be imported into Google Calendar (or any other calendar app supporting the iCalendar format).

## Features

- Fetches birthdays from Google Contacts (via Google People API)
- Generates future birthday events up to **n years ahead**
- Supports people **with and without birth years**
- Splits `.ics` files to avoid exceeding the Google Calendar [file size limit (max ~1MB)](https://support.google.com/calendar/answer/45654?hl=en#zippy=)
- Written in pure Python using standard and widely-used libraries

## Setup

### 1. Prerequisites

- Python 3.7+
- A [Google Cloud project](https://console.cloud.google.com/) with the **People API** enabled, can be activated at [https://console.cloud.google.com/apis/library/people.googleapis.com](https://console.cloud.google.com/apis/library/people.googleapis.com)
- OAuth 2.0 client credentials (`credentials.json`), can be created at [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client icalendar
```

### 3. OAuth Credentials

Place your `credentials.json` (downloaded from your Google Cloud console) in the root directory of the project.

When running the script for the first time, a browser window will open asking you to authenticate. This will create a `token.json` to cache the credentials for future use.

## Usage

```bash
python google_contacts_birthdays_to_ics.py
```

- The script will generate one or more `.ics` files in the current directory (e.g. `geburtstage_1.ics, geburtstage_2.ics`, etc.).
- Each `.ics` file contains up to 4000 birthday events to stay under Google's ~1MB import limit.
- Events will include:
  - Year-based birthdays (e.g. “Alice turns 30”) if a birth year is known
  - Recurring-style yearly birthdays (e.g. “Bob's birthday”) for contacts without a year

## Limitations

ICS import is manual: The generated `.ics` files must be imported into Google Calendar manually. Google does not currently support programmatic `.ics` file imports via API.

Calendar lifetime: Since birthdays are generated up to a limited number of years ahead (currently 5 years, configurable via `YEARS_AHEAD`), the simplest way to keep the calendar updated in the future is:

1. Delete the old imported calendar from Google Calendar
2. Re-run the script
3. Re-import the newly generated `.ics` files

## Customization

You can adjust:

- `YEARS_AHEAD` = 5: How many years into the future birthdays should be generated
- `MAX_EVENTS_PER_FILE` = 4000: Maximum number of events per .ics file to avoid file size limits
