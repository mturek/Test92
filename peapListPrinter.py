import pickle

from HTMLParser import HTMLParser
import datetime,calendar

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def handle_entityref(self, name):
        self.fed.append('&%s;' % name)
    def get_data(self):
        return ''.join(self.fed)

def html_to_text(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()



f = open("mtPeapList.dat","r")
pl = pickle.load(f)
f.close()


# Print names, emails, and context
#
# outputFile = open("peapListText.tsv", "w")
# outputFile.write("\t".join(["Primary name", "All names", "Emails", "ScopeScore","Last Contacted","NumberOfEmailsIncluded","ContextLocations","ContextOrganizations","ContextEducation"]) + "\n")
# for peap in pl.list:
# 	row = [peap.name, peap.names, peap.emails, peap.getScopeScore(), peap.getLastContacted(), len(peap.getMessageIDs()), peap.context["locations"], peap.context["organizations"], peap.context["education"]]

# 	outputFile.write("\t".join(map(str, row)) + "\n")

# 	print peap.name, "written"

# outputFile.close()

# Print score parameters
#
outputFile = open("regressionData.tsv", "w")
outputFile.write("\t".join(["Primary name","normalizedNumEmails","receivedEmailRatio","lastContacted","daysSinceLastContact","scopeScore","scopeStatusAutomatic"]) + "\n")

d = datetime.datetime.utcnow()
now = 1.0*calendar.timegm(d.utctimetuple())/(24*60*60.0)

for peap in pl.list:
    daysSinceLastContact = now - peap.getLastContacted()
    row = [peap.name, peap.scopeInfo["normalizedNumEmails"],peap.scopeInfo["receivedEmailRatio"],peap.getLastContacted(),daysSinceLastContact,peap.getScopeScore(),peap.getScopeStatusAutomatic()]

    outputFile.write("\t".join(map(str, row)) + "\n")

    print peap.name, "written"

outputFile.close()



# Print message bodies
#
# outputFile = open("messageBodies.txt", "w")
# for peap in pl.list:
# 	if "Armen Nalband" in peap.names:
# 		for messageID in peap.getMessageIDs():
# 			message = peap.getMessageByID(messageID)

# 			body = message["messageBody"]
# 			textBody = html_to_text(body)

# 			outputFile.write(textBody + "\n")
# outputFile.close()