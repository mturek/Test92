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
from Peaps import PeapList

NUM_DAYS = 360

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


def getQuery(days, type):

    """
        ARG: number of months of the query

        RETURN : string of the query
    """
    user = 'me'

    today = datetime.date.today()
    delta = datetime.timedelta(days)
    t_after = today - delta

    query = 'after:' + t_after.strftime("%Y/%m/%d") + ' before:' + today.strftime("%Y/%m/%d") + ' -in:chats'

    black_list = [line.strip() for line in open('black_list.txt')]     # don't retrieve emails from the black_list.txt

    for lines in black_list:
        query = query + " -" + lines
    # print query

    if type == 'sent':
        query = query + ' in:sent'

    elif type == 'inbox':
        query = query + ' -in:sent'

    return query


def getUserName(service):
    user = service.people().get(userId='me').execute()
    return user['displayName']


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


def calculateScopeScore(pl):

    '''
    Arg: pl

    This section iterates over the list of peaps and tries to calculate and save the score for each one

    '''

    sumOfWeightedNum = 0

    #log = open("log", "w")

    #for peapID in range(0,len(pl.list)):    
    for peap in pl.list:    
        try:
            time, sender = Score_v2.get_time_sender(peap)
            parameters = Score_v2.convofit(sender, time)


            """ MT EDIT"""
            theta = parameters[0]
            A = parameters[1]
            weightedNum = Score_v2.get_weighted_num_emails(peap)
            sumOfWeightedNum += weightedNum


            score = weightedNum
            #score = theta * (1-theta)
            #score = 0.5*parameters[0]+0.5*parameters[1] # Using alpha and theta

            #log.write(peap.getName() +","+str(len(peap.getMessageIDs()))+","+str(NUM_DAYS)+","+str(theta)+"\n")

            """ END MT EDIT """

            peap.setScopeScore(score)

        except:
            print "Exception: " + peap.getName()       

    #log.close()

    # Normalize the weightedNum, make sure to change this
    # when the score takes into account theta
    for peap in pl.list:
        if peap.getScopeScore() != -1:
            peap.setScopeScore(peap.getScopeScore()/sumOfWeightedNum)


def definePeapsInScope(pl, nrOfPeapsInScope):
    '''
    Arg:    pl
            Number of People in Scope

    Return: List of peaps' IDs (scopeScore's descending ordered)
            List of peaps' scopeScore (descending ordered)
    '''

    scopeListPeapsID_inv = []
    scopeListValues_inv = []
    for peap in pl.list:

        scopeScore = peap.getScopeScore()

        if len(scopeListValues_inv) == 0:
            scopeListPeapsID_inv.append(peap.getID())
            scopeListValues_inv.append(scopeScore)
        else:
            ins = bisect.bisect_left(scopeListValues_inv,scopeScore,0,len(scopeListValues_inv))
            scopeListPeapsID_inv.insert(ins,peap.getID())
            scopeListValues_inv.insert(ins,scopeScore)

    scopeListPeapsID = scopeListPeapsID_inv[::-1]
    scopeListValues = scopeListValues_inv[::-1]

    for x in range(min(nrOfPeapsInScope, len(scopeListPeapsID)-1)):
        peapID = scopeListPeapsID[x]
        pl.getPeapByID(peapID).setScopeStatusAutomatic(1)

    return scopeListPeapsID, scopeListValues


