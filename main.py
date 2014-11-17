"""

The main file that fetches data and does the handles access and calls all the functions 

"""
import numpy as np
import datetime
import calendar
import Message
import Score_v2
import httplib2
import bisect

import pickle

from parse_rest.connection import register
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run
from Peaps import PeapList,UserEntry

import json
import os

import sys

NUM_DAYS = 360*5

from ServerFlag import SERVER

def getAuthPythonFromString(jsonString):
    
    jsonAuth = json.loads(jsonString)
    
    pid = os.getpid()
    print os.getpid()
    
    
    f = open('/root/nodejsPeaps/storage/'+str(pid)+'.storage','w')
    
    storage = jsonAuth
    
    f.write(json.dumps(storage))
    # f.write ("{\"_module\": \"oauth2client.client\", \"token_expiry\": \"2014-09-16T04:53:04Z\", \"access_token\": \"ya29.ggD31F2RmvKTd7QC2koPaK6BZhPhw2IqLstpWkz8rJ7wDtX7kYZ25Vfr\", \"token_uri\": \"https://accounts.google.com/o/oauth2/token\", \"invalid\": false, \"token_response\": ")
    #
    # f.write(jsonString)
    #
    # f.write(", \"client_id\": \"944061120239-tpmp65vqp9h4d6pe52v33fljgmol4o5v.apps.googleusercontent.com\", \"id_token\": {\"aud\": \"944061120239-tpmp65vqp9h4d6pe52v33fljgmol4o5v.apps.googleusercontent.com\", \"cid\": \"944061120239-tpmp65vqp9h4d6pe52v33fljgmol4o5v.apps.googleusercontent.com\", \"iss\": \"accounts.google.com\", \"at_hash\": \"axASjthEjF6RkMc7x0c3sA\", \"exp\": 1409335817, \"azp\": \"944061120239-tpmp65vqp9h4d6pe52v33fljgmol4o5v.apps.googleusercontent.com\", \"iat\": 1409331917, \"token_hash\": \"axASjthEjF6RkMc7x0c3sA\", \"id\": \"103318250095136450821\", \"sub\": \"103318250095136450821\"}, \"client_secret\": \"4PVtNCo_NCNC1agXEB7SSA5p\", \"revoke_uri\": \"https://accounts.google.com/o/oauth2/revoke\", \"_class\": \"OAuth2Credentials\", \"refresh_token\": \"1/ziwThDFsj0GVxSB2fneFka5gjIV3tav9elmEsqJRQ_4\", \"user_agent\": null}")

    f.close()
    

    # Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly profile email'

    # Location of the credentials storage file
    STORAGE = Storage('/root/nodejsPeaps/storage/'+str(pid)+'.storage')

    # Try to retrieve credentials from storage or run the flow to generate them
    credentials = STORAGE.get()
    if credentials is None or credentials.invalid:
        print "invalid credentials"
    print "Done getting credentials"

    # Authorize the httplib2.Http object with our credentials
    http = httplib2.Http()
    http = credentials.authorize(http)

    # Build the Gmail service from discovery
    service_gmail = build('gmail', 'v1', http=http)
    service_user  = build('plus', 'v1', http=http)

    return [service_gmail,service_user]

def getAuthPython(secretFilePath):
    # Combine the relationship matrices of merged E-mail addresses

    """
ARGS : filePath : A string that indicates the path to the client_secret  


RETURNS : A Gmail Service object

    """

    ####

    #Step 1 : Get Authorization from Google :

    ####
    # Path to the client_secret.json file downloaded from the Developer Console
    CLIENT_SECRET_FILE = 'client_secret.json'

    # Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
    OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.readonly profile email https://www.googleapis.com/auth/contacts.readonly'


    # Location of the credentials storage file
    STORAGE = Storage('gmail.storage')

    # Start the OAuth flow to retrieve credentials
    flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
    http = httplib2.Http()

    # Try to retrieve credentials from storage or run the flow to generate them
    credentials = STORAGE.get()
    if credentials is None or credentials.invalid:
        credentials = run(flow, STORAGE, http=http)
    print "Done getting credentials"

    # Authorize the httplib2.Http object with our credentials
    http = credentials.authorize(http)

    # Build the Gmail service from discovery
    service_gmail = build('gmail', 'v1', http=http)
    service_user  = build('plus', 'v1', http=http)

    return [service_gmail,service_user]


