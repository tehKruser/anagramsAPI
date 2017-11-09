# Anagrams API- Ibotta Candidate Project 
by Justin Kruse

---

This anagram API is my submission for the Ibotta Candidate Project. Requirements can be found in the [Ibotta folder](/ibotta).

## Contents
1. [Run locally](#run-locally)
2. [Add words](#add-words)
3. [Delete a single word](#delete-a-single-word)
4. [Delete a word and its anagrams](#delete-a-word-and-its-anagrams)
5. [Delete all words from the data store](#delete-all-words-from-the-data-store)
6. [Get anagrams for a word](#get-anagrams-for-a-word)
7. [Get anagram sets containing at least x words](#get-anagram-sets-containing-at-least-x-words)
8. [Check if a set of words are anagrams of eachother](#check-if-a-set-of-words-are-anagrams-of-eachother)
9. [Get stats on words contained in the data store](#get-stats-on-words-contained-in-the-data-store)
10. [Design](#design)
11. [Testing](#testing)
12. [Benchmarking](#benchmarking)
13. [Other features that could be useful](#other-features-that-could-be-useful)

---

## Run locally
**OS**
Linux/Ubuntu

###### Installs
**Redis for data store**
- Install [Redis](https://redis.io/topics/quickstart)

**Python: Flask and Redis**
- Install [Python](https://packaging.python.org/guides/installing-using-linux-tools/). Version 2.7
- Install [Flask](http://flask.pocoo.org/docs/0.12/installation/)
- Install [Redis](https://pypi.python.org/pypi/redis) for Python

**Ruby**
- Install [Ruby](https://www.ruby-lang.org/en/documentation/installation/)

###### Run
**Start**
1. Start Redis server: ```redis-server --daemonize yes```
2. Clone project to desired directory
3. Terminal 1: Run App
From project directory:
- ```cd app```
- ```FLASK_APP=anagrams.py flask run```
4. Terminal 2: API calls, Test, Benchmark
From project directory:
- ```cd test```
- API calls: see [Ibotta README.md](https://github.com/tehKruser/anagramsAPI/blob/master/ibotta/README.md) for instructions on curl or irb
- Test: ```ruby anagram_test.rb```
- Benchmark: ```ruby anagram_benchmark.rb```

Optional:
To populate words from dictinoary in data store:
- In project directory /script: ```ruby anagram_dbload``` (approx. 3 minutes)

**Stop**
1. Redis shutdown: ```redis-cli shutdown```
2. App shutdown, Terminal 2: Ctrl+c

---

## Add words
Add words to the data store:
`POST /words.json`

**Input**

Name  | Type         | Description
----- | ------------ | -------------
words | string array | words as strings to be posted to data store are in an array

Example: ```curl -i -X POST -d '{ "words": ["read", "dear", "dare"] }' http://127.0.0.1:5000/words.json```

**Response**
```
HTTP/1.0 201 CREATED
```

## Delete a single word
Removes a word from the data store:

`DELETE /words/:word.json`

Example: ```curl -i -X DELETE http://localhost:5000/words/read.json```

**Response**
```
HTTP/1.0 204 NO CONTENT
```

## Delete a word and its anagrams
Removes a word and its anagrams from the data store:

`DELETE /words/:word/anagrams.json`

Example: ```curl -i -X DELETE http://localhost:5000/words/read/anagrams.json```

**Response**
```
HTTP/1.0 204 NO CONTENT
```

## Delete all words from the data store
Removes all words from the data store:

`DELETE /words.json`

Example: ```curl -i -X DELETE http://localhost:5000/words.json```

**Response**
```
HTTP/1.0 204 NO CONTENT
```

## Get anagrams for a word
Get anagrams for a word:

`GET /anagrams/:word.json`

**Parameters**

Name        | Type          | Description
----------- | ------------- | -------------
limit       | int           | maximum number of anagrams to return
propernouns | boolean       | true (default): allow propernouns<br>false: do not return propernouns

Example: ```curl -i -X GET http://localhost:5000/anagrams/read.json```

**Response**
```
HTTP/1.0 200 OK

{
  "anagrams": [
    "Drae",
    "dear",
    "dare"
  ]
}
```

## Get anagram sets containing at least x words
Get all sets of anagrams with at least :x words:

`GET /sets/anagrams/size/:x.json`

:x can be a value > 1 or "max" to return the anagram set(s) that contains the most words

Example: ```curl -i -X GET http://localhost:5000/sets/anagrams/size/3.json```

**Response**
```
HTTP/1.0 200 OK

{
  "sets": [
    {
      "anagrams": [
        [
          "act",
          "tac",
          "cat"
        ]
      ],
      "size": 3
    },
    {
      "anagrams": [
        [
          "read",
          "Drae",
          "dear",
          "dare"
        ]
      ],
      "size": 4
    }
  ]
}
```

## Check if a set of words are anagrams of eachother

Post a set of words and receive a reponse if all words are anagrams of eachother:

`POST /anagrams.json`

Example: ```curl -i -X POST -d '{ "words": ["dork", "dear", "dare"] }' http://127.0.0.1:5000/anagrams.json```

**Response**
```
HTTP/1.0 200 OK

{
  "anagrams": "false"
}
```

## Get stats on words contained in the data store
Get stats for words in data store:

`GET /words/stats.json`

Example: ```curl -i -X GET http://localhost:5000/words/stats.json```

**Response**
```
HTTP/1.0 200 OK

{
  "count": 9,
  "length": {
    "average": 3.56,
    "max": 5,
    "median": 4.0,
    "min": 2
  }
}
```


## Design

**Data store Design with Redis**

Visuals here. 

**Why Redis?**

I chose Redis because it is a fast, in-memory key-value data store that comes with a set of versatile in-memory data structures. 

The key-value aspect is important because I decided on using a key-value method for storing words in anagram groups. 

The versatile data structures is an ideal solution to:
- store the anagrams in sets with no duplicates,
- and track information about word count and lengths in a list.

Also, did I say it was fast? Since I was only using sets and lists, the add/delete operations were of time complexity O(1), or O(N) for N items being added or deleted. The number of words in the data store had no effect.

Admittedly, I had not used Redis before, but I had already started researching it prior to the "coffee interview", as it was listed in the Ibotta Platform Engineer job description as a scalable technology. After spending time in tutorials and understanding Redis usage, I decided it would be a good opportunity to showcase my ability to learn and implement a new technology.

**Python and Flask**

I was already familiar with developing API's in Python and Google App Engine using webapp2, so I started researching if Redis could be used in the GAE standard environment. The answer was 'no', but it could be used with the flexible environment. This bit of research turned me on to Flask, which looked easy and fun, so I decided to use it as the API framework and develop on my local machine.

## Testing

- Edge cases: returning 1 anagram
- running stats after various scenarios

**Results**

```
$ ruby anagram_test.rb
Loaded suite anagram_test
Started
......................

Finished in 0.3829484 seconds.
-----------------------------------------------------------------------------------------------
22 tests, 59 assertions, 0 failures, 0 errors, 0 pendings, 0 omissions, 0 notifications
100% passed
-----------------------------------------------------------------------------------------------
57.45 tests/s, 154.07 assertions/s
```


## Benchmarking

- Discussion

**Results**

POST words

![POST words](https://tehkruser.github.io/anagramsAPI/img/bm_post_words.JPG)

GET anagrams

![GET words](https://tehkruser.github.io/anagramsAPI/img/bm_get_words.JPG)

DELETE words

![DELETE words](https://tehkruser.github.io/anagramsAPI/img/bm_delete_words.JPG)

GET stats

![GET words](https://tehkruser.github.io/anagramsAPI/img/bm_get_stats.JPG)



## Other features that could be useful

- Get stats on anagram sets (i.e. how many sets exist with only :x words)
