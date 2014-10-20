import Peaps
import pickle
import string
import re

from gensim import corpora, models, similarities


with open("topicModelData/stop_list.txt") as file:
	common_words = ["re","fw","fwd","eom"]

	for row in file:
		common_words.append(re.sub(r'[^\w\s]','',row.rstrip().lower()))


def analyze_subjects(subject_lines):
	# Raw subject lines
	#print "\n".join(subject_lines)

	# Remove punctuation
	subject_lines_no_punct = [re.sub(r'[^\w\s]','',s) for s in subject_lines]
	# print "\n".join(subject_lines_no_punct)

	# Tokenized on spaces
	subject_lines_no_punct_token = [s.split(" ") for s in subject_lines_no_punct]
	# for line in subject_lines_no_punct_token:
	# 	print str(line)

	# Remove common words
	texts = []
	for line in subject_lines_no_punct_token:
		new_line = []

		for word in line:
			if not word in common_words:
				new_line.append(word)

		texts.append(new_line)

	# for line in subject_lines_no_punct_token:
	# 	print str(line)

	# Filter so that each subject line only appears once
	texts = list(set([tuple(text) for text in texts]))
	texts = [list(text) for text in texts]

	# for line in texts:
	# 	print str(line)

	# Remove words that only appear in a single subject line
	all_tokens = sum(texts,[])
	tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
	texts = [[word for word in text if word not in tokens_once] for text in texts]

	for line in texts:
		print str(line)

	# Try the topic model
	dictionary = corpora.Dictionary(texts)
	dictionary.save("pokus.dict")

	corpus = [dictionary.doc2bow(text) for text in texts]
	corpora.MmCorpus.serialize("pokus.mm", corpus)
	
	#id2word = corpora.Dictionary.load_from_text('pokus.dict')
	id2word = dictionary
	mm = corpora.MmCorpus('pokus.mm')

	#print(mm)

	#lda = models.ldamodel.LdaModel(corpus=mm, id2word=id2word, num_topics=5, update_every=0, passes=20)
	lda = models.ldamodel.LdaModel(corpus=mm, id2word=id2word, num_topics=3)
	#print lda

	topics = lda.print_topics(num_words=2)
	#print "\n".join(topics)
	#lda.print_topics()

	# corpus = subject_lines_no_punct_token

	# tfidf = models.TfidfModel(corpus)












if __name__ == "__main__":
	f = open("mtPeapList.dat")
	pl = pickle.load(f)
	f.close()

	sortedPeaps = sorted(pl.list, key=lambda x:len(x.messageID), reverse=True)


	for peap in sortedPeaps[:10]:
		if peap.name == "Null":
			continue

		print "-"*20
		print "Peap name: " + peap.name
		print "Peap emails: " + str(peap.emails)
		print "Number of emails: " + str(len(peap.messageID))
		
		subject_lines = [peap.table[ID][7].lower() for ID in peap.messageID]
		
		# print "\n".join(subject_lines)

		analyze_subjects(subject_lines)

		print "\n"

	# f = open("mtPeapList.dat", "w")
	# pickle.dump(pl, f)
	# f.close()