#!/usr/bin/env python3

from flask import Flask
from flask import jsonify
from flask import request
import random
import redis
import json


app = Flask(__name__)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
s = redis.StrictRedis(host='localhost', port=6379, db=1)

lengthsKey = "lengths"
maxGroupCountKey = "maxGroupCount"

def keyWord(word):
	return ''.join(sorted(word)).lower()


def groupKeyWord(count):
	return "groupSize" + str(count)


def incrementValueAtIndexinDB1(index, increment):
	listLength = int(s.llen(lengthsKey))

	# create indices in db1, if needed
	if index >= listLength:
		for i in range(0, index - listLength + 1, 1):
			s.rpush(lengthsKey, 0)

	value = int(s.lindex(lengthsKey, index))
	value += increment

	s.lset(lengthsKey, index, value)


def decrementValueAtIndexinDB1(index, decrement):
	value = int(s.lindex(lengthsKey, index))
	if value > 0:
		value -= decrement

	s.lset(lengthsKey, index, value)


def updateGroupsOfSize(key, groupSizeDelta):
	groupCount = r.scard(key)
	#print("groupCount", groupCount)

	# if group increased in size, remove key from previous group. vice versa
	s.srem(groupKeyWord(groupCount - groupSizeDelta), key)

	'''
	if groupSizeDelta == 1:
		s.srem(groupKeyWord(groupCount - 1), key)
	else:
		s.srem(groupKeyWord(groupCount + 1), key)
	'''
	# add key to new group count key
	s.sadd(groupKeyWord(groupCount), key)

	# if group decreased in size, check that max group size still has keys
	if groupSizeDelta < 0:
		#print("decrement branch")
		currentMaxGroupCount = int(s.spop(maxGroupCountKey)[0])
		#print("currentMaxGroupCount:", currentMaxGroupCount)
		if groupCount + 1 == currentMaxGroupCount:
			anagramKeyCount = int(s.scard(groupKeyWord(currentMaxGroupCount)))
			if anagramKeyCount > 0:
				#print("staying the same")
				s.sadd(maxGroupCountKey, currentMaxGroupCount)
			else:
				#print("moving to one lower group size")
				s.sadd(maxGroupCountKey, currentMaxGroupCount - 1)
	else:
		try:
			currentMaxGroupCount = int(s.spop(maxGroupCountKey))
		except:
			currentMaxGroupCount = 0

		if groupCount > currentMaxGroupCount:
			s.sadd(maxGroupCountKey, groupCount)
		else:
			s.sadd(maxGroupCountKey, currentMaxGroupCount)


@app.route("/anagrams.<data_format>", methods=['POST'])
def areAnagrams(word=None, data_format=None):
	if request.method == 'POST':
		if data_format == 'json':
			try:
				data = request.get_json(force=True)
			except:
				# return 400: content type of entity not understood
				return "400 Bad Request: Check syntax of JSON data\n", 400
			
			try:
				words = data['words']
			except:
				# return 422: content type understood, missing entity key
				return '422 Unprocessable Entity: Missing "words" entity\n', 422

			groupKey = keyWord(words[0])
			groupMembers = r.smembers(groupKey)
			for word in words:
				if keyWord(word) != groupKey or word not in groupMembers:
					return jsonify({'anagrams' : "false"})

			return jsonify({'anagrams' : "true"})
		else:
			return '400 Bad Request : only JSON data supported at this time\n', 400


@app.route("/anagrams/<word>.<data_format>", methods=['GET'])
def word(word=None, data_format=None):
	if request.method == 'GET':
		if data_format == 'json':

			anagrams = list(r.smembers(keyWord(word)))
			
			# remove word if in list
			try:
				anagrams.remove(word)
			except:
				pass

			# remove proper nouns if requested
			try:
				properNoun = request.args.get('propernoun')
				if properNoun.lower() == "false":
					try:
						for anagram in anagrams:
							if anagram[0].isupper():
								anagrams.remove(anagram)
					except:
						print("Failed filter")
						pass
			except:
				pass	
			
			# limit number of anagrams
			try:
				limit = int(request.args.get('limit'))
				anagrams = random.sample(anagrams, limit)
			except:
				pass

			return jsonify({'anagrams' : anagrams}), 200

		else:
			return '400 Bad Request : only JSON data supported at this time\n', 400