def calculatePriorityScore(pl):

    '''

    Arg:    pl

    Return: priorityListPeapsID: list of peapsIDs (priorityScore's descending order)
            priorityListValues: list of priority values (descending order)
    '''


    priorityListPeapsID_inv = []
    priorityListValues_inv = []
    d = datetime.datetime.utcnow()
    now = calendar.timegm(d.utctimetuple())/(24*60*60.0)

    #for peapID in range(0,len(pl.list)):
    for peap in pl.list:

        time_no_contact = now - peap.getLastContacted()
        scopeScore = peap.getScopeScore()

        # WE NEED A BETTER FUNCTION HERE
        prio =  scopeScore * np.exp(-time_no_contact/10)

        peap.setPriorityScore(prio) # adds the priorityScore to each peap

        if len(priorityListValues_inv) == 0:
            priorityListPeapsID_inv.append(peap.getID())
            priorityListValues_inv.append(prio)
        else:
            ins = bisect.bisect_left(priorityListValues_inv,prio,0,len(priorityListValues_inv))
            priorityListPeapsID_inv.insert(ins,peap.getID())
            priorityListValues_inv.insert(ins,prio)

    priorityListPeapsID = priorityListPeapsID_inv[::-1]
    priorityListValues = priorityListValues_inv[::-1]

    return priorityListPeapsID, priorityListValues


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




if __name__ == "__main__":

    # 0. Register the application to Parse

    registerToParse()

    # 1. set up time format
    d = datetime.datetime.utcnow()

    # 2. Get Authorization

    t0 = calendar.timegm(d.utctimetuple())
    service = getAuthPython('client_secret.json')

    # 3. Get Query
    """ MT EDIT """
    query_all = getQuery(NUM_DAYS, 'all')
    """ END MT EDIT """


    # 4. Run the query

    user = "me" # Use the user who authorized the call
    userName = getUserName(service[1])

    userTest = service[1].people().get(userId='me').execute()

    response_all = Message.ListMessagesMatchingQuery(service[0], user, query_all)

    root = findRoot(service[0],service[1])


    # 5. this section is to reduce the nr of emails that will be processed

    response = filterResponse(response_all, 2)

    # 6. Process the inbox

    pl = PeapList(userName)
    Message.Process_Inbox_peapFH(response, user, service[0], root, pl)

    
    # 7. Calculate scores (new Zaman's algorithm). Scores are stored in each object

    print 'Nr. of peaps: ', len(pl.list)
    calculateScopeScore(pl)


    # 8. Define the list of peaps in scope. The first 150 peaps in the list will be in the scope

    scopeListPeapsID, scopeListValues = definePeapsInScope(pl, 150)

    # 9. Calculate priority as as a function of lastContacted and score for every peap. Potential improvement: we could modify this to calculate priority only for peaps in scope

    priorityListPeapsID, priorityListValues = calculatePriorityScore(pl)


    # 10. Test, print lists

    """ MT DEBUG """
    
    f = open("mtPeapList.dat", "w")
    pickle.dump(pl, f)
    f.close()    

    """ END MT DEBUG """

    d = datetime.datetime.utcnow()
    now = calendar.timegm(d.utctimetuple())/(24*60*60.0)

    print '\n','This is the list of peaps in scope','\n\n'
    c = 0
    for peapID in scopeListPeapsID:
        c = c + 1
        scopeScore = pl.getPeapByID(peapID).getScopeScore()
        scopeStatusAutomatic = pl.getPeapByID(peapID).getScopeStatusAutomatic()
        print c, '. ', pl.getPeapByID(peapID).getName(), '-->', scopeScore, 'scopeStatusAutomatic: ',scopeStatusAutomatic

    print '\n','This is the list prioritized peaps','\n\n'
    for x in range(0, min(len(priorityListPeapsID),150)):
        peapID = scopeListPeapsID[x]
        peap = pl.getPeapByID(peapID)

        priorityScore = peap.getPriorityScore()
        time_no_contact = now - peap.getLastContacted()
        scopeScore = peap.getScopeScore()
        print x, '. ', peap.getName(), ' priority score: ', priorityScore, 'scope score: ', scopeScore, 'lastContacted', time_no_contact

        # Save Peaps
        peap.savePeap() #  WHAT DO WE USE THIS LINE FOR? PARSE?

    tf = calendar.timegm(d.utctimetuple())
    print 'the whole process took: ', tf - t0, ' seconds'

	
