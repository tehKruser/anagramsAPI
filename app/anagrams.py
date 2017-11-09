#!/usr/bin/env python3

from flask import Flask
from flask import jsonify
from flask import request
import random
import redis
import json

app = Flask(__name__)

db0 = redis.StrictRedis(host='localhost', port=6379, db=0)
db1 = redis.StrictRedis(host='localhost', port=6379, db=1)

KEY_WORD_LENGTHS = "countOfWordLengths"
KEY_MAX_GROUP_SIZE = "maxGroupSize"


def keyWord(word):
	return ''.join(sorted(word.lower()))


def groupKeyWord(count):
	return "groupSize" + str(count)


def formatData(data, dataFormat):
	if dataFormat == 'json':
		return jsonify(data)
	# can be expanded for more data types
	else:
		return None


def getFormattedPostData(data_format):
	if data_format == 'json':
		try:
			return request.get_json(force=True)
		except:
			return None
	# can be expanded to accept more post types
	else:
		return None


def isValidDataFormat(data_format):
	if data_format == 'json':
		return True
	else:
		return False


# Update count of words with length of index
def updateDB1WordLengths(index, delta):
	# if delta is positive, check if room is needed in list index
	if delta > 0:
		listLength = int(db1.llen(KEY_WORD_LENGTHS))

		# create indices in db1, if needed
		if index >= listLength:
			for i in range(0, index - listLength + 1, 1):
				db1.rpush(KEY_WORD_LENGTHS, 0)
	
	newValue = int(db1.lindex(KEY_WORD_LENGTHS, index)) + delta
	db1.lset(KEY_WORD_LENGTHS, index, newValue)


# update anagram group size in db1
def updateDB1GroupSizes(key, groupSizeDelta):
	if db0.exists(key):
		newGroupSize = db0.scard(key)
	else:
		newGroupSize = 0

	# where the key group is currently sitting
	currentGroupSize = newGroupSize - groupSizeDelta

	# if group changed in size, remove key from previous group. vice versa
	db1.srem(groupKeyWord(currentGroupSize), key)

	# update to new group bucket. Don't place in bucket if group count is 0
	if newGroupSize != 0:
		db1.sadd(groupKeyWord(newGroupSize), key)

	# compare to max group size and update new max if new group is larger
	if db1.exists(KEY_MAX_GROUP_SIZE):
		currentMaxGroupSize = int( list(db1.smembers(KEY_MAX_GROUP_SIZE) )[0] )
	else:
		currentMaxGroupSize = 0
		db1.sadd(KEY_MAX_GROUP_SIZE, currentMaxGroupSize)
	
	if newGroupSize > currentMaxGroupSize:
		temp = db1.spop(KEY_MAX_GROUP_SIZE)
		db1.sadd(KEY_MAX_GROUP_SIZE, newGroupSize)
	else:
		# check that max group still has entries; if none, then update to next
		maxGroupSetSize = int(db1.scard(groupKeyWord(currentMaxGroupSize)))
		if maxGroupSetSize == 0:
			for groupSize in range(currentMaxGroupSize, -1, -1):
				if int(db1.scard(groupKeyWord(groupSize))) > 0:
					temp = db1.spop(KEY_MAX_GROUP_SIZE)
					db1.sadd(KEY_MAX_GROUP_SIZE, groupSize)
					break


@app.route("/anagrams.<data_format>", methods=['POST'])
def are_anagrams(word=None, data_format=None):
	if not isValidDataFormat(data_format):
		return '400 Bad Request : only JSON data supported at this time\n', 400
	elif request.method == 'POST':
		form_data = getFormattedPostData(data_format)
		if data_format is None:
			return '400 Bad Request : only JSON data supported at this time\n', 400
		else:
			try:
				words = form_data['words']
			except:
				# return 422: content type understood, missing entity key
				return '422 Unprocessable Entity: Missing "words" entity\n', 422

			data ={'anagrams' : "true"}
			anagrams = db0.smembers(keyWord(words[0]))
			for word in words:
				# logic here is that the words have to exist in the data store
				if word not in anagrams:
					data = {'anagrams' : "false"}
					break

			data = formatData(data, data_format)
			return data, 200


@app.route("/anagrams/<word>.<data_format>", methods=['GET'])
def word(word=None, data_format=None):
	if not isValidDataFormat(data_format):
		return '400 Bad Request : only JSON data supported at this time\n', 400
	elif request.method == 'GET':
		anagrams = list(db0.smembers(keyWord(word)))
		try:
			anagrams.remove(word)
		except:
			pass

		# remove proper nouns if requested
		if 'propernouns' in request.args:
			propernouns = request.args.get('propernouns')
			if propernouns.lower() == "false":
				for anagram in anagrams:
					if anagram[0].isupper():
						anagrams.remove(anagram)	
		
		# limit number of anagrams
		if 'limit' in request.args:
			try:
				limit = int(request.args.get('limit'))
				anagrams = random.sample(anagrams, limit)
			except:
				pass

		data = formatData({'anagrams' : anagrams}, data_format)
		return data, 200


