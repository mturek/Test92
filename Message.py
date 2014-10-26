"""
	this file deals with all the functionality to get and manipulate message data

"""

import re
import time
import Merge
import base64
import socket

from apiclient import errors
from email.utils import parsedate


def ListMessagesMatchingQuery(service, user_id, query):
  """List all Messages of the user's mailbox matching the query.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    query: String used to filter messages returned.
    Eg.- 'from:user@some_domain.com' for Messages from a particular sender.

  Returns:
    List of Messages that match the criteria of the query. Note that the
    returned list contains Message IDs, you must use get with the
    appropriate ID to get the details of a Message.
  """
  try:
    response = service.users().messages().list(userId=user_id,q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError, error:
    print 'An error occurred: %s' % error

 ####


def GetMessage(service, user_id, msg_id):
  """Get a Message with given ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    msg_id: The ID of the Message required.

  Returns:
    A Message.
  """
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    # print 'Message snippet: %s' % message['snippet']
    return message
  except (socket.error,errors.HttpError) as error:
    print 'An error occurred: %s' % error
    print 'Message ID:', msg_id
    
    message = {
        'payload': {
            'headers': []
        }
    } 

    return message


def extractEmailsAndName(string):

    """
    ARGS : A raw string of Email
    RETURN : A list of Email and Name
    """

    #print string
    string = string.lower()

    # Get the name as well, we need that for the merging round
    temp = string.split(' <')
    name = ""
    if len(temp) > 1:
        name = temp[0]
    #  print name

    foundemail = []
    mailsrch = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
    foundemail.extend(mailsrch.findall(string)) # this extends the previously named list via the "mailsrch" variable which was named before
    #print [ foundemail , name ]
    return [ foundemail , name ]


def extractEmails(string):

    """
    ARGS : A raw string of Email
    RETURN : A list of Email and Name
    """

    #print string
    string = string.lower()

    # Get the name as well, we need that for the merging round
    temp = string.split(' <')
    name = ""
    if len(temp) > 1:
        name = temp[0]
    #  print name

    foundemail = []
    mailsrch = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}')
    foundemail.extend(mailsrch.findall(string)) # this extends the previously named list via the "mailsrch" variable which was named before
    return foundemail

def validateFieldValue(value):
    if '\"' in value:
        segments = value.split('\"')

        #Even segments are within \" ... \" -> replace commas with ;
        for index in range(1,len(segments),2):
            segments[index] = segments[index].replace(",",";")

        value = "".join(segments)

    return value


def Process_Inbox_peapFH(response, user, service, root, pl):

    count = 0

    for x in response: # Loops over every email in the query
        msg_id = x['id'] # gives back an email id
        msg = GetMessage(service, user, msg_id) # gets back 'full' data from email
        vTo = [[],""]
        vCc = [[],""]
        vBcc = [[],""]
        vFrom = [[],""]
        countFrom = 0
        countTo = 0
        countCc = 0
        countBcc = 0

        messageSubject = "N/A"
        messageBody = "N/A"

        # A list of users that are merged together if they have the same name
        nameEmailList = []

        # prints every 100 loops
        count = count + 1
        if count%100 == 0:
            print count

        # loops over a list of headers
        Direction = -1

        #print x
        # if msg["payload"]["body"]["size"] != 0:
        #     bodyParts = [msg["payload"]["body"]["data"]]
        # elif "parts" in msg["payload"].keys():
        #     bodyParts = [part["body"]["data"] for part in msg["payload"]["parts"] if part["mimeType"] in ["text/plain", "text/html"] and "data" in part["body"].keys()] 
        # else:
        #     bodyParts = []

        # messageBody = " ".join([base64.urlsafe_b64decode(part.encode("UTF-8")).replace("\r\n","\n") for part in bodyParts])

        #Placeholder for messageBody
        messageBody = "N/A"

        for i in range(len(msg['payload']['headers'])):
            name = msg['payload']['headers'][i]['name']
            value = msg['payload']['headers'][i]['value']

            if name == 'Subject':
                messageSubject = value

            if name == 'From' and value != "":


                # By using the function from merge.py, the following function gets the Email Address and the name from the Email. This info can later be used to perform merge

                try:
                    nameEmail = Merge.get_name_and_email(value)
                    if not "Null" in nameEmail:
                        nameEmailList.append(nameEmail)

                except:
                    pass

                vFrom = extractEmailsAndName(value)

                countFrom = len(vFrom[0])
                for email in root:
                    if email in vFrom[0]:
                        Direction = 1


            if name == 'To' and value != "":
                value = validateFieldValue(value)

                pList = value.split(',')
                for p in pList:
                    try:
                        nameEmail = Merge.get_name_and_email(p) 
                        if not "Null" in nameEmail:
                            nameEmailList.append(nameEmail)
                           
                           # nameEmailList.append(Merge.get_name_and_email(p))
                        #print 'to',Merge.get_name_and_email(value)
                    except:
                        pass

                vTo = extractEmailsAndName(value)

                countTo = len(vTo[0])

            if name == 'Cc' and value != "":

                value = validateFieldValue(value)

                pList = value.split(',')
                for p in pList:
                    try:
                        nameEmail = Merge.get_name_and_email(p) 
                        if not "Null" in nameEmail:
                            nameEmailList.append(nameEmail)
                        #nameEmailList.append(Merge.get_name_and_email(p))
                        #print 'to',Merge.get_name_and_email(value)
                    except:
                        pass

                vCc = extractEmailsAndName(value)
                countCc = len(vCc[0])
            if name == 'Bcc' and value != "":
                value = validateFieldValue(value)

                pList = value.split(',')
                for p in pList:
                    try:
                        nameEmail = Merge.get_name_and_email(p) 
                        if not "Null" in nameEmail:
                            nameEmailList.append(nameEmail)
                        #nameEmailList.append(Merge.get_name_and_email(p))
                        #print 'to',Merge.get_name_and_email(value)
                    except:
                        pass

                vBcc = extractEmailsAndName(value)
                countBcc = len(vBcc[0])
            if name == 'Date':
                try:
                    t = time.mktime(parsedate(value))
                except:
                    pass
        users = vFrom[0] + vTo[0] + vCc[0] + vBcc[0]

        y = (t,Direction, countTo, countCc, countBcc)

        # where is the user on the email? (find highest position)
        userField = ""
        for email in root:
            if email in vFrom[0]:
                userField = "From"
            elif email in vTo[0]:
                if not userField in ["From"]:
                    userField = "To"
            elif email in vCc[0]:
                if not userField in ["From", "To"]:
                    userField = "Cc"
            elif email in vBcc[0]:
                if not userField in ["From", "To", "Cc"]:
                    userField = "Bcc"

        if userField == "":
            userField = "None"


        # If the user is not on the email, don't record the email!
        if userField == "None":
            #print "User not on email, skipping: " + messageSubject
            continue

        for nameEmail in nameEmailList:
            if nameEmail[0] == "Null" or nameEmail[1] == "Null":
                print "Found null"
                print nameEmail
                print x

        # if the email is in root, just skip ;
        for nameEmail in nameEmailList:
            #print nameEmail[0] + '\n'
            if nameEmail[0] in root:
                continue

            if nameEmail[1]==" " or nameEmail[1]== "" or nameEmail[1] == '"':
                nameEmail[1]=nameEmail[0]

            # 1. Check if the Peap exists:

            p = pl.getPeapByName(nameEmail[1],fuzzy=True)

            if p == -1:
                p = pl.getPeapByEmail(nameEmail[0])

            # 2. It doesn't exist:

            if p == -1:
                p = pl.addPeap(nameEmail[1],nameEmail[0])

                print "New peap added: ", nameEmail[1], nameEmail[0]
                #add message

                peapEmail = nameEmail[0]

                peapField = ""
                if peapEmail in vFrom[0]:
                    peapField = "From"
                elif peapEmail in vTo[0]:
                    if not peapField in ["From"]:
                        peapField = "To"
                elif peapEmail in vCc[0]:
                    if not peapField in ["From", "To"]:
                        peapField = "Cc"
                elif peapEmail in vBcc[0]:
                    if not peapField in ["From", "To", "Cc"]:
                        peapField = "Bcc"
                else:
                    peapField = "None"

                p.addMessage(msg_id, {
                    "time": t,
                    "direction": Direction,
                    "countTo": countTo,
                    "countCc": countCc,
                    "countBcc": countBcc,
                    "userField": userField,
                    "peapField": peapField,
                    "messageSubject": messageSubject,
                    "messageBody": messageBody
                    })

            # 3. The peap does exist

            else:
                # If the e-mail is not in th peap, add the email and then the message
                if not nameEmail[0] in p.emails:
                    p.addEmail(nameEmail[0])
                    print "Adding new email address to peap:", p.emails ,p.names, p.name

                if not nameEmail[1] in p.names:
                    p.addName(nameEmail[1])
                    print "Adding new name to peap:", p.emails, p.names, p.name

                # Then add the message

                peapEmail = nameEmail[0]

                peapField = ""
                if peapEmail in vFrom[0]:
                    peapField = "From"
                elif peapEmail in vTo[0]:
                    if not peapField in ["From"]:
                        peapField = "To"
                elif peapEmail in vCc[0]:
                    if not peapField in ["From", "To"]:
                        peapField = "Cc"
                elif peapEmail in vBcc[0]:
                    if not peapField in ["From", "To", "Cc"]:
                        peapField = "Bcc"
                else:
                    peapField = "None"

                p.addMessage(msg_id, {
                    "time": t,
                    "direction": Direction,
                    "countTo": countTo,
                    "countCc": countCc,
                    "countBcc": countBcc,
                    "userField": userField,
                    "peapField": peapField,
                    "messageSubject": messageSubject,
                    "messageBody": messageBody
                    })
                    
    return pl
