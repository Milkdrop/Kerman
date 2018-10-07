# KermanCodeforcesAutoHack
A neat script to mercilessly hack Codeforces C++ sources during contests

Dependencies:
It should work for both Python 2 and Python 3.
- pip install bs4
- pip install colorama

Usage:
> Kerman.py -c <ContestID> -p <ProblemLetter> -s <StartPage> -e <EndPage>
Example:
> Kerman.py -c 1059 -p C -s 1 -e 10
To run through pages 1 to 10, testing the problem C from the contest with ID 1059.

There are 3 important files generated for Kerman: **TestGen.cpp, Correct.cpp and Config.txt**

- Config.txt: Can store some neat options like the number of tests to run on a submission before declaring it unhackable.

- Correct.cpp: A C++ Source Code file used as a reference for every test, that each other source would have its output compared with it. Should be chosen with care, if no Correct.cpp file is found, Kerman will automatically browse through the sources until it finds one made by a Master/Grandmaster.

- TestGen.cpp: A C++ Source file that should be edited by the user. It's compiled automatically, and it's used to generate random valid tests for the current problem.