@app.route("/anagrams/size/<min_size>.<data_format>", methods=['GET'])
def anagram_sets(min_size=None, data_format=None):
	if not isValidDataFormat(data_format):
		return '400 Bad Request : only JSON data supported at this time\n', 400
	elif request.method == 'GET':
		if db1.scard(KEY_MAX_GROUP_SIZE) > 0:
			maxGroupSizeinDB1 = int(list(db1.smembers(KEY_MAX_GROUP_SIZE))[0])
		else:
			maxGroupSizeinDB1 = 0

		size_start = 0
		size_end = 0

		if min_size.lstrip('-').isdigit():
			if int(min_size) > 0:
				size_start = int(min_size)
				size_end = maxGroupSizeinDB1 + 1
			elif int(min_size) < 0:
				# Option: negative values get last X group sizes
				size_end = maxGroupSizeinDB1 + 1
				size_start = size_end + int(min_size)
			else:
				return '400 Bad Request : size must be max or an integer not equal to 0\n', 400
		else:
			if min_size == 'max':
				size_start = maxGroupSizeinDB1
				size_end = maxGroupSizeinDB1 + 1
			else:
				return '400 Bad Request : size must be max or an integer not equal to 0\n', 400

		sets = []
		for size in range(size_start, size_end, 1):
			anagramSet = {}
			anagramSet['size'] = size
			anagrams = []
			anagramKeysInGroupSize = list(db1.smembers(groupKeyWord(size)))
			for key in anagramKeysInGroupSize:
				anagrams.append(list(db0.smembers(key)))
			anagramSet['anagrams'] = anagrams
			sets.append(anagramSet)

		data = formatData({'sets' : sets }, data_format)
		return data, 200


@app.route("/words.<data_format>", methods=['POST', 'DELETE'])
def words(data_format=None):
	if request.method == 'POST':
		if not isValidDataFormat(data_format):
			return '400 Bad Request : only JSON data supported at this time\n', 400
		else:
			data = getFormattedPostData(data_format)
			if data is None:
				# return 400: content type of entity not understood
				return "400 Bad Request: Check syntax of data\n", 400
			
			try:
				words = data['words']
			except:
				# return 422: content type understood, missing entity key
				return '422 Unprocessable Entity: Missing "words" entity\n', 422
			
			for word in words:
				new = db0.sadd(keyWord(word), word)
				if new == 1:
					updateDB1WordLengths(len(word), 1)
					updateDB1GroupSizes(keyWord(word), 1)

			return '', 201
	
	if request.method == 'DELETE':
		# removes from db0 and db1
		db0.flushall()
		return '', 204


@app.route("/words/<word>.<data_format>", methods=['DELETE'])
def delete_word(word=None, data_format=None):
	if request.method == 'DELETE':
		removed = db0.srem(keyWord(word), word)
		if removed == 1:
			updateDB1WordLengths(len(word), -1)
			updateDB1GroupSizes(keyWord(word), -1)
		return '', 204


@app.route("/words/<word>/anagrams.<data_format>", methods=['DELETE'])
def delete_anagrams(word=None, data_format=None):
	if request.method == 'DELETE':
		anagramCount = int(db0.scard(keyWord(word)))
		db0.delete(keyWord(word))
		removed = db1.srem(groupKeyWord(anagramCount), keyWord(word))
		if removed == 1:
			updateDB1WordLengths(len(word), -anagramCount)
		return '', 204


@app.route("/words/stats.<data_format>", methods=['GET'])
def stats(data_format=None):
	if not isValidDataFormat(data_format):
		return '400 Bad Request : only JSON data supported at this time\n', 400
	elif request.method == 'GET':

		wordCountTotal = 0
		charCountTotal = 0
		minWordLength = 999
		maxWordLength = 0
		averageWordLength = 0
		medianSum = 0
		medianWordLength = 0

		# bucket indices represent word lengths
		# bucket 0 is not a word length
		buckets = db1.llen(KEY_WORD_LENGTHS) - 1

		# get total words in buckets
		for charCount in range(1, buckets + 1, 1):
			wordCountAtIndex = int(db1.lindex(KEY_WORD_LENGTHS, charCount))
			wordCountTotal +=  wordCountAtIndex
			charCountTotal = charCountTotal + (charCount * wordCountAtIndex)
			# find min
			if wordCountAtIndex > 0 and minWordLength > charCount:
				minWordLength = charCount
			# find max
			if wordCountAtIndex > 0 and charCount > maxWordLength:
				maxWordLength = charCount

		# find median
		if wordCountTotal > 0:
			for charCount in range(1, buckets + 1, 1):
				medianSum += int(db1.lindex(KEY_WORD_LENGTHS, charCount))
				if (wordCountTotal / 2.0) - float(medianSum) < 1 and medianSum != 0:
					if (wordCountTotal / 2.0) == float(medianSum) and (wordCountTotal % 2) == 0:
						medianWordLength = (charCount * 2 + 1) / 2.0
					elif (wordCountTotal / 2.0) - float(medianSum) < 0:
						medianWordLength = float(charCount - 1)
					else:
						medianWordLength = float(charCount + 1)
					break

		# find average word length
		if wordCountTotal == 0:
			averageWordLength = 0
			minWordLength = 0
		else:
			averageWordLength =  float(charCountTotal) / wordCountTotal

		stats_data = {}
		stats_data["count"] = wordCountTotal
		length_data = {}
		length_data["min"] = minWordLength
		length_data["max"] = maxWordLength
		length_data["average"] = round(averageWordLength, 2)
		length_data["median"] = round(medianWordLength, 1)
		stats_data["length"] = length_data

		data = formatData(stats_data, data_format)
		return data, 200


@app.route('/')
def hello_client():
  return 'Hello from anagramsAPI!'


@app.errorhandler(404)
def not_found(error):
    return "404 Not Found: Invalid URL\n", 404