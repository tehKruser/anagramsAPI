#!/usr/bin/env python3

from flask import Flask
from flask import jsonify
from flask import request
import redis
import json


app = Flask(__name__)

r = redis.StrictRedis(host='localhost', port=6379, db=0)

def keyWord(word):
	return ''.join(sorted(word)).lower()

def method_is_delete(request):
    '''Workaround for a lack of delete method is the HTML spec for forms.'''
    return request.form.get('_method') == 'DELETE'


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
				r.sadd(keyWord(word), word)
			return '', 201
		
		else:
			return '400 Bad Request : only JSON data supported at this time\n', 400
	
	if request.method == 'DELETE':
		r.flushall()
		return '', 204
		



@app.route("/anagrams/<word>.<data_format>", methods=['GET'])
def word(word=None, data_format=None):
	if request.method == 'GET':
		if data_format == 'json':
			count = r.scard(keyWord(word))
			try:
				limit = int(request.args.get('limit'))
				anagrams = list(r.srandmember(keyWord(word), limit))
				# if limiting to 1 and more than 1 anagram exists- don't return self
				if limit == 1 and count > 1:
					# Must have at least one anagram returned if it exists
					while word == anagrams[0]:
						anagrams = list(r.srandmember(keyWord(word), limit))
			except:
				anagrams = list(r.smembers(keyWord(word)))
			
			try:
				anagrams.remove(word)
			except:
				pass

			return jsonify({'anagrams' : anagrams}), 200

		else:
			return '400 Bad Request : only JSON data supported at this time\n', 400

@app.route("/words/<word>.<data_format>", methods=['DELETE'])
def delete_word(word=None, data_format=None):
	if request.method == 'DELETE':
		r.srem(keyWord(word), word)
		return '', 204


@app.route("/words/stats.<data_format>", methods=['GET'])
def stats(data_format=None):
	if request.method == 'GET':
		#dbSize = r.dbsize()
		mList = []
		keyEntriesSum = 0
		keyLengthSum = 0
		minLength = 999
		maxLength = 0
		medianLength = 0
		averageLength = 0

		for key in r.scan_iter("*"):
			keyLength = len(key)
			keyEntries = r.scard(key)
			# list for length of key and number of entries
			keyStat = []
			keyStat.append(keyLength)
			keyStat.append(keyEntries)
			mList.append(keyStat)
			keyLengthSum += (keyLength * keyEntries)
			keyEntriesSum += keyEntries
			if keyLength < minLength:
				minLength = keyLength
			if keyLength > maxLength:
				maxLength = keyLength

		if keyEntriesSum == 0:
			averageLength = 0
			minLength = 0
		else:
			averageLength = keyLengthSum / keyEntriesSum

		mList.sort(key=lambda x: x[0])
		

		mListSum = 0
		for ea in mList:
			mListSum += ea[1]
			if mListSum > (keyEntriesSum / 2):
				medianLength = ea[0]
				break
			elif mListSum == (keyEntriesSum / 2):
				if keyEntriesSum % 2 == 0:
					medianLength = (ea[0] * 2 + 1) / 2
				else:
					medianLength = ea[0]
				break

		stats_data = {}
		stats_data["count"] = keyEntriesSum
		length_data = {}
		length_data["min"] = minLength
		length_data["max"] = maxLength
		length_data["average"] = averageLength
		length_data["median"] = medianLength
		stats_data["length"] = length_data

		return jsonify(stats_data), 200


@app.errorhandler(404)
def not_found(error):
    return "404 Not Found: Invalid REST URL\n", 404