@app.route("/anagrams/groupsOfMinimumSize/<minsize>.<data_format>", methods=['GET'])
def anagramgroups(minsize=None, data_format=None):
	if request.method == 'GET':
		try:
			currentMaxGroupCount = int(list(s.smembers(maxGroupCountKey))[0])
		except:
			currentMaxGroupCount = 0

		if minsize == "max":
			mostAnagramsKeys = list(s.smembers(groupKeyWord(currentMaxGroupCount)))

			mostAnagrams = []
			for key in mostAnagramsKeys:
				mostAnagrams.append(list(r.smembers(key)))

			return jsonify({'most_anagrams' : mostAnagrams}), 200
		else:
			try:
				minSize = int(minsize)
				groupSizes = {}
				for size in range(minSize, currentMaxGroupCount + 1, 1):
					anagramGroup = []
					anagramKeysInGroupSize = list(s.smembers(groupKeyWord(size)))
					for key in anagramKeysInGroupSize:
						anagramGroup.append(list(r.smembers(key)))
					groupSizes[str(size)] = anagramGroup

				return jsonify({'anagram_group_sizes' : groupSizes}), 200

			except:
				return '400 Bad Request : size must be max or an integer\n', 400


@app.route("/words.<data_format>", methods=['POST', 'DELETE'])
def words(data_format=None):
	if request.method == 'POST':
		if data_format == 'json':
			try:
				data = request.get_json(force=True)
			except:
				# return 400: content type of entity not understood
				return "400 Bad Request: Check syntax of JSON data\n", 400
			
			try:
				words = data['words']
			except:
				# return 422: content type understood, missing entity key
				return '422 Unprocessable Entity: Missing "words" entity\n', 422
			
			for word in words:
				new = r.sadd(keyWord(word), word)
				if new == 1:
					incrementValueAtIndexinDB1(len(word), 1)
					updateGroupsOfSize(keyWord(word), 1)


			return '', 201
		
		else:
			return '400 Bad Request : only JSON data supported at this time\n', 400
	
	if request.method == 'DELETE':
		r.flushall()
		return '', 204


@app.route("/words/<word>.<data_format>", methods=['DELETE'])
def delete_word(word=None, data_format=None):
	if request.method == 'DELETE':
		removed = r.srem(keyWord(word), word)
		if removed == 1:
			decrementValueAtIndexinDB1(len(word), 1)
			updateGroupsOfSize(keyWord(word), -1)
		return '', 204


@app.route("/words/<word>/anagrams.<data_format>", methods=['DELETE'])
def delete_anagrams(word=None, data_format=None):
	if request.method == 'DELETE':
		anagramCount = int(r.scard(keyWord(word)))
		r.delete(keyWord(word))
		removed = s.srem(groupKeyWord(anagramCount), keyWord(word))
		if removed == 1:
			decrementValueAtIndexinDB1(len(word), anagramCount)
		return '', 204


@app.route("/words/stats.<data_format>", methods=['GET'])
def stats(data_format=None):
	if request.method == 'GET':

		wordCountTotal = 0
		charCountTotal = 0
		minWordLength = 999
		maxWordLength = 0
		averageWordLength = 0
		medianSum = 0
		medianWordLength = 0

		# bucket indices represent word lengths
		# bucket 0 is not a word length
		buckets = s.llen(lengthsKey) - 1
		#print("buckets", buckets)

		# get total words in buckets
		for charCount in range(1, buckets + 1, 1):
			wordCountAtIndex = int(s.lindex(lengthsKey, charCount))
			wordCountTotal +=  wordCountAtIndex
			charCountTotal = charCountTotal + (charCount * wordCountAtIndex)
			# find min
			if wordCountAtIndex > 0 and minWordLength > charCount:
				minWordLength = charCount
			# find max
			if wordCountAtIndex > 0 and charCount > maxWordLength:
				maxWordLength = charCount

		#print("wordCountTotal", wordCountTotal)
		# find median
		if wordCountTotal > 0:
			for charCount in range(1, buckets + 1, 1):
				medianSum += int(s.lindex(lengthsKey, charCount))
				#print("medianSum:", medianSum)
				# median != 0 not needed for the first logical check
				if medianSum > (wordCountTotal / 2) and medianSum != 0:
					#print("Branch 1")
					#print("charCount", charCount)
					medianWordLength = charCount
					break
				elif medianSum == (wordCountTotal / 2) and medianSum != 0:
					if wordCountTotal % 2 == 0:
						medianWordLength = (charCount * 2 + 1) / 2
						#print("Branch 3")
						#print("medianWordLength", medianWordLength)
					else:
						medianWordLength = charCount
						#print("Branch 4")
						#print("medianWordLength", medianWordLength)
					break

		# find average word length
		if wordCountTotal == 0:
			averageWordLength = 0
			minWordLength = 0
		else:
			averageWordLength =  charCountTotal / wordCountTotal
			#print("charCountTotal,", charCountTotal)
			#print("wordCountTotal", wordCountTotal)

		stats_data = {}
		stats_data["count"] = wordCountTotal
		length_data = {}
		length_data["min"] = minWordLength
		length_data["max"] = maxWordLength
		length_data["average"] = averageWordLength
		length_data["median"] = medianWordLength
		stats_data["length"] = length_data

		return jsonify(stats_data), 200


@app.route('/')
def hello_client():
  return 'Hello from anagramsAPI!'


@app.errorhandler(404)
def not_found(error):
    return "404 Not Found: Invalid REST URL\n", 404


