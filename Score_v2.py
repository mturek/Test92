import numpy as np
import math

from scipy.optimize import minimize


def sufficient_statistics(sender, time):  # return the sufficient statistics needed for ll calculation of conversation
                                         # Sender is list of sender in 0-1 format
                                         # Time is list of times in real number format
    tol = 1e-24
    X = list(map(lambda x,y:y-x,time[0:-1],time[1:])) #inter-msg times
    S = list(map(lambda s0,s1: s1+2*s0,sender[0:-1],sender[1:]))
    SX = list(map(lambda s,x: (s,x),S,X))
    m1 = [0,0,0,0]
    m2 = [0,0,0,0]
    N = [0,0,0,0]
    for i in list(range(0,4)):
        Xi = list(map(lambda x: math.log(x[1]+tol),filter(lambda xs: xs[0]==i, SX)))
        X2i = list(map(lambda x: math.log(x[1]+tol)**2,filter(lambda xs: xs[0]==i, SX)))
        try: # Xi is sometimes 0, so it cannot be divided by zero (Francisco)
            m1[i] = float(sum( Xi))/float(len(Xi))
            m2[i] = float(sum( X2i))/float(len(Xi))
        except:
            pass
        N[i] = len(Xi)
    return (S,X,SX,m1,m2,N)

def convofit(sender,time):  #fit model parameters to convo data in Sender, Time arrays
    inf = float('inf')
    #parameters = [theta, A, alpha, delta, epsilon, sigma]
    params0 = [0.49314,10,1,1,-6,2]  #initial values
    bnds = ((0.01,0.99),(0,inf), (0.01,10),
            (0,inf),(-inf,inf),(0.01,inf))
    res = minimize(log_likelihood, params0, args = (sender,time),
                   bounds=bnds, method='SLSQP')
    params = res.x
    return params

def log_likelihood_state(params,sender,time):
    #params = [theta,A,alpha,delta,epsilon,sigma]
    tol = 1e-24
    theta = float(params[0])
    alpha = float(params[2])
    if min(theta,alpha)<0:
        ll = -float('inf')
    else:
        (S,X,SX,m1,m2,N)= sufficient_statistics(sender,time)
        
        if theta < 0:
            theta = 0

        if 1 - theta + tol < 0:
            theta = 1   

        puu = alpha*np.log(theta+tol)
        pvv = alpha*np.log(1-theta+tol)
        puv = np.log1p(-np.exp(alpha*np.log(theta+tol)))
        pvu = np.log1p(-np.exp(alpha*np.log(1-theta+tol)))
        try:
            ll = (N[0]*puu+N[1]*puv+
                  N[2]*pvu+N[3]*pvv)
        except:
            print 'll error: theta = %s, alpha = %s'%(theta,alpha)
            ll=0
    return -ll #take negative for minimization

def log_likelihood_time(params,sender,time):
    #params = [theta,A,alpha,delta,epsilon,sigma]
    tol = 1e-24

    theta = float(params[0])
    delta = float(params[3])
    epsilon = float(params[4])
    sigma = float(params[5])
    if min(sigma,theta,delta)<0:
        ll = -float('inf')
    else:
        (S,X,SX,m1,m2,N)= sufficient_statistics(sender,time)
        mu_uv = epsilon+delta/2*(1/2-theta)  #delay of v
        mu_vu = epsilon-delta/2*(1/2-theta)  #delay of u
        ind_uv = 1
        ind_vu = 2
        Nuv = N[ind_uv]
        Nvu = N[ind_vu]
        m1_uv = m1[ind_uv]
        m1_vu = m1[ind_vu]
        m2_uv = m2[ind_uv]
        m2_vu = m2[ind_vu]
        try:
            ll_uv = -Nuv*(math.log(sigma+tol)+
                          1/(2*sigma**2+tol)*(m2_uv-2*mu_uv*m1_uv+mu_uv**2))
        except:
            print 'll_uv error: sigma = %s'%(sigma)
        ll_vu = -Nvu*(math.log(sigma+tol)+
                      1/(2*sigma**2+tol)*(m2_vu-2*mu_vu*m1_vu+mu_vu**2))
        ll= ll_uv + ll_vu
    return -ll #take negative for minimization

def log_likelihood_A(params,sender,time):
    tol = 1e-24
    (S,X,SX,m1,m2,N)= sufficient_statistics(sender,time)
    A = float(params[1])

    if A + tol < 0:
        A = 0

    ll = -A+sum(N)*math.log(A+tol)

    return -ll  #take negative for minimization