def registerToParse():

    register('z0tVwPXHKH0vpQ1elZuedq9yhEfdsuyZzB6gcVtV','4tSjXFZw3rS20QKI6e2fUJH4jwqI9eEDJV7v4wWF')

def getQuery(days, type, forceItem):

    """
        ARG: number of days of the query

        RETURN : string of the query
    """
    user = 'me'

    today = datetime.date.today()
    delta = datetime.timedelta(days)
    t_after = today - delta

    query = 'after:' + t_after.strftime("%Y/%m/%d") + ' before:' + today.strftime("%Y/%m/%d") + ' -in:chats'

    if forceItem != "":
        query += (' ' + forceItem)

    if SERVER == False:
        black_list = [line.strip() for line in open('black_list.txt')]     # don't retrieve emails from the black_list.txt
    elif SERVER == True:
        black_list = [line.strip() for line in open('/root/nodejsPeaps/black_list.txt')]

    for lines in black_list:
        query = query + " -" + lines
    # print query

    if type == 'sent':
        query = query + ' in:sent'

    elif type == 'inbox':
        query = query + ' -in:sent'

    return query

# def getQuery(days, type):

#     """
#         ARG: number of months of the query

#         RETURN : string of the query
#     """
#     user = 'me'

#     today = datetime.date.today()
#     delta = datetime.timedelta(days)
#     t_after = today - delta

#     query = 'after:' + t_after.strftime("%Y/%m/%d") + ' before:' + today.strftime("%Y/%m/%d") + ' -in:chats'

#     if SERVER == False:
#         black_list = [line.strip() for line in open('black_list.txt')]     # don't retrieve emails from the black_list.txt
#     elif SERVER == True:
#         black_list = [line.strip() for line in open('/root/nodejsPeaps/black_list.txt')]


#     for lines in black_list:
#         query = query + " -" + lines
#     # print query

#     if type == 'sent':
#         query = query + ' in:sent'

#     elif type == 'inbox':
#         query = query + ' -in:sent'

#     return query


def getUserName(service):
    user = service.people().get(userId='me').execute()
    return user['displayName']

# Get the user name to identify in the parse database 

def getUserEmail(service):
    user = service.people().get(userId='me').execute()
    print user
    print user['emails'][0]['value']
    return user['emails'][0]['value']


####



def filterResponse(response_all, minNrMessagesInThread):

    '''
    Arg:    list of messages/thread IDs downloaded from Gmail (example: [{u'id': u'14497df03110bebc', u'threadId': u'14497dec79c3a729'}, {u'id': u'14497dec79c3a729', u'threadId': u'14497dec79c3a729'}....
            minimum number of messages per thread to be considered

    Ret:    list of messages/thread IDs filtered
    '''

    threadList = {}
    for x in response_all:
        if threadList.has_key(x['threadId']):
            threadList[x['threadId']].append(x['id'])
        else:
            threadList[x['threadId']] = [x['id']]
    response = []
    for x in response_all:
        pair = {}
        pair['id'] = x['id']
        pair['threadId'] = x['threadId']
        if len(threadList[x['threadId']]) >= minNrMessagesInThread:  # we will only process emails from threats that have at least 2 messages
            response.append(pair)
        else:
            pass
    print '# of messages downloaded: ', len(response_all)
    print '# of messages that we will actually process: ',len(response)
    return response


