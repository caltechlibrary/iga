# Common surnames

In some edge cases where IGA can only obtain a text string containing the name of a contributor to a software project, IGA needs to determine whether the name is the name of a person or an organization. This is currently impossible to do with complete accuracy: there are no known foolproof method to identify a name in a string. The best we can hope for is to apply some heuristics.

One of the heuristics IGA uses is to take advantage of the fact that a large fraction of family names in China, Japan, and Korea are drawn from a small subset common to those countries. We can therefore gather lists of these common names and test unknown names against them. If an unknown name string contains a known surname, we can judge that string as being the name of a person. This is not always accurate; for example, a company might be named after its founder. Still, it is a heuristic that works often enough.

This directory contains common surnames gather from different sources:

* [`korean-surnames.txt`](korean-surnames.txt): the first two columns of <https://simple.wikipedia.org/wiki/List_of_Korean_surnames>, after removing the ones corresponding to North Korea.
* [`japanese-surnames.txt`](japanese-surnames.txt): the unique surnames found in the [ENAMDICT/JMnedict Japanese Proper Names Dictionary Files](https://www.edrdg.org/enamdict/enamdict_doc.html). The dictionary files are licensed under a Creative Commons Attribution-ShareAlike Licence (V4.0). A copy of the XML file can be found in the [enamdict](enamdict) subdirectory.
* [`chinese-surnames.txt`](chinese-surnames.txt): the contents of the relevant columns of most of the tables in <https://en.wikipedia.org/wiki/List_of_common_Chinese_surnames>. The script is the file [`parse-common-names.py`](wikipedia/parse-common-names.py).

These surnames were combined into a single file and used to create the [`surnames.p`] pickle file in the IGA [`iga/data`](../../iga/data) subdirectory.
