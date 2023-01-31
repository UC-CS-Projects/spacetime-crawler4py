import sys
import os
import re

#if the amount of lines in filepath is n.
#The time complexity should be O(n["reading"] + n[spliting] + n["splitting on nonalnum"]
def tokenize(filepath):
    if not os.path.isfile(filepath):
        return []
    res = []
    with open(filepath) as text:
        for line in text:
            words = line.split(" ")
            for word in words:
                splitted = re.split('\W+',word)
                for s in splitted:
                    if s.isalnum():
                        res.append(s)
                
    return res
#Should be O(n + n[lowercasing all the tokens])
def computeWordFrequencies(tokens):
    res = {}
    for tok in tokens:
        tok = tok.lower()
        if tok not in res:
            res[tok] = 1
        else:
            res[tok] += 1
    return res
#O(nlogn) + O(n) to sort the dictionary
def printTokens(freq):
    for token,freq in sorted(freq.items(), key = lambda x: (x[1], -x[0]), reverse = True):
        print(token,freq)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        pass
    else:
        filename = sys.argv[1]
        tokens = tokenize(filename)
        freq = computeWordFrequencies(tokens)
        printTokens(freq)