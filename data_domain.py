import Peaps
import csv

import pythonwhois

import pickle

def load_domain_data(pl):
	# Load domain database into memory
	domain_data = {}
	domain_files = ["general_tlds","country_tlds","geo_specific_tlds","topic_tlds","us_colleges","free_domains"]
	
	for domain_file in domain_files:
		with open("domain_data/" + domain_file + ".csv") as csvfile:
			csvreader = csv.reader(csvfile, delimiter=",")

			domain_data[domain_file] = []

			for row in csvreader:
				domain_data[domain_file].append(row)

	# Go through peaps one by one
	for peap in pl.list:
		for email in peap.emails:
			
			found = False

			# Scan for countries
			for row in domain_data["country_tlds"]:
				if email.endswith(row[0]):
					found = True

					if row[1] not in [location["country"] for location in peap.context["locations"] if "country" in location.keys()]:
						peap.context["locations"].append({"country":row[1], "source":email})
						
						print "Country match: " + row[1] + " for " + email

					break

			# Scan for geo-specific tld's
			for row in domain_data["geo_specific_tlds"]:
				if email.endswith(row[0]):
					found = True

					if row[1] not in [location["city"] for location in peap.context["locations"] if "city" in location.keys()]:
						peap.context["locations"].append({"city": row[1], "country":row[2], "source":email})
						
						print "City match: " + row[1] + ", " + row[2] + " for " + email

					break

			# Scan for US colleges:
			for row in domain_data["us_colleges"]:
				if email.endswith("." + row[0]) or email.endswith("@" + row[0]):
					found = True

					if row[1] not in [education_item["school"] for education_item in peap.context["education"] if "school" in education_item.keys()]:
						peap.context["education"].append({"name": row[1], "state":row[2], "country": "USA", "source":email})
						peap.context["locations"].append({"state": row[2], "country": "USA", "source": email})
							
						print "School match: " + row[1] + " in " + row[2] + " for " + email

					break

			# Scan for generic free-emails:
			for row in domain_data["free_domains"]:
				if email.endswith("." + row[0]) or email.endswith("@" + row[0]):
					found = True
					print "Generic free domain: " + email

					break

			"""
			TODO: Which fields should we use WHOIS registrant data for?
			"""

			# If not in local database, try WHOIS
			if not found:
				if email != None and "@" in email:
					full_domain = email[email.index("@") + 1:]
				else:
					full_domain = ""
					print "Invalid email: " + email

				# Try loading data from the online database
				try:
					whois = pythonwhois.get_whois(full_domain)

					registrant = whois["contacts"]["registrant"]

					if registrant != None:
						organization_entry = {}
						location_entry = {}

						# Check which fields are filled in on WHOIS

						# Do not use city/state since companies might have multiple branches
						# if "city" in registrant.keys():
						# 	location_entry["city"] = registrant["city"]

						# if "state" in registrant.keys():
						# 	location_entry["state"] = registrant["state"]

						if "country" in registrant.keys():
							location_entry["country"] = registrant["country"]

						if "organization" in registrant.keys():
							organization_entry = location_entry.copy()
							organization_entry["name"] = registrant["organization"]

						# Include in peap.context if any field contained information
						if len(location_entry.keys()) > 0:
							location_entry["source"] = email
							peap.context["locations"].append(location_entry)

							print "WHOIS location match for ("+email+"): " + str(location_entry)
							found = True

						if len(organization_entry.keys()) > 0:
							organization_entry["source"] = email
							peap.context["organizations"].append(organization_entry)

							print "WHOIS organization match for ("+email+"): " + str(organization_entry)
							found = True
							
				except:
					print "Couldn't retrieve WHOIS data for " + email


			# If neither in local nor WHOIS, log the email
			if not found:
				print "No match for email: " + email



if __name__ == "__main__":
	f = open("mtPeapList.dat")
	pl = pickle.load(f)
	f.close()

	load_domain_data(pl)

	f = open("mtPeapList.dat", "w")
	pickle.dump(pl, f)
	f.close()