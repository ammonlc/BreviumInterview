import requests
import json
from datetime import date, timedelta
import copy

authToken = "e33ffe4a-82d6-4705-9138-f6856bbb6a70"

# calls start API with authToken so we can get the rest of the data
def start():
    url = f"http://scheduling-interview-2021-265534043.us-west-2.elb.amazonaws.com/api/Scheduling/Start?token={authToken}"
    headers = {
    'accept': '*/*'
    }
    requests.request("POST", url, headers=headers)
    
# calls schedule API with authToken, gives us the initial schedule
def getStartingSchedule():
    url = f"http://scheduling-interview-2021-265534043.us-west-2.elb.amazonaws.com/api/Scheduling/Schedule?token={authToken}"
    headers = {
    'accept': 'text/plain'
    }
    r = requests.request("GET", url, headers=headers)
    with open(f"response.json", "w") as outfile:
        outfile.write(r.text)

# generates a dictionary of all possible appointments between 2 dates
def generatePossibleAppointments():
    openAppointments = {}
    start_date = date(2021, 11, 1)
    end_date = date(2021, 12, 31)
    delta = timedelta(days=1)
    while start_date <= end_date:
        if(start_date.isoweekday() < 6): # if date is M-F
            start_date_str = str(start_date.year) + "-" + str(start_date.month) + "-" + str(start_date.day)
            openAppointments[start_date_str] = [8,9,10,11,12,1,2,3,4]
        start_date += delta
    return openAppointments

# looks through data, lets us know how many doctors there are
def getNumberOfDoctors(data):
    doctorIds = []
    for row in data:
        doctorIds.append(row['doctorId'])
    doctorIds = [*set(doctorIds)]
    return len(doctorIds)

# generates a dictionary of all currently available appointments for each doctor from starting schedule
def getOpenAppointments():
    with open("response.json",'r') as file:
        data = json.load(file)
    openAppointments = generatePossibleAppointments()
    numberOfDoctors = getNumberOfDoctors(data)
    allAppointmentsAvailable = {}
    for i in range(numberOfDoctors):
        allAppointmentsAvailable[f'{i + 1}'] = copy.deepcopy(openAppointments)
    for row in data:
        doctorNum = str(row['doctorId'])
        time = row['appointmentTime']
        year, month, day = time.split('T')[0].split('-')
        date = str(year) + '-' + str(month) + '-' + str(int(day))
        time = int(time.split('T')[1].split(':')[0])
        if time > 12:
            time = time - 12
        allAppointmentsAvailable[doctorNum][date].remove(time)
        # TODO: add dictionary for each patient ID
    return allAppointmentsAvailable

# calls appointment request API to get next appointment to be scheduled
def getAppointmentDetails():
    url = "http://scheduling-interview-2021-265534043.us-west-2.elb.amazonaws.com/api/Scheduling/AppointmentRequest?token=e33ffe4a-82d6-4705-9138-f6856bbb6a70"

    headers = {
        'accept': 'text/plain'
    }
    response = requests.request("GET", url, headers=headers)
    return response.text

# calls schedule API to mark appointment as taken
def postAppointment(request):
    url = f"http://scheduling-interview-2021-265534043.us-west-2.elb.amazonaws.com/api/Scheduling/Schedule?token={authToken}"
    payload = json.dumps(request)
    headers = {
        'accept': '*/*',
        'Content-Type': 'application/json'
    }
    requests.request("POST", url, headers=headers, data=payload)

def getPreferredDays(daysList):
    preferredDays = []
    for item in daysList:
        year, month, day = item.split('T')[0].split('-')
        preferredDays.append(str(int(year)) + '-' + str(int(month)) + '-' + str(int(day)))
    return preferredDays

# gets new appointment to add, finds a time in the schedule, and adds it
def addAppointment(myList):
    with open("appointment.json",'r') as file:
        appointment = json.load(file)
    preferredDoc = appointment['preferredDocs']
    preferredDays = getPreferredDays(appointment['preferredDays'])
    apptDoctor = ''
    apptTime = ''
    for doctor in preferredDoc:
        for date in preferredDays:
            doctorTimesAvailable = myList[str(doctor)]
            dayTimesAvailable = doctorTimesAvailable[date]
            if appointment["isNew"]:
                # TODO: if new appointment is new patient, must be at 3 or 4 on days available
                if 3 in dayTimesAvailable:
                    apptTime = 3
                    break
                elif 4 in dayTimesAvailable:
                    apptTime = 4
                    break
            elif len(dayTimesAvailable) > 0:
                # TODO: schedule patient
                apptTime = dayTimesAvailable[0]
                break
    dayTimesAvailable.remove(apptTime)
    apptDoctor = doctor
    myList[str(doctor)][date] = dayTimesAvailable
    # TODO: patient cannot be scheduled 2x in same 7-day period
    # TODO: convert apptTime & date from int to UTC
    request = {
        "doctorId": apptDoctor,
        "personId": appointment["personId"],
        "appointmentTime": apptTime,
        "isNewPatientAppointment": appointment["isNew"],
        "requestId": appointment["requestId"]
    }
    postAppointment(request)
    return myList

# start()
# getStartingSchedule()
myList = getOpenAppointments()
# TODO: addAppointment in while loop...while getAppointmentDetails does not return 204 code
addAppointment(myList)