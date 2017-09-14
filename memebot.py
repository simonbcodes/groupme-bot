# groupid = 32143427
# token = z0aE2sRQd3b3QjSIpEeccWoFlBJHTPS46ubwRIvG
# botid = 2e8f6f67c5121cef0ad3fbe4a1

import requests
import numpy as np
import matplotlib.pyplot as plt
import json
from datetime import datetime
import pandas as pd
from collections import namedtuple
import re

groupID = "32143427"
token = "z0aE2sRQd3b3QjSIpEeccWoFlBJHTPS46ubwRIvG"

groupmeAPI = "https://api.groupme.com/v3/groups/" + groupID+ "/messages?token=" + token + "&limit=100"
group_data = "https://api.groupme.com/v3/groups/" + groupID + "?token=" + token
created_at = requests.get(group_data).json()['response']['created_at']
beforeID = 0
ids_and_names = {}
allMessages = []
members = {}

class Post(object):
	def __init__(self, post=None, attr=None):
		if attr is None:
			self.name = post['name']
			self.user_id = post['user_id']
			self.post_id = post['id']
			self.likes = len(post['favorited_by'])
			self.likers = post['favorited_by']
			self.text = post['text']
			self.created_at = post['created_at']

			if len(post['attachments']) > 0:
				self.type = 'meme'
				self.attachments = post['attachments']
			else:
				self.type = 'message'

			for user_id in self.likers:
				if user_id in ids_and_names:
					members[ids_and_names[user_id]].has_liked.append(self)
		else:
			self.__dict__ = attr

	def toJSON(self):
		return json.dumps(self.__dict__)

class User(object):
	def __init__(self, data={"nickname":"", "user_id":""}):
		self.name = data['nickname']
		self.user_id = data['user_id']
		self.date_joined = created_at

		ids_and_names[self.user_id] = self.name

		self.posts = []
		self.memes = []
		self.messages = []

		self.likes = 0
		self.meme_likes = 0
		self.message_likes = 0

		self.has_liked = []
	def add_post(self, post):
		self.posts.append(post)
		self.likes += post.likes

		if post.type == "meme":
			self.memes.append(post)
			self.meme_likes += post.likes
		else:
			self.messages.append(post)
			self.message_likes += post.likes

	def toJSON(self):
		return json.dumps(self.__dict__)


def add_users(api):
	group_members = requests.get(api).json()['response']['members']
	for member in group_members:
		members[member['nickname']] = User(member)
	# for user_id, name in ids_and_names.items():
	# 	print (name + ": " + user_id)

def parse_messages_network(api):
	r = requests.get(api);
	try:
		posts = r.json()['response']['messages'] # 100 messages returned from api
		for p in posts:
			post = Post(p)
			allMessages.append(post) # add message to total messages list
			if post.name in members:
				members[post.name].add_post(post)

			if p['system'] and p['event']['type'] == 'membership.announce.added':
				added_users = p['event']['data']['added_users']
				for user in added_users:
					if not user['nickname'] in members:
						members[user['nickname']] = User({'nickname': user['nickname'], 'user_id': str(user['id'])})
					members[user['nickname']].date_joined = p['created_at']

		beforeID = allMessages[-1].post_id # set beforeID to id of last added message, so next GET returns 100 previous posts
		currentAPI = groupmeAPI + "&before_id=" + beforeID # construct new api call
		parse_messages_network(currentAPI) # parse again
	except ValueError:
		pass # if no more messages, return

def parse_messages_sheet():
	df = pd.read_excel(open('users.xlsx', 'rb'), sheetname='sheet1')
	# df1 = df.set_index('Names')
	for key, value in df.iterrows():
		members[value.names] = User()
		members[value.names].name = value.names
		members[value.names].user_id = value.user_ids
		members[value.names].date_joined = value.joined
		members[value.names].likes = value.likes
		members[value.names].meme_likes = value.meme_likes
		members[value.names].message_likes = value.message_likes

		post_parse = []
		# for post in value.posts[2:-2].split("',"):
		# 	try:
		# 		print(json.loads(post.replace(" '", ""))
		# 	except Exception:
		# 		print("fuck")
		# 		pass
			#post_parse.append(json.loads(post))

		# print(value.posts[2:-2])

		members[value.names].posts = post_parse
		members[value.names].memes = value.memes
		members[value.names].messages = value.messages
		members[value.names].has_liked = []

	for member in members:
		members[member].posts = json.loads(members[member].memes[2:-2].split("',"))

		#print(json.loads(members['Kayla Lewis'].memes[2:-2].split("\',")[0])['created_at'])

def likes_over_time(user, type=""):
	chrono = [0]

	if type == "meme":
		posts_of_type = members[user].memes
	elif type == "message":
		posts_of_type = members[user].messages
	else:
		posts_of_type = members[user].posts

	for post in posts_of_type:
		chrono.append(chrono[-1] + post.likes)

	return chrono

