from PartA import tokenize, computeWordFrequencies

import sys
# O(n log(n) + m log(m))
def find_intersection(file1, file2):
    tok1 = tokenize(file1) #O(n)
    tok2 = tokenize(file2) #O(m)
    freq1 = computeWordFrequencies(tok1) #O(n log n)
    freq2 = computeWordFrequencies(tok2) #O(m log m)

    keys1 = set(freq1) #O(n)
    keys2 = set(freq2) #O(m)
    inter = keys1.intersection(keys2)#O(n + m)
    return len(inter)#O(n - m)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        pass
    else:
        print(find_intersection(sys.argv[1], sys.argv[2]))