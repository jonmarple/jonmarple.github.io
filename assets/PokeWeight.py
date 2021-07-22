# author: Jonathan Marple

from pyexcel_ods import get_data
from bisect import bisect_left
import praw
import time
import re

# Reading pokemon data from spreadsheet
data = get_data("Pokemon Weightlist.ods")

# Number of pokemon in list
numOfPokemon = 151

# Creating lists based on the spreadsheet data
pokemonNums = [list(data.values())[0][i][0] for i in range(numOfPokemon)]
pokemonNames = [list(data.values())[0][i][1] for i in range(numOfPokemon)]
pokemonPounds = [list(data.values())[0][i][2] for i in range(numOfPokemon)]
pokemonKilograms = [list(data.values())[0][i][3] for i in range(numOfPokemon)]

# Function to find the closest pokemon weight to weight input
# @param weight amount to compare to pokemon
# @param units units to measure weight in
# @return index of weight closest to weight param
def findClosestWeight(weight, units):
    if units == "lb":
        pos = bisect_left(pokemonPounds, weight)
        if pos == 0:
            return 0
        if pos == len(pokemonPounds):
            return -1
        before = pokemonPounds[pos - 1]
        after = pokemonPounds[pos]
        if after - weight < weight - before:
           return pos
        else:
           return pos - 1
    elif units == "kg":
        pos = bisect_left(pokemonKilograms, weight)
        if pos == 0:
            return 0
        if pos == len(pokemonKilograms):
            return -1
        before = pokemonKilograms[pos - 1]
        after = pokemonKilograms[pos]
        if after - weight < weight - before:
           return pos
        else:
           return pos - 1

# Function to verify str is a number by converting to float
# @param str string to test
# @return 0 if str can be converted to a number, 1 otherwise
def checkVal(str):
    try:
        float(str)
        return 1
    except ValueError:
        return 0

# Function to remove all special characters and numbers from a string
# @param str string to modify
# @return modified string
def formatStr(str):
    return re.sub('[^A-Za-z]+', '', str)

# Function to remove all characters not desired in a number string
# @param str string to modify
# @return modified string
def formatNum(str):
    return re.sub('[^0-9.]+', '', str)

# Initialize PRAW with a custom User-Agent
bot = praw.Reddit(user_agent='PokeWeight',
                  client_id='',
                  client_secret='',
                  username='',
                  password='')

# Assigning a subreddit
subreddit = bot.subreddit('all')

# Input stream of comments on subreddit
comments = subreddit.stream.comments()

# Looping through comments collected
for comment in comments:

    # Skipping comments posted by bot's account
    if comment.author == "":
        continue

    # Dividing comment into individual strings
    commentParts = comment.body.split(" ")

    # Looping through strings in comment
    i = 0
    for string in commentParts:

        currentWord = formatStr(string.lower())

        if currentWord == "lb" or currentWord == "lbs":
            if i > 0 and checkVal(formatNum(commentParts[i - 1])) == 1:
                lb = float(formatNum(commentParts[i - 1]))
                totalWeight = 0
                indexList = []
                while totalWeight < lb - (lb / 20): # Searching within 5% accuracy
                    indexList.append(findClosestWeight(float(lb - totalWeight), "lb"))
                    totalWeight += pokemonPounds[indexList[len(indexList) - 1]]
                message = "The closest pokemon to " + str(lb) + currentWord + " is "
                j = 0
                for index in indexList:
                    if j == indexList.index(index):
                        message += str(indexList.count(index)) + " " + pokemonNames[index] + " "
                    j += 1
                message += "(" + str(totalWeight) + "lbs)"
                print(message)
                comment.reply(message)
                time.sleep(1)

        if currentWord == "kg":
            if i > 0 and checkVal(formatNum(commentParts[i - 1])) == 1:
                kg = float(formatNum(commentParts[i - 1]))
                totalWeight = 0
                indexList = []
                while totalWeight < kg - (kg / 20): # Searching within 5% accuracy
                    indexList.append(findClosestWeight(float(kg - totalWeight), "kg"))
                    totalWeight += pokemonKilograms[indexList[len(indexList) - 1]]
                message = "The closest pokemon to " + str(kg) + currentWord + " is "
                j = 0
                for index in indexList:
                    if j == indexList.index(index):
                        message += str(indexList.count(index)) + " " + pokemonNames[index] + " "
                    j += 1
                message += "(" + str(totalWeight) + "kg)"
                print(message)
                comment.reply(message)
                time.sleep(1)

        i += 1