def log_likelihood(params,sender,time):
    ll_state = log_likelihood_state(params,sender,time)
    ll_time =log_likelihood_time(params,sender,time)
    ll_A = log_likelihood_A(params,sender,time)
    ll = ll_A+ll_state+ll_time
    return ll

def get_time_sender(peap):
    time = []
    sender = []
    for id in peap.getMessageIDs():

        # Filter down to emails where userField is either To or From
        if not peap.getMessageByID(id)["userField"] in ["To", "From"]:
            # print "Skipping email for model since user is in the (" + pl.list[peapID].table[id][5] + ") field: " + pl.list[peapID].table[id][7] + ""
            continue

        # Filter so that the peap is also in To/From
        if not peap.getMessageByID(id)["peapField"] in ["To", "From"]:
            continue    

        # Filter down to emails where the peap is on the opposite side of the email
        # (if user in "To", require peap in "From" and vice versa, eliminate emails where both user and peap in To)
        if peap.getMessageByID(id)["userField"] == peap.getMessageByID(id)["peapField"]:
            #print "Skipping email since user and peap are both in " + peap.getMessageByID(id)["userField"]
            continue

        time.append(peap.getMessageByID(id)["time"])
        if peap.getMessageByID(id)["direction"] == 1:
            sender.append(1)
        else:
            sender.append(0)

    return time, sender 

# Return the ratio of emails received from peap to total number
# Only consider emails where user and peap appear in the To/From fields
def get_received_email_ratio(peap):
    totalEmails = 0
    receivedEmails = 0

    for messageID in peap.getMessageIDs():
        message = peap.getMessageByID(messageID)

        if message["userField"] == "To" and message["peapField"] == "From":
            receivedEmails += 1
            totalEmails += 1
        elif message["userField"] == "From" and message["peapField"] == "To":
            totalEmails += 1

    if totalEmails > 0:
        return 1.0 * receivedEmails / totalEmails
    else:
        return 1



def get_weighted_num_emails(peap):
    weighted_num_emails = 0

    # Define weighting coefficients
    # Coefficients[SENDING/RECEIVING][TARGET's_EMAIL_FIELD][COUNT_CATEGORY]
    coefficients = {"RECEIVING":{}, "SENDING":{}}
    coefficients["RECEIVING"]["To"] = [1, 0.6, 0.5, 0.15]
    coefficients["RECEIVING"]["Cc"] = [0.75, 0.6, 0.3, 0.15]
    coefficients["RECEIVING"]["Bcc"] = [0.5, 0.5, 0.5, 0.5]

    coefficients["SENDING"]["To"] = [1, 0.6, 0.5, 0.15]
    coefficients["SENDING"]["Cc"] = [0.75, 0.6, 0.3, 0.15]
    coefficients["SENDING"]["Bcc"] = [1, 0.8, 0.7, 0.4]

    for id in peap.getMessageIDs():
        #(time, direction,countTO,countCC,countBCC, userField, peapField, messageSubject) = pl.list[peapID].table[id]
        
        message = peap.getMessageByID(id)

        time = message["time"]
        direction = message["direction"]
        countTO = message["countTo"]
        countCC = message["countCc"]
        countBCC = message["countBcc"]
        userField = message["userField"]
        peapField = message["peapField"]

        # Assuming that there is always only 1 sender
        countTotal = 1 + countTO + countCC + countBCC

        # Find the category of email by number of people involved
        if 0 <= countTotal <= 2:
            countCategory = 0
        elif 3 <= countTotal <= 7:
            countCategory = 1
        elif 8 <= countTotal <= 15:
            countCategory = 2
        elif 16 <= countTotal:
            countCategory = 3

        # Normalize direction to indices 
        if direction == -1:
            directionName = "RECEIVING"
            targetEmailField = userField
        else:
            directionName = "SENDING"
            targetEmailField = peapField

        # Increment the number of emails by the weighting coefficient
        if targetEmailField == 'None':
            print "targetEmailField is None for message ", id
            print message
        else: 
            weighted_num_emails += coefficients[directionName][targetEmailField][countCategory]

        #print str(pl.list[peapID].name) + " : " + str(coefficients[directionName][targetEmailField][countCategory]) + " for: " + messageSubject

    return weighted_num_emails
        