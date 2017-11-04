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


@app.errorhandler(404)
def not_found(error):
    return "404 Not Found: Invalid REST URL\n", 404


