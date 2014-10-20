import facebook
import Peaps

import pickle

def get_paged_connections(graph, node_name, connection_name, pagination_type):
	response = []

	if pagination_type == "offset":
		PAGING_STEP = 25
		index = 0

		segment = graph.get_connections(node_name,connection_name,limit=PAGING_STEP,offset=0)

		while len(segment["data"]) > 0:
			response.extend(segment["data"])

			index += 1
			segment = graph.get_connections(node_name,connection_name,limit=PAGING_STEP,offset=index * PAGING_STEP)

	elif pagination_type == "cursor":
		segment = graph.get_connections(node_name, connection_name, limit=25)
		response.extend(segment["data"])

		while "next" in segment["paging"].keys():
			cursor = segment["paging"]["cursors"]["after"]
			segment = graph.get_connections(node_name, connection_name, limit=25, after=cursor)
			response.extend(segment["data"])

	return response

def load_facebook_data(pl, access_token):
	graph = facebook.GraphAPI(ACCESS_TOKEN)

	user_profile = graph.get_object("me")
	user_likes = get_paged_connections(graph, "me", "likes", "cursor")
	user_like_ids = [like["id"] for like in user_likes]


	# Load a list of all user's friends that use the app
	# friends: [{'name': 'Michael Turek', 'id':'123456'},{...}]
	friends = get_paged_connections(graph, "me", "friends", "offset")

	# For each friend, try to locate the corresponding peap
	for friend in friends:
		friend_info = graph.get_object(friend["id"])

		if "email" in friend_info.keys():
			# TODO: This is not very common but if available, could be used instead of name
			pass

		elif not "email" in friend_info.keys():
			friend_name = friend_info["name"].replace(" ","")

			peap = pl.getPeapByName(friend_name, fuzzy=True)

			# If peap found, check the likes the peap shares with user and save to Peap.context["common_likes"] 
			if peap != -1:
				print "Success, filling in Facebook data for ", peap.name

				friend_likes = get_paged_connections(graph, friend_info["id"], "likes", "cursor")

				friend_like_ids = [like["id"] for like in friend_likes]
				common_like_ids = set(user_like_ids) & set(friend_like_ids)
				
				common_likes = set([(like["id"], like["name"]) for like in friend_likes if like["id"] in common_like_ids])
				
				# Update the Peap entry in the PeapList with the new context
				if not "common_likes" in peap.context.keys():
					peap.context["common_likes"] = []

				peap.context["common_likes"].extend(common_likes)

			else:
				#print "Cannot locate user in PeapList ", friend_name
				pass
			
if __name__ == "__main__":
	f = open("mtPeapList.dat")
	pl = pickle.load(f)
	f.close()

	ACCESS_TOKEN = "<enter current access token>"

	load_facebook_data(pl, ACCESS_TOKEN)

	f = open("mtPeapList.dat", "w")
	pickle.dump(pl, f)
	f.close()