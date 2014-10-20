"""
File contains function that performs the deals with merging the emails belonging to one user.

"""

import re

def mergePeaps(pl, peap1, peap2):
    if peap1.getID() == peap2.getID():
        print "Attempt failed, cannot merge a peap with itself"
        return peap1

    mergedPeap = pl.addPeap(peap1.getNames()[0], peap1.getEmails()[0])

    for name in peap1.getNames() + peap2.getNames():
        if not name in mergedPeap.getNames():
            mergedPeap.addName(name)

    for email in peap1.getEmails() + peap2.getEmails():
        if not email in mergedPeap.getEmails():
            mergedPeap.addEmail(email)

    for category in ["education", "jobs", "organizations", "locations", "common_likes"]:
        for peap in [peap1,peap2]:
            for entry in peap.getContextEntries(category):
                if not entry in mergedPeap.getContextEntries(category):
                    mergedPeap.addContextEntry(category, entry)

    for peap in [peap1,peap2]:
        for ID in peap.getMessageIDs():
            mergedPeap.addMessage(ID, peap.getMessageByID(ID))

    # Add the ability to calculate a score for the new peap


    print "Sucessfully merged peaps " + peap1.getName() + ", " + str(peap1.getEmails()) + " and " + peap2.getName() + ", " + str(peap2.getEmails())

    pl.removePeap(peap1.getID())
    pl.removePeap(peap2.getID())

    return mergedPeap




def combineUsers(userList, data):
# Combine the relationship matrices of merged E-mail addresses

	"""
	ARGS : userList - A dict with 
	        keys : userNames and values : emails under that user

	        data - A dict with 
	          keys : emails and values : a list of relationship arrays

	RETURNS : A dict with 
	            keys : userNames and values : merged list of relationship arrays for various email(s) that correspond to it
	"""

	combinedList = {}

	for usr in userList.keys():
	    for email in userList[usr]:
	      if combinedList.has_key(usr):
	        combinedList[usr] += data[email]
	      elif data.has_key(email):
	        combinedList[usr] = data[email]

	return combinedList


def getEmail(user): #this function extracts the email address from a contact line
    if '<' in user:
        emailPattern = '[<].*@.*[>]'
    else:
        emailPattern = '.*@.*'
    if '@' in user:
        match = re.search(emailPattern,user)
        return match.group().replace('<','').replace('>','').strip().lower()
    else:
        return 'Null'


def get_name_and_email(entry):
    '''entry is a string
    return a list of two strings --
    first string is email address, second string is list of words in name'''


    ''' something like 'qp@mit.edu' gives ['qp@mit.edu', '']
        something like '<kibuanita@gmail.com>' gives ['kibuanita@gmail.com', []]
        something like 'Laura Diamond <diamond.laura@gmail.com>' gives ['diamond.laura@gmail.com', 'Laura Diamond']'''

    #"Scullin, Chris" <CScullin@baincapital.com>
    #['cscullin@baincapital.com', 'Chris""Scullin']
    
    if "<" not in entry and ">" not in entry:
        email = getEmail(entry)
        nameInfo = [email, '']
    
    elif "<" in entry and ">" in entry:
        splitList = entry.split("<",1)

        #print splitList
        Name = str(splitList[0])


        # first get rid of any surrounding "
        # '"Scullin, Chris" ' --> 'Scullin, Chris'
        if len(Name) > 3 and Name[0] == '"' and Name[-2:] == '" ':
            Name = Name[1:-2]

        # and get rid of doubles
        # Name "'chalana.niharika@gmail.com'"

        if len(Name) > 3 and Name[0:2]=='"\'' and Name[-2:] =='\'"':
            Name = Name[2:-2]


        # remove things in parentheses
        # '"Joe Hill (Google+)" <replyto-68688f08@plus.google.com>'
        # We want to treat the same as if it had been "Joe Hill" without the (Google+)
        if "(" in Name and ")" in Name:
            paren = Name[ Name.index("(") : Name.index(")")+1 ]
            Name = Name.replace(paren, "")
            
        # 'Scullin, Chris' -> [' Chris', 'Scullin']
        if ";" in Name:

            nameList = Name.split(";")
            nameList.reverse()

        else:
            nameList = Name.split()



        nameListNoSpaces = []
        for i in range(len(nameList)):
            nameListNoSpaces.append(nameList[i].replace(' ', ''))



        nameNoSpaces = ''
        for word in nameListNoSpaces:
            nameNoSpaces += word

        nameWithSpaces = " ".join(nameListNoSpaces)

        # get rid of quotes:
        nameWithSpaces = nameWithSpaces.replace('"', '')

        # get rid of quotes
        # nameList ['Gabriel"'] -> nameNoSpaces Gabriel
        # nameList ['"mba15@sloan.mit.edu"'] -> nameNoSpaces mba15@sloan.mit.edu

        # if len(nameNoSpaces)>2 and nameNoSpaces[0]=='"' and nameNoSpaces[-1]=='"':
        #     nameNoSpaces=nameNoSpaces[1:-1]
        # elif len(nameNoSpaces)>1 and nameNoSpaces[0]!='"' and nameNoSpaces[-1]=='"':
        #     nameNoSpaces=nameNoSpaces[0:-1]

        
        # nameInfo in form [email, full name]
        #nameInfo = [getEmail(splitList[1]),nameNoSpaces]
        nameInfo = [getEmail(splitList[1]),nameWithSpaces]

    # print nameInfo

    # if nameInfo[0] == "Null":
    #     print entry

    return nameInfo

