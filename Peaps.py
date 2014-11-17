"""
    The Peap class

"""

from parse_rest.datatypes import Object
import difflib
import Score_v2
import datetime
import calendar
import math
import numpy as np

from ServerFlag import SERVER


class parsePeap2(Object):
    pass

class UserEntry(Object):
    pass

class PeapList():

    # The constructor function

    PeapID=0

    def __init__(self,name):
        self.name = name
        self.list = []
        # FH: It would be useful to have several variables here:
        # Lists:
        #   - listInScope: all peaps (list of peaps in scope, ordered by priority)
        #   - listPriority (list of peaps in scope, ordered by priority)
        # Other global variables?
        #   - numberOfPeapsInScope: this number should include the 150 + manualEntries
        #   - dateLastQuery, etc

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

    def getPeapByName(self, name, fuzzy=False, min_similarity=0.9):
        # Always do a first pass without fuzzy match:
        for peap in self.list:
            for peapName in peap.names:
                if peapName == name:
                    return peap

        # If fuzzy match allowed, do a 2nd fuzzy pass as well:
        if fuzzy == True:
            for peap in self.list:
                for peapName in peap.names:
                    stringSimilarity = difflib.SequenceMatcher(None, name, peapName).ratio()

                    if stringSimilarity >= min_similarity:
                        return peap

        return -1


    # def getPeapByName(self, name, fuzzy=False, min_similarity=0.9):
    #     for peap in self.list:
    #         for peapName in peap.names:
    #             stringSimilarity = difflib.SequenceMatcher(None, name, peapName).ratio()

    #             if (fuzzy == False and peap.name==name) or (fuzzy == True and stringSimilarity >= min_similarity):
    #                 return peap

    #     return -1

    def getPeapByEmail(self, email):
        for peap in self.list:
            if email in peap.emails:
                return peap

        return -1

    # Removes all peaps to whom the user never sent a personal email
    def eliminatePeapsWithoutRelationship(self):
        print "Starting elimination with " + str(len(self.list)) + " peaps"

        eliminateIDs = []
        
        for peap in self.list:
            eliminate = True

            for messageID in peap.getMessageIDs():
                if peap.getMessageByID(messageID)["userField"] == "From":
                    eliminate = False

            if eliminate:
                eliminateIDs.append(peap.getID())

        for eliminateID in eliminateIDs:
            #print "Eliminating: " + self.getPeapByID(eliminateID).getName()
            self.removePeap(eliminateID)


        print "Ending elimination with " + str(len(self.list)) + " peaps"

    # Tries to identify the most desirable primary name for each Peap
    def chooseBestNames(self):
        for peap in self.list:
            potentialNames = set([name for name in peap.names if not '@' in name])

            deprioritizedNames = set([name for name in potentialNames if name.lower() == name.upper()])

            if len(potentialNames) > len(deprioritizedNames):
                potentialNames = potentialNames - deprioritizedNames

            # If any potential names left, pick a random one for the time being
            if len(potentialNames) > 0:
                newName = potentialNames.pop()

                #print "Renaming peap from (" + peap.name + ") to (" + newName + ")"
                peap.setPrimaryName(newName)

    def calculateNumEmails(self):
        sumOfWeightedNum = 0

        for peap in self.list:
            weightedNum = Score_v2.get_weighted_num_emails(peap)
            peap.scopeInfo["normNumEmails"] = weightedNum

            sumOfWeightedNum += weightedNum

        for peap in self.list:
            peap.scopeInfo["normNumEmails"] = peap.scopeInfo["normNumEmails"] / sumOfWeightedNum
 
    def calculateThetas(self):
        for peap in self.list:
            theta = Score_v2.get_simplified_theta_estimate(peap)

            peap.scopeInfo["theta"] = theta

    def calculateScopeScores(self):
        # Assign final score:
        for peap in self.list:
            #score = <some combination of normNumEmails and the ratio>
            score = peap.scopeInfo["normNumEmails"]
            
            peap.setScopeScore(score)


    def calculateDurations(self, NUM_DAYS):
        for peap in self.list:
            times,sender = Score_v2.get_time_sender(peap)

            if len(times) > 0:
                firstContacted = min(times)
                lastContacted = max(times)

                duration = lastContacted - firstContacted

                # normDuration is the duration as a percentage of the total timeframe scanned
                normDuration = 1.0 * duration / (NUM_DAYS * 24 * 60 * 60)

                # print "normDuration for", peap.name, "is", normDuration
                
            else:
                normDuration = 0

            peap.scopeInfo["normDuration"] = normDuration


    def calculateDomainStats(self, root):
        if SERVER == False:
            free_domains = [row.strip() for row in open("domain_data/free_domains.csv")]
        elif SERVER == True:
            free_domains = [row.strip() for row in open("/root/nodejsPeaps/domain_data/free_domains.csv")]

        # print free_domains
        # with open("domain_data/free_domains.csv") as csvfile:
        #     csvreader = csv.reader(csvfile, delimiter=',')

        #     free_domains = list(csvreader)


        # userDomains = []
        # for email in root:
        #     if '@' in email:
        #         full_domain = email[email.index("@") + 1:]

        #         if not full_domain in free_domains:
        #             userDomains.append(full_domain)

        # print "Starting with root:", root

        userDomains = [email[email.index("@")+1:] for email in root if "@" in email]
        userDomains = [domain for domain in userDomains if domain not in free_domains]

        # print "Using root:", userDomains

        for peap in self.list:
            peapDomains = [email[email.index("@")+1:] for email in peap.emails if "@" in email]

            # print "Peap domains for", peap.name, "are", peapDomains

            numShared = len(set(userDomains) & set(peapDomains))
            # print "Shared domains:", (set(userDomains) & set(peapDomains))

            peap.scopeInfo["numSharedDomains"] = numShared

            peap.scopeInfo["numAddresses"] = len(peap.emails)

    def sortPeapsByScopeScore(self, numInScope):
        self.list.sort(key=lambda x: x.scopeInfo["scopeScore"], reverse=True)

        for i in range(min(numInScope, len(self.list))):
            self.list[i].scopeInfo["scopeStatusAutomatic"] = 1

    def calculatePriorityScores(self, numInScope):

        listScope = []

        self.list.sort(key=lambda x: x.scopeInfo["scopeScore"], reverse=True)  # organizes peaps by scopeScore
        for i in range(len(self.list)):
            if (self.list[i].scopeInfo["scopeStatusManual"] == 1) | (self.list[i].scopeInfo["scopeStatusAutomatic"] == 1):
                listScope.append(self.list[i])

        n = len(listScope)

        listScope.sort(key=lambda x: x.scopeInfo["lastContacted"], reverse=False) # organizes peaps by lastContacted
        for i in range(len(listScope)):
            listScope[i].scopeInfo["lastContactedPercentage"] = (n*1.0-i)/n*100.0
            #print listScope[i].name, " ", listScope[i].scopeInfo["lastContactedPercentage"]


        listScope.sort(key=lambda x: x.scopeInfo["scopeScore"], reverse=True)  # organizes peaps by scopeScore
        for i in range(len(listScope)):
            listScope[i].scopeInfo["scopePercentage"] = (n*1.0-i)/n*100.0
            #print listScope[i].name, " ", listScope[i].scopeInfo["scopePercentage"]

        for i in range(len(listScope)):
            listScope[i].scopeInfo["priorityScore"] = 0.4 * listScope[i].scopeInfo["scopePercentage"] + 0.6 * listScope[i].scopeInfo["lastContactedPercentage"]
            #print listScope[i].name, " ", listScope[i].scopeInfo["priorityScore"]

    def calculateEntropies(self, numDaysTotal, numDaysPeriod):
        d = datetime.datetime.utcnow()
        now = int(1.0*calendar.timegm(d.utctimetuple()))
        beginning = now - numDaysTotal * 24 * 60 * 60

        interval = numDaysPeriod * 24 * 60 * 60
        binRanges = range(beginning, now, interval)

        # Method definition for helper method
        def calculateEntropy(dist):
            total = sum(dist)

            H = 0
            for period in dist:
                if period == 0:
                    continue
                else:
                    H += -1.0 * period / total * math.log(1.0 * period / total)

            return H
        # End of method definition

        maxEntropy = calculateEntropy([1] * (len(binRanges) - 1))

        for peap in self.list:
            times,sender = Score_v2.get_time_sender(peap)

            hist,bin_edges = np.histogram(times, bins=binRanges)

            normEntropy = 1.0 * calculateEntropy(hist) / maxEntropy

            peap.scopeInfo["normEntropy"] = normEntropy

            # print "Name:",peap.name,"normEntropy:",normEntropy


    def uploadPeapsToParse(self):
        # Check if user already had his mailbox processed:
        userEntries = UserEntry.Query.filter(uemail = self.name)
        print userEntries

        if len(userEntries) != 1:
            print "Database error, number of user entries associated with email:", len(userEntries)
            return

        else:
            print "Saving peaps for user on Parse"
            userEntry = userEntries[0]

            # numInScope = 0
            
            # Assume self.list is ordered by scopeScore (ran sortPeapsByScore recently)
            #for index in range(min(300, len(self.list))):
            for peap in self.list:
                #peap = self.list[index]
                # scopeStatusManual = peap.getScopeStatusManual()
                # scopeStatusAutomatic = peap.getScopeStatusAutomatic()

                # if scopeStatusManual == 1 or (scopeStatusManual == 0 and scopeStatusAutomatic == 1):
                #     numInScope += 1    

                peap.savePeap()

            userEntry.mailboxProcessed = True

            d = datetime.datetime.utcnow()
            now = calendar.timegm(d.utctimetuple())
            userEntry.lastMailboxUpdate = now

            # userEntry.numPeapsInScope = numInScope

            userEntry.save()


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

        self.scopeInfo = {
            "normNumEmails":0,
            "receivedEmailRatio":1,
            "lastContacted": -1,
            "scopeScore": -1,
            "priorityScore": -1,
            "scopeStatusAutomatic": -1,
            "scopeStatusManual": 0,
            "scopePercentage": 0,  # created by FH
            "lastContactedPercentage": 0 # created by FH
        }

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

    def setScopeStatusManual(self,status):  # edited by FH
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

    def getScopeStatusManual(self):
        return self.scopeInfo["scopeStatusManual"]

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
        pPeap = parsePeap2(uemail = self.userName, name = self.name , names=self.names, ID = self.ID , emails = self.emails , 
            scopeScore = self.scopeInfo["scopeScore"], priorityScore = self.scopeInfo["priorityScore"], 
            scopeStatusAutomatic = self.scopeInfo["scopeStatusAutomatic"], scopeStatusManual = self.scopeInfo["scopeStatusManual"],
            normalizedNumEmails = self.scopeInfo["normNumEmails"], receivedEmailRatio = self.scopeInfo["receivedEmailRatio"],
            lastContacted = self.scopeInfo["lastContacted"], context = self.context)
        
        # Rename normalizedNumEmails to normNumEmails when switching to parsePeap3

        """ DON'T SAVE ON PARSE FOR THE TIME BEING """
        pPeap.save()
        """ REMOVE WHEN DONE DEBUGGING """

        #print "Object ID", pPeap.objectId