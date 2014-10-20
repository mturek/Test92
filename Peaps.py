"""
    The Peap class

"""

from parse_rest.datatypes import Object
import difflib

class parsePeap(Object):
    pass

class PeapList():

    # The constructor function

    PeapID=0

    def __init__(self,name):
        self.name = name
        self.list = []

    # Creates a new Peap object and adds it to the PeapList
    def addPeap(self,name,email):
        self.PeapID += 1
        peap = Peap(self.name,name,email,self.PeapID)
        self.list.append(peap)
        return peap

    # Removes a peap with a given ID from the PeapList
    def removePeap(self, id):
        for peap in self.list:
            if peap.ID == id:
                self.list.remove(peap)
                break

    # Returns a peap with a given ID from the PeapList
    def getPeapByID(self, id):
        for peap in self.list:
            if peap.ID == id:
                return peap

    """ MT EDIT """
    def getPeapByName(self, name, fuzzy=False, min_similarity=0.9):
        for peap in self.list:
            for peapName in peap.names:
                stringSimilarity = difflib.SequenceMatcher(None, name, peapName).ratio()

                if (fuzzy == False and peap.name==name) or (fuzzy == True and stringSimilarity >= min_similarity):
                    return peap

        return -1

    def getPeapByEmail(self, email):
        for peap in self.list:
            if email in peap.emails:
                return peap

        return -1
    """ END MT EDIT"""

   

class Peap():


    # The constructor function

    def __init__(self,uname,name,email,ID):

        self.userName = uname # name of the Peap owner, required for parse purposes
        self.name = name    # The name of the Peap

        self.objectId = ID
        self.ID = str(ID)       # The ID associated with the peap, assigned by the peapList class
        self.emails = [email]   # The list of e-mails associated with the peap
        self.names = [name]     # List of names associated with the peap

        self.messageID = [] # chronologically sorted list of message IDs
        self.table = {}     # Table containing the gathered data

        """DEPRECATED"
        self.lastContacted = -1
        self.scopeScore = -1  #
        self.priorityScore = -1
        self.scopeStatusAutomatic = -1  # 1: in scope, -1: out of scope. By default they are all -1
        self.scopeStatusManual = 0  # 0: not chosen, 1: in scope, -1: not in scope
        "END DEPRECATED"""

        self.scopeInfo = {
            "lastContacted": -1,
            "scopeScore": -1,
            "priorityScore": -1,
            "scopeStatusAutomatic": -1,
            "scopeStatusManual": 0 
        }

        """ MT EDIT """

        self.context = {
            "education":[],
            "jobs":[],
            "organizations":[],
            "locations":[],
            "common_likes":[]
        }

        # Example entries:
        # Only include an entry if parameter known
        # When using, check for parameter. E.g.
        # if "city" in self.context["education"][0].keys():
        #   bring up article about the city

        """
        "education":[{
            "name":"MIT",
            "city":"Cambridge",
            "state":"MA",
            "country":"USA",
            "timeframe":(2011,2015)
        }],
        "locations":[{
            "city":"Cambridge",
            "state":"MA",
            "country":"USA",
            "timeframe":(2011,2015),
            "source":"mturek@mit.edu"
        }]
        """

        """ END MT EDIT """

    # Identifiers    
    def addEmail(self,email):
        self.emails.append(email)

    def addName(self,name):
        self.names.append(name)

    def getName(self):
        return self.name

    def getNames(self):
        return self.names

    def getEmails(self):
        return self.emails

    def setPrimaryName(self, name):
        self.name = name

    def getID(self):
        return self.ID

    # Other info
    def getContextEntries(self,category):
        if category in self.context.keys():
            return self.context[category]
        else:
            return []

    def addContextEntry(self, category, entry):
        if category in self.context.keys():
            self.context[category].append(entry)
        else:
            self.context[category] = [entry]


    # Scope info
    def setScopeScore(self,sco):  # edited by FH
        self.scopeInfo["scopeScore"] = sco

    def addScopeStatusManual(self,status):  # edited by FH
        self.scopeInfo["scopeStatusManual"] = status

    def setScopeStatusAutomatic(self,status):  # edited by FH
        self.scopeInfo["scopeStatusAutomatic"] = status

    def setPriorityScore(self,prio):  # edited by FH
        self.scopeInfo["priorityScore"] = prio

    def getLastContacted(self):
        return self.scopeInfo["lastContacted"]

    def getScopeScore(self):
        return self.scopeInfo["scopeScore"]

    def getPriorityScore(self):
        return self.scopeInfo["priorityScore"]

    def getScopeStatusAutomatic(self):
        return self.scopeInfo["scopeStatusAutomatic"]

    def getMessageIDs(self):
        return self.messageID

    def getMessageByID(self, ID):
        if ID in self.messageID:
            return self.table[ID]
        else:
            return {}


    # Add a new message to list of existing messages
    def addMessage(self, ID, message):

        # 1. Add the message information to the table

        #self.table[ID] = [time, direction,countTO,countCC,countBCC, userField, peapField, messageSubject]
        # self.table[ID] = {
        #     "time": time,
        #     "direction": direction,
        #     "countTo": countTO,
        #     "countCc": countCC,
        #     "countBcc": countBCC,
        #     "userField": userField,
        #     "peapField": peapField,
        #     "messageSubject": messageSubject
        # }

        self.table[ID] = message

        """ END EDIT """
        # 2. Now add the message ID at the right chronological position in the messageID list

        i = 0

        for id in reversed(self.messageID):

            if self.table[id]["time"] <= message["time"]:
                self.messageID.insert(len(self.messageID)-i,ID)
                break

            if i == len(self.messageID) - 1:
                self.messageID.insert(0,ID)
                break
            i+=1

        if len(self.messageID)==0:
            self.messageID.append(ID)

        self.scopeInfo["lastContacted"] = self.table[self.messageID[len(self.messageID)-1]]["time"]/(24*60*60)  # edited by FH

    # Save the relevant information in Parse

    def savePeap(self):
        pPeap = parsePeap(uemail = self.userName, name = self.name , names=self.names, ID = self.ID , emails = self.emails , 
            scopeInfo = self.scopeInfo, context = self.context)
        
        """ DON'T SAVE ON PARSE FOR THE TIME BEING """
        # pPeap.save()
        """ REMOVE WHEN DONE DEBUGGING """