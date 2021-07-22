from __future__ import print_function
from gtts import gTTS
import datetime
import genclips
import pickle
import os
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# "Readable Time Format"
RTF = "%m/%d/%Y, %I:%M %p"

# "Google Calendar API Time"
GCAT = "%Y-%m-%dT%H:%M:%S"

# Save text to mp3 and read it
def read(text):
    print(text)
    tts = gTTS(text=text, lang='en')
    tts.save('clips/output.mp3')
    os.system('omxplayer --no-osd clips/output.mp3')

# Play pre-existing mp3 file
def play(file):
    os.system('omxplayer --no-osd clips/' + str(file))

#pylint: disable=no-member
def main():

    # Handle credentials at startup
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Generate static clips
    if not os.path.isfile('clips/none_today.mp3'):
        genclips.genToday()
    if not os.path.isfile('clips/none_tomorrow.mp3'):
        genclips.genTomorrow()
    if not os.path.isfile('clips/none_week.mp3'):
        genclips.genWeek()
    if not os.path.isfile('clips/none_month.mp3'):
        genclips.genMonth()
    if not os.path.isfile('clips/hello.mp3'):
        genclips.genHello()

    # Let user know application is started
    print('Hello!')
    play('hello.mp3')

    # Main handler loop
    while True:
        num = input("Press Enter to continue...\n")
        if num == ' ':
            break
        if num == '':
            now = datetime.datetime.now()
            read("It is " + now.strftime(RTF))
        num = num[-1:]
        try:
            num = int(num)
        except:
            continue

        now = datetime.datetime.now()
        start = datetime.datetime(now.year, now.month, now.day)

        if num == 0: # today, starting at current time
            print("Listing the rest of today's events...")
            end = start + datetime.timedelta(days=1)
            start = now
        elif num == 1: # tomorrow
            print("Listing all of tomorrow's events...")
            start = start + datetime.timedelta(days=1)
            end = start + datetime.timedelta(days=1)
        elif num == 2: # one week, starting at current time
            print("Listing the events for the next 7 days...")
            end = start + datetime.timedelta(weeks=1)
            start = now
        elif num == 3: # one month, starting at current time
            print("Listing the events for the next 4 weeks...")
            end = start + datetime.timedelta(weeks=4)
            start = now
        else:
            continue

        timeMin = start.astimezone(datetime.timezone.utc).isoformat()
        timeMax = end.astimezone(datetime.timezone.utc).isoformat()

        service = build('calendar', 'v3', credentials=creds)
        cidFile = open('cid.txt', 'r')
        calendarId = cidFile.read()
        cidFile.close()
        events_result = service.events().list(calendarId=calendarId, timeMin=timeMin, timeMax=timeMax, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        if not events:
            if num == 0:
                print("No appointments for the rest of the day")
                play('none_today.mp3')
            elif num == 1:
                print("No appointments tomorrow")
                play('none_tomorrow.mp3')
            elif num == 2:
                print("No appointments in the next 7 days")
                play('none_week.mp3')
            elif num == 3:
                print("No appointments in the next 4 weeks")
                play('none_month.mp3')
        for event in events:
            summary = event['summary']
            try:
                description = event['description']
            except:
                description = ''
            start = datetime.datetime.strptime(event['start'].get('dateTime')[:-6], GCAT).strftime(RTF)
            end = datetime.datetime.strptime(event['end'].get('dateTime')[:-6], GCAT).strftime(RTF)
            print()
            print(summary + ":")
            print(description)
            print("\tSTART: " + start)
            print("\t  END: " + end)
            read(summary + ", " + description + ", starting at " + start + ", ending at " + end)
        print()

if __name__ == '__main__':
    main()