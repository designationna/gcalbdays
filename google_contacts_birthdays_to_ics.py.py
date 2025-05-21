import datetime
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from icalendar import Calendar, Event

# OAuth scope: read-only access to Google Contacts
SCOPES = ['https://www.googleapis.com/auth/contacts.readonly']

# Max number of events per .ics file (to stay below 1MB for Google Calendar import)
MAX_EVENTS_PER_FILE = 4000

# Number of future years to generate birthday events for
YEARS_AHEAD = 5

def authenticate():
    """Handles authentication using OAuth2 and returns valid credentials."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh()
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def fetch_birthdays(service):
    """Fetches contacts with birthdays from Google People API."""
    people = []
    results = service.people().connections().list(
        resourceName='people/me',
        pageSize=2000,
        personFields='names,birthdays',
    ).execute()
    connections = results.get('connections', [])

    for person in connections:
        names = person.get('names', [])
        birthdays = person.get('birthdays', [])
        if names and birthdays:
            name = names[0].get('displayName')
            for b in birthdays:
                date = b.get('date')
                if date and 'month' in date and 'day' in date:
                    year = date.get('year')
                    people.append((name, year, date['month'], date['day']))
    return people

def create_calendars_split(people, max_events_per_file=MAX_EVENTS_PER_FILE):
    """Creates one or more .ics calendar files with birthday events, splitting when necessary."""
    calendars = []
    cal = Calendar()
    cal.add('prodid', '-//Birthday Calendar//mxm.dk//')
    cal.add('version', '2.0')

    today = datetime.date.today()
    end_year = today.year + YEARS_AHEAD
    event_count = 0
    file_index = 1

    def save_calendar(cal_to_save, idx):
        filename = f'birthdays_{idx}.ics'
        with open(filename, 'wb') as f:
            f.write(cal_to_save.to_ical())
        print(f"File created: {filename}")

    for name, year, month, day in people:
        if year:
            # With birth year: generate events for future birthdays including age
            for offset in range(1, 101):
                bday_year = year + offset
                if today.year <= bday_year <= end_year:
                    try:
                        bday = datetime.date(bday_year, month, day)
                    except ValueError:
                        continue
                    age = bday_year - year
                    event = Event()
                    event.add('summary', f'{name} turns {age}')
                    event.add('dtstart', bday)
                    event.add('dtend', bday + datetime.timedelta(days=1))
                    event.add('description', f"{name}'s {age}th birthday.")
                    event['uid'] = f'{name}-{bday}@birthdaycalendar.local'
                    event.add('transp', 'TRANSPARENT')
                    cal.add_component(event)
                    event_count += 1

                    if event_count >= max_events_per_file:
                        save_calendar(cal, file_index)
                        file_index += 1
                        cal = Calendar()
                        cal.add('prodid', '-//Birthday Calendar//mxm.dk//')
                        cal.add('version', '2.0')
                        event_count = 0
        else:
            # Without birth year: add recurring yearly events for the next few years
            for year_offset in range(YEARS_AHEAD):
                target_year = today.year + year_offset
                try:
                    bday = datetime.date(target_year, month, day)
                except ValueError:
                    continue
                event = Event()
                event.add('summary', f"{name}'s birthday")
                event.add('dtstart', bday)
                event.add('dtend', bday + datetime.timedelta(days=1))
                event.add('description', f"Birthday of {name} (no year provided).")
                event['uid'] = f'{name}-{month:02d}{day:02d}-{target_year}@birthdaycalendar.local'
                event.add('transp', 'TRANSPARENT')
                cal.add_component(event)
                event_count += 1

                if event_count >= max_events_per_file:
                    save_calendar(cal, file_index)
                    file_index += 1
                    cal = Calendar()
                    cal.add('prodid', '-//Birthday Calendar//mxm.dk//')
                    cal.add('version', '2.0')
                    event_count = 0

    if event_count > 0:
        save_calendar(cal, file_index)

def main():
    creds = authenticate()
    service = build('people', 'v1', credentials=creds)

    print("Fetching birthdays...")
    people = fetch_birthdays(service)
    print(f"Found {len(people)} contacts with birthdays.")

    create_calendars_split(people)
    print("Done. .ics calendar files were created.")

if __name__ == '__main__':
    main()