def findRoot(serviceGmail, serviceUser):  # Edited by FH: uses the user
    root = []
    user = "me" # Use the user who authorized the call
    userData = serviceUser.people().get(userId='me').execute()
    query = 'in:sent'
    try:
        userEmail = userData['emails'][0]['value']
        root.append(userEmail)
        query = 'in:sent' + ' -' + userEmail
    except:
        pass

    # max maxResults = 10


    # response = Message.ListMessagesMatchingQuery(service, user, query)
    response = serviceGmail.users().messages().list(userId=user, q=query, maxResults=1).execute()
    numberOfMessages = response['resultSizeEstimate']

    while numberOfMessages:
        messageID = response['messages'][0]['id']
        # extract the vFrom
        msg = Message.GetMessage(serviceGmail, user, messageID)

        for i in range(len(msg['payload']['headers'])):
            name = msg['payload']['headers'][i]['name']
            value = msg['payload']['headers'][i]['value']
            if name == 'From':
                vFrom = Message.extractEmails(value)
                if vFrom[0] not in root:
                    root.append(vFrom[0])
                    print root
                    query = query + ' -' + vFrom[0]
        response = serviceGmail.users().messages().list(userId=user, q=query).execute()
        numberOfMessages = response['resultSizeEstimate']
    return root


