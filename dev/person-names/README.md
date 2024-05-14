# Common surnames

In some edge cases where IGA can only obtain a text string containing the name of a contributor to a software project, IGA needs to determine whether the name is the name of a person or an organization. This is currently impossible to do with complete accuracy: there are no known foolproof method to identify a name in a string. The best we can hope for is to apply some heuristics.

One of the heuristics IGA uses is to take advantage of the fact that a large fraction of family names in China, Japan, and Korea are drawn from a small subset common to those countries. We can therefore gather lists of these common names and test unknown names against them. If an unknown name string contains a known surname, we can judge that string as being the name of a person. This is not always accurate, of course, but it is a heuristic that works more often than not.

This directory contains common surnames gather from different sources:

* [`korean-surnames.txt`](korean-surnames.txt): the first two columns of <https://simple.wikipedia.org/wiki/List_of_Korean_surnames>, after removing the ones corresponding to North Korea.
* [`japanese-surnames.txt`]():
* [`chinese-surnames.txt`]():