def average_likes(name, type="post"):
	user = members[name]

	if type == "meme":
		num_type = len(user.memes)
		average = user.meme_likes / num_type if num_type > 0 else 0
	elif type == "message":
		num_type = len(user.messages)
		average = user.message_likes / num_type if num_type > 0 else 0
	else:
		type = "post"
		num_type = len(user.posts)
		average = user.likes / num_type if num_type > 0 else 0

	return average

def liker_histogram():
	users = sorted(members.values(), key=lambda user:len(user.has_liked))
	data = []
	for user in users:
		data.append(len(user.has_liked))
	plt.bar(np.arange(len(data)), data)
	plt.xticks(np.arange(len(data)), [user.name for user in users], rotation='vertical')
	plt.title("Likes")
	plt.show()
	plt.clf()

def get_user_data(name):
	post_y = likes_over_time(name)
	post_x = np.arange(len(post_y))
	meme_y = likes_over_time(name, type="meme")
	meme_x = np.arange(len(meme_y))
	message_y = likes_over_time(name, type="message")
	message_x = np.arange(len(message_y))
	# average = average_likes(name)
	# average_data = []
	# for i in range(0, len(post_data)):
	# 	average_data.append(i * average)

	plt.plot(post_x, post_y, label="Posts")
	plt.plot(meme_x, meme_y, label="Memes")
	plt.plot(message_x, message_y, label="Messages")
	# plt.plot(np.arange(len(average_data)), average_data, label="Average")

	plt.legend()

	plt.xlabel("Total Posts")
	plt.ylabel("Total Likes")
	plt.title(name)

	plt.savefig("{}.png".format(name))
	plt.clf()

def store_data():
	names = []
	user_ids = []
	joined = []
	posts = []
	memes = []
	messages = []
	likes = []
	meme_likes = []
	message_likes = []
	has_liked = []

	for name, data in members.items():
		names.append(data.name)
		user_ids.append(data.user_id)
		joined.append(data.date_joined)
		likes.append(data.likes)
		meme_likes.append(data.meme_likes)
		message_likes.append(data.message_likes)
		hasLiked = []
		for post in data.has_liked:
			hasLiked.append(post.toJSON())
		has_liked.append(hasLiked)
		posted = []
		for post in data.posts:
			posted.append(post.toJSON())
		posts.append(posted)
		memed = []
		for post in data.memes:
			memed.append(post.toJSON())
		memes.append(memed)
		messaged = []
		for post in data.messages:
			messaged.append(post.toJSON())
		messages.append(messaged)

	df = pd.DataFrame({
		'names': names,
		'user_ids': user_ids,
		"joined": joined,
		"posts": posts,
		"memes": memes,
		"messages": messages,
		"likes": likes,
		"meme_likes": meme_likes,
		"message_likes": message_likes,
		"has_liked": has_liked
	})

	df.to_excel('users.xlsx', sheet_name='sheet1', index=False)

#
# def topByUser(userName, num, meme): #username, top num of posts, meme or not
# 	posts = []
# 	topPosts = []
# 	if meme:
# 		posts = members[userName].sentMemes
# 	else:
# 		posts = members[userName].sentMessages
#
# 	for i in range(0, num):
# 		curBest = posts[1]
# 		for message in posts:
# 			if len(curBest['favorited_by']) < len(message['favorited_by']):
# 				curBest = message
# 		topPosts.append(curBest)
# 		posts.remove(curBest)
# 	return topPosts
#
# def printMeme(meme):
# 	print str(len(meme['favorited_by'])) + " likes: " + "[" + meme['attachments'][0]['url'] + "]"
# 	print "-" + meme['name']
#
# def printMessage(message):
# 	print str(len(message['favorited_by'])) + " likes: " + message['text']
# 	print "-" + message['name']
#
# def averageLikes(arr):
# 	totalLikes = 0.0
# 	numPosts = len(arr) * 1.0
# 	for message in arr:
# 		totalLikes += len(message['favorited_by'])
# 	if(numPosts == 0):
# 		return 0
# 	else:
# 		return totalLikes / numPosts
# def userSummary(user):
# 	print user.name
# 	print "Likes: [Total: " + str(user.totalMemeLikes + user.totalLikes) + ", Meme: " + str(user.totalMemeLikes) + ", Posts: " + str(user.totalLikes) + "]"
# 	print "Messages: [Total: " + str(user.totalMemes + user.totalPosts) + ", Meme: " + str(user.totalMemes) + ", Posts: " + str(user.totalPosts) + "]"
# 	print "Averages: [Total: " + str(averageLikes(user.sentMemes + user.sentMessages)) + ", Meme: " + str(averageLikes(user.sentMemes)) + ", Posts: " + str(averageLikes(user.sentMessages)) + "]"
# add_users(group_data)
# parse_messages_network(groupmeAPI) #get all messages
# store_data()

parse_messages_sheet()

for post in members['Chai Nunes'].posts:
	print(post.replace(" '", ""))