#@profile
def main():

    # 0. Register the application to Parse

    registerToParse()

    # 1. set up time format
    d = datetime.datetime.utcnow()

    # 2. Get Authorization

    t0 = calendar.timegm(d.utctimetuple())
    
    # Local
    if SERVER == False:
        service = getAuthPython('client_secret.json')
    elif SERVER == True:
        service = getAuthPythonFromString(sys.argv[1])

    # Server
    #service = getAuthPythonFromString(sys.argv[1])

    # 3. Get Query
    # query_all = getQuery(NUM_DAYS, 'all')


    # 4. Run the query

    user = "me" # Use the user who authorized the call
    userName = getUserEmail(service[1])


    # 4.5 Check whether we have the user in the database

    # Check if user already had his mailbox processed:
    userEntries = UserEntry.Query.filter(uemail = userName)

    if len(userEntries) == 0:
        print "User logging in for the first time, creating a database entry on Parse"
        
        userEntry = UserEntry(uemail = userName, userCreated=t0, lastLogin=t0, 
            mailboxProcessed=False, lastMailboxUpdate=t0, numAppOpened=1)

        userEntry.save()
    
    elif len(userEntries) == 1:
        print "User found - updating access statistics"

        userEntry = userEntries[0]
        userEntry.increment("numAppOpened")
        userEntry.lastLogin = t0

        userEntry.save()

        if userEntry.mailboxProcessed == True:
            print "User's mailbox already processed, quitting..."
            sys.exit(0)

    else:
        print "Duplicate entries for user, check database consistency"
        print "Quitting..."
        sys.exit(0)

    userTest = service[1].people().get(userId='me').execute()


    # 4.75. Set up the query and get all the messages that match
    query_sent = getQuery(NUM_DAYS, 'sent', "")
    response_sent = Message.ListMessagesMatchingQuery(service[0], user, query_sent)

    recipients = Message.extractRecipients(response_sent, user, service[0])

    # print "Recipients", recipients

    # Group recipients into 10s to decrease the number of queries
    accumulatedRecipients = []
    for i in range(0, len(recipients), 10):
        accumulatedRecipients.append(" OR ".join(recipients[i:i+10]))

    # print "Accumulated recipients:", accumulatedRecipients


    emails_to_process = set()
    for recipient_email in accumulatedRecipients:
        query_section = getQuery(NUM_DAYS, 'all', recipient_email)
        response_section = Message.ListMessagesMatchingQuery(service[0], user, query_section)

        for x in response_section:
            emails_to_process.add( (x["id"], x["threadId"]) )


    response_all = [{'id': item[0], 'threadId': item[1]} for item in emails_to_process]

    #query_all = getQuery(NUM_DAYS, 'all', "")
    #response_all = Message.ListMessagesMatchingQuery(service[0], user, query_all)






    root = findRoot(service[0],service[1])


    # 5. this section is to reduce the nr of emails that will be processed

    # TODO: think about speed vs. comprehensive data tradeoff
    response = filterResponse(response_all, 2)

    # 6. Process the inbox

    pl = PeapList(userName)
    Message.Process_Inbox_peapFH(response, user, service[0], root, pl)

    # 6.5 Filter the peaplist to peaps the user might be interested in
    pl.eliminatePeapsWithoutRelationship()

    # 6.6 Try to set the primary name to the most meaningful from the saved names
    pl.chooseBestNames()
    
    # 7. Calculate scores (new Zaman's algorithm). Scores are stored in each object


    # Save another pickle for debugging purposes
    # if SERVER == False:
    #     f2 = open("mtPeapList_noscore.dat","w")
    #     pickle.dump(pl, f2)
    #     f2.close()


    print 'Nr. of peaps: ', len(pl.list)



    # Calculate all the score components
    pl.calculateNumEmails()
    pl.calculateThetas()
    pl.calculateEntropies(NUM_DAYS, 7)
    pl.calculateDomainStats(root)
    pl.calculateDurations(NUM_DAYS)



    pl.calculateScopeScores()
    
    #calculateScopeScore(pl)


    # 8. Define the list of peaps in scope. The first 150 peaps in the list will be in the scope

    #scopeListPeapsID, scopeListValues = definePeapsInScope(pl, 150)

    pl.sortPeapsByScopeScore(150)


    # 9. Calculate priority as as a function of lastContacted and score for every peap. Potential improvement: we could modify this to calculate priority only for peaps in scope

    #priorityListPeapsID, priorityListValues = calculatePriorityScore(pl)
    pl.calculatePriorityScores(150)  # Edited by FH

    pl.calculateEntropies(NUM_DAYS, 7)

    # 9.5 - Save the peaps in scope to the parse server
    pl.uploadPeapsToParse()



    # 10. Test, print lists

    if SERVER == False:
        f = open("mtPeapList.dat", "w")
        pickle.dump(pl, f)
        f.close()    

    if SERVER == True and userName == 'mturek92@gmail.com':
        f = open("/root/nodejsPeaps/peapLists/mt.dat", "w")
        pickle.dump(pl, f)
        f.close()

    if SERVER == True and userName == 'nalbana@gmail.com':
        f = open("/root/nodejsPeaps/peapLists/an.dat", "w")
        pickle.dump(pl, f)
        f.close()

    if SERVER == True and userName == 'francisco.hidalgo@gmail.com':
        f = open("/root/nodejsPeaps/peapLists/fh.dat", "w")
        pickle.dump(pl, f)
        f.close()




    if SERVER == False:
        d = datetime.datetime.utcnow()
        now = calendar.timegm(d.utctimetuple())/(24*60*60.0)

        print '\n','This is the list of peaps in scope','\n\n'

        c = 0
        for peap in pl.list:
            c+=1
            scopeScore = peap.getScopeScore()
            scopeStatusAutomatic = peap.getScopeStatusAutomatic()

            print c, '. ', peap.getName(), '-->', scopeScore, 'scopeStatusAutomatic:', scopeStatusAutomatic 


        print '\n','This is the list prioritized peaps','\n\n'
        

        peapsByPriority = sorted(pl.list, key = lambda x: x.scopeInfo["priorityScore"], reverse = True)
        for x in range(0, min(150, len(pl.list))):
            peap = peapsByPriority[x]

            priorityScore = peap.getPriorityScore()
            scopeScore = peap.getScopeScore()

            print x, '. ', peap.getName(), '-->', priorityScore, 'scopeScore:', scopeScore

        tf = calendar.timegm(d.utctimetuple())
        print 'the whole process took: ', tf - t0, ' seconds'

    if SERVER == True:
        print 'finished successfully'

        d = datetime.datetime.utcnow()
        tf = calendar.timegm(d.utctimetuple())
        print 'the whole process took: ', tf - t0, ' seconds'


if __name__ == "__main__":
    main()
