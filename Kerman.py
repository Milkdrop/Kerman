from requests import *
from bs4 import BeautifulSoup
from threading import Timer
from sys import argv
from shutil import copyfile
from colorama import Fore, Back, Style
import subprocess, psutil, time, random, atexit, getpass
import sys, os, colorama

colorama.init()

#PRINT FUNCTIONS
sys.stdout.write (Style.BRIGHT)
sys.stdout.flush ()

def PrintFancy (string):
	for i in string:
		if (i == ':'):
			sys.stdout.write (Fore.WHITE + i)
		else:
			sys.stdout.write (Fore.CYAN + i)
	sys.stdout.flush()

def PrintError (string):
	print (Fore.WHITE + "[ " + Fore.RED + "ERRR" + Fore.WHITE + " ] " + string)
	
def PrintWarn (string):
	print (Fore.WHITE + "[ " + Fore.YELLOW + "WARN" + Fore.WHITE + " ] " + string)
	
def PrintOK (string):
	print (Fore.WHITE + "[ " + Fore.GREEN + " OK " + Fore.WHITE + " ] " + string)
	
def PrintInfo (string):
	print (Fore.WHITE + "[ " + Fore.CYAN + "INFO" + Fore.WHITE + " ] " + string)
	
def exit_handler():
	if (NeedToCleanUp):
		PrintInfo ("Cleaning up...")
	
	try: os.remove("SuspectOut")
	except: pass
	try: os.remove("CorrectOut")
	except: pass
	try: os.remove("TestGen")
	except: pass
	try: os.remove("TestGen.exe")
	except: pass
	try: os.remove("Suspect")
	except: pass
	try: os.remove("Correct")
	except: pass
	try: os.remove("Suspect.exe")
	except: pass
	try: os.remove("Correct.exe")
	except: pass
	
atexit.register(exit_handler)
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36'}

#CHECK ARGS
NeedToCleanUp = False
CID = -1
PN = -1
StartPage = 1
EndPage = 5000

BatteringRam = False
ShowHelp = False
PoisonRun = False

Session = ""
Username = ""
Password = ""

arg = 1
while arg < len(argv):
	if (argv[arg] == "--help"):
		ShowHelp = True
	elif (argv[arg] == "help"):
		ShowHelp = True
	elif (argv[arg] == "-h"):
		ShowHelp = True
	elif (argv[arg] == "--BatteringRam"):
		BatteringRam = True
	elif (argv[arg] == "--PoisonRun"):
		PoisonRun = True
	elif (argv[arg] == "-u"):
		Username = argv[arg + 1]
		arg += 1
	elif (argv[arg] == "-c"):
		CID = argv[arg + 1]
		arg += 1
	elif (argv[arg] == "-p"):
		PN = argv[arg + 1]
		arg += 1
	elif (argv[arg] == "-s"):
		StartPage = int(argv[arg + 1])
		arg += 1
	elif (argv[arg] == "-e"):
		EndPage = int(argv[arg + 1])
		arg += 1
	else:
		PrintError ("Unknown Option: " + argv[arg])
		ShowHelp = True
	arg += 1

if ((ShowHelp) or ((CID == -1 or PN == -1) and BatteringRam == False)):
	print ("""Usage: Kerman.py [-c <ContestID>] [-p <ProblemLetter>]
	
Options:	-c: The Contest ID to analyze (1033, 1056, ...)
		-p: The Problem Letter to analyze (A, B, C, D, ...)
		-s: The page on which to start the analysis (1, 2, 3, ...)
		-e: The page on which to end the analysis (10, 11, 12, ...)
		-u: Login with an username (for auto hack uploading). You will be prompted for the password
		-h/--help: Show this help message
		--BatteringRam: Attack a single, user-given, Suspect.cpp file until it breaks
		--PoisonRun: Iterate through all the submissions while only testing for Poison files\n""")
	
	sys.exit(0)

#LOGIN
if (Username != ""):
	PrintInfo ("Using Username: " + Username)
	loginpage = get("http://codeforces.com/enter?back=%2F", headers=headers)
	cookies = {'JSESSIONID' : loginpage.cookies['JSESSIONID']}
	loginpage = loginpage.text
	loginpage = loginpage[loginpage.find("data-csrf"):]
	csrftoken = loginpage[loginpage.find("='") + 2:loginpage.find("'>")]
	
	check = False
	while (check == False):
		Password = getpass.getpass("Password: ")
		login = post("http://codeforces.com/enter?back=%2F", data = {'csrf_token' : csrftoken, 'action' : 'enter', 'handleOrEmail' : Username, 'password' : Password}, cookies=cookies, headers=headers)
		if (login.text.find ("Invalid handle") != -1):
			PrintError ("Wrong Password.")
		else:
			check = True
	
	PrintOK ("Login Successful.")
	
#GET CONFIGS
Blacklist = {}
TestCnt = 500

PoisonCount = 0
try:
	os.walk("Poisons")
except:
	PrintWarn ("No Poisons folder found. Creating...")
	try:
		os.makedirs("Poisons")
	except:
		PrintError ("Couldn't create Poisons folder. Exiting...")
		sys.exit(2)

try:
	os.walk("Poisons/" + str(CID) + str(PN))
	PoisonCount = len(next(os.walk("Poisons/" + str(CID) + str(PN)))[2])
except:
	try:
		os.makedirs("Poisons/" + str(CID) + str(PN))
		PrintInfo ("Created " + str(CID) + str(PN) + " Poison folder.")
	except:
		PrintError ("Couldn't create " + str(CID) + str(PN) + " Poison folder. Exiting...")
		sys.exit(2)

PrintInfo ("Reading Configs...")
try:
	conffile = open("Config.txt", "r")
	conftext = conffile.read()
	conflines = conftext.split('\n')

	for confline in conflines:
		confs = confline.split(" ")
		if (confs[0].lower() == "blacklist"):
			for i in range(1, len(confs)):
				Blacklist[confs[i]] = True
		elif (confs[0].lower() == "testcount"):
			TestCnt = int(confs[1])
		elif (confs[0].lower() == "testrule"):
			pass
except:
	PrintWarn ("No Config.txt file found! Using defaults.")

#BUILD TESTGEN
try:
	testgen = open("TestGen.cpp", "r")
	os.system("g++ -O2 TestGen.cpp -o TestGen")
except:
	PrintError ("No TestGen.cpp file found! Exiting.")
	sys.exit(2)

if (BatteringRam):
	PoisonRun = False
	try:
		suspect = open("Suspect.cpp", "r")
	except:
		PrintError ("No Suspect.cpp file to test in Battering Ram mode!")
		sys.exit(2)

if (PoisonRun):
	if (PoisonCount == 0):
		PrintError ("You have no Poison files!")
		sys.exit(2)
	
#FANCY INTRO
PrintFancy ("""KKKKKKKKK    KKKKKKK\nK:::::::K    K:::::K\nK:::::::K    K:::::K\nK:::::::K   K::::::K\nKK::::::K  K:::::KKK    eeeeeeeeeeee    rrrrr   rrrrrrrrr      mmmmmmm    mmmmmmm     aaaaaaaaaaaaa  nnnn  nnnnnnnn\n  K:::::K K:::::K     ee::::::::::::ee  r::::rrr:::::::::r   mm:::::::m  m:::::::mm   a::::::::::::a n:::nn::::::::nn\n  K::::::K:::::K     e::::::eeeee:::::eer:::::::::::::::::r m::::::::::mm::::::::::m  aaaaaaaaa:::::an::::::::::::::nn\n  K:::::::::::K     e::::::e     e:::::err::::::rrrrr::::::rm::::::::::::::::::::::m           a::::ann:::::::::::::::n\n  K:::::::::::K     e:::::::eeeee::::::e r:::::r     r:::::rm:::::mmm::::::mmm:::::m    aaaaaaa:::::a  n:::::nnnn:::::n\n  K::::::K:::::K    e:::::::::::::::::e  r:::::r     rrrrrrrm::::m   m::::m   m::::m  aa::::::::::::a  n::::n    n::::n\n  K:::::K K:::::K   e::::::eeeeeeeeeee   r:::::r            m::::m   m::::m   m::::m a::::aaaa::::::a  n::::n    n::::n\nKK::::::K  K:::::KKKe:::::::e            r:::::r            m::::m   m::::m   m::::ma::::a    a:::::a  n::::n    n::::n\nK:::::::K   K::::::Ke::::::::e           r:::::r            m::::m   m::::m   m::::ma::::a    a:::::a  n::::n    n::::n\nK:::::::K    K:::::K e::::::::eeeeeeee   r:::::r            m::::m   m::::m   m::::ma:::::aaaa::::::a  n::::n    n::::n\nK:::::::K    K:::::K  ee:::::::::::::e   r:::::r            m::::m   m::::m   m::::m a::::::::::aa:::a n::::n    n::::n\nKKKKKKKKK    KKKKKKK    eeeeeeeeeeeeee   rrrrrrr            mmmmmm   mmmmmm   mmmmmm  aaaaaaaaaa  aaaa nnnnnn    nnnnnn""")
print ("\n                                                       " + Fore.WHITE + "AUTO HACK v2.3")
print ("                                                Made by " + Fore.CYAN + "Loona " + Fore.WHITE + "& " + Fore.MAGENTA + "PinkiePie1189\n")

if (BatteringRam):
	PrintOK ("KERMAN IS CURRENTLY RUNNING IN " + Fore.RED + "BATTERING RAM" + Fore.WHITE + " MODE.")
	
if (PoisonRun):
	PrintOK ("KERMAN IS CURRENTLY RUNNING IN " + Fore.MAGENTA + "POISON RUN" + Fore.WHITE + " MODE.")
	
PrintOK ("NOW LET'S GET TO " + Fore.GREEN + "WORK" + Fore.WHITE + '\n')
	
FNULL = open(os.devnull, 'w')
random.seed(time.time())

NeedToCleanUp = True
#CORRECT CPP SEARCH
try:
	open("Correct.cpp", "r")
except:
	PrintInfo ("No Correct.cpp file found! Searching for one...")
	found = False
	
	for Page in range(StartPage, EndPage+1):
		if (found):
			break
		Problem = 'http://codeforces.com/contest/' + CID + '/status/' + PN + '/page/' + str(Page)
		Soup = BeautifulSoup(get(Problem, headers=headers).content, "html.parser")
		IDData = Soup.find_all("td", {"class": "id-cell"})
		NameData = Soup.find_all("td", {"class": "status-party-cell"})
		LangData = Soup.find_all("td", {"class": ""})
		
		EntryCount = len(IDData)
		cnt = 0
		
		for i in range(EntryCount):
			if (found):
				break
			if (len(NameData[cnt].text.split()) == 2):
				Name = NameData[cnt].text.split()[1]
			else:
				Name = NameData[cnt].text.split()[0]
			
			ID = IDData[cnt].text.split()[0]
			
			if (len(LangData[cnt].text.split()) >= 2):
				Lang = LangData[cnt].text.split()[1]
			else:
				Lang = "INVALID"
			
			if ((Lang == "C++" or Lang == "C++11" or Lang == "C++14" or Lang == "C++17") and ID not in Blacklist and (str(NameData[cnt]).find("Master") != -1 or str(NameData[cnt]).find("Grandmaster") != -1)):
				CorrectFile = open("Correct.cpp",'wb', 0)
				SourcePage = 'http://codeforces.com/contest/' + CID + '/submission/' + ID
				SourceSoup = BeautifulSoup(get(SourcePage, headers=headers).content, "html.parser")
				Source = SourceSoup.find_all("pre", {"class": "prettyprint"})
				check = False
				if (len(Source) > 0):
					check = True
				else:
					for k in range(5):
						SourceSoup = BeautifulSoup(get(SourcePage, headers=headers).content, "html.parser")
						Source = SourceSoup.find_all("pre", {"class": "prettyprint"})
						if (len(Source) > 0):
							check = True
							break
				
				if (check):
					CorrectFile.write(Source[0].text.encode())
					CorrectFile.close()
					PrintInfo ("Using " + Name + "'s Source with ID " + ID + " as a supposedly Correct source.")
					found = True;
				else:
					PrintWarn ("Could not get the Source Code after 5 tries.")
					
			cnt += 1

if (BatteringRam):
	cor = subprocess.Popen("g++ -static -DONLINE_JUDGE -lm -s -x c++ -Wl,--stack=268435456 -O1 -std=c++11 -D__USE_MINGW_ANSI_STDIO=0 Correct.cpp -o Correct", stdout=FNULL, stderr=FNULL)
	cor.wait()
	sus = subprocess.Popen("g++ -static -DONLINE_JUDGE -lm -s -x c++ -Wl,--stack=268435456 -O1 -std=c++11 -D__USE_MINGW_ANSI_STDIO=0 Suspect.cpp -o Suspect", stdout=FNULL, stderr=FNULL)
	sus.wait()
	check = False
	
	#RUN POISONS
	for k in range (PoisonCount):
		if (check):
			break
		os.system("(Correct < Poisons/" + str(CID) + str(PN) + "/Poison" + str(k+1) + ") > CorrectOut")
		os.system("(Suspect < Poisons/" + str(CID) + str(PN) + "/Poison" + str(k+1) + ") > SuspectOut")
		Correct = open("CorrectOut", "r").read().strip()
		Suspect = open("SuspectOut", "r").read().strip()
				
		if (Correct != Suspect and len(Correct) != 0 and len(Suspect) != 0):
			PrintOK ("FOUND MISMATCH ON POISON FILE " + str(k+1))
			input("Press Enter to continue...")
			check = True
				
	k = 0
	while True:
		if (check):
			break
		if ((k + 1) % 100 == 0):
			PrintInfo (str(k + 1) + " TESTS PASSED.")
					
		os.system("(TestGen " + str(random.randint(0, 5000000)) + ") > Test")
		os.system("(Correct < Test) > CorrectOut")
		os.system("(Suspect < Test) > SuspectOut")
				
		Correct = open("CorrectOut", "r").read().strip()
		Suspect = open("SuspectOut", "r").read().strip()
				
		if (Correct != Suspect and len(Correct) != 0 and len(Suspect) != 0):
			PoisonCount += 1
			copyfile("Test", "Poisons/" + str(CID) + str(PN) + "/Poison" + str(PoisonCount))
			PrintOK ("FOUND MISMATCH. CHECK NEW POISON FILE: " + str(PoisonCount))
			input("Press Enter to continue...")
			
			check = True
		k += 1
	
	sys.exit(0)
	
#START SUSPECT SEARCH
for Page in range(StartPage, EndPage+1):
	PrintInfo ("NOW ON PAGE " + str(Page))
	Problem = 'http://codeforces.com/contest/' + CID + '/status/' + PN + '/page/' + str(Page)
	Soup = BeautifulSoup(get(Problem, headers=headers).content, "html.parser")

	IDData = Soup.find_all("td", {"class": "id-cell"})
	NameData = Soup.find_all("td", {"class": "status-party-cell"})
	LangData = Soup.find_all("td", {"class": ""})
	
	EntryCount = len(IDData)
	cnt = 0
	
	for i in range(EntryCount):
		if (len(NameData[cnt].text.split()) == 2):
			Name = NameData[cnt].text.split()[1]
		else:
			Name = NameData[cnt].text.split()[0]
		
		ID = IDData[cnt].text.split()[0]
		
		if (len(LangData[cnt].text.split()) >= 2):
			Lang = LangData[cnt].text.split()[1]
		else:
			Lang = "INVALID"
			
		if ((Lang == "C++" or Lang == "C++11" or Lang == "C++14" or Lang == "C++17") and ID not in Blacklist):
			SuspectFile = open("Suspect.cpp",'wb', 0)
			PrintInfo ("NOW TESTING " + Name + "'S SOURCE WITH ID " + ID)
			SourcePage = 'http://codeforces.com/contest/' + CID + '/submission/' + ID
			SourceSoup = BeautifulSoup(get(SourcePage, headers=headers).content, "html.parser")
			Source = SourceSoup.find_all("pre", {"class": "prettyprint"})
			
			check = False
			if (len(Source) > 0):
				check = True
			else:
				for k in range(5):
					SourceSoup = BeautifulSoup(get(SourcePage, headers=headers).content, "html.parser")
					Source = SourceSoup.find_all("pre", {"class": "prettyprint"})
					if (len(Source) > 0):
						check = True
						break
			
			if (check):
				SuspectFile.write(Source[0].text.encode())
				SuspectFile.close()
			else:
				PrintWarn ("Could not get the Source Code after 5 tries.")
			
			#START KERMAN SESSION
			cor = subprocess.Popen("g++ -static -DONLINE_JUDGE -lm -s -x c++ -Wl,--stack=268435456 -O1 -std=c++11 -D__USE_MINGW_ANSI_STDIO=0 Correct.cpp -o Correct", stdout=FNULL, stderr=FNULL)
			cor.wait()
			sus = subprocess.Popen("g++ -static -DONLINE_JUDGE -lm -s -x c++ -Wl,--stack=268435456 -O1 -std=c++11 -D__USE_MINGW_ANSI_STDIO=0 Suspect.cpp -o Suspect", stdout=FNULL, stderr=FNULL)
			sus.wait()
			
			check = False
			
			#RUN POISONS
			for k in range (PoisonCount):
				if (check):
					break
				os.system("(Correct < Poisons/" + str(CID) + str(PN) + "/Poison" + str(k+1) + ") > CorrectOut")
				os.system("(Suspect < Poisons/" + str(CID) + str(PN) + "/Poison" + str(k+1) + ") > SuspectOut")
				Correct = open("CorrectOut", "r").read().strip()
				Suspect = open("SuspectOut", "r").read().strip()
				
				if (Correct != Suspect and len(Correct) != 0 and len(Suspect) != 0):
					PrintOK ("FOUND MISMATCH ON POISON FILE " + str(k+1))
					if (Username != ""):
						TestFile = open("Poisons/" + str(CID) + str(PN) + "/Poison" + str(k+1), "rb").read()
						submissionpage = get("http://codeforces.com/contest/" + str(CID) + "/challenge/" + str(ID), cookies=cookies, headers=headers).text
						submissionpage = submissionpage[submissionpage.find("data-csrf"):]
						csrftoken = submissionpage[submissionpage.find("='") + 2:submissionpage.find("'>")]
						hack = post("http://codeforces.com/data/challenge?csrf_token=" + csrftoken, files={'csrf_token': csrftoken, 'action': 'challengeFormSubmitted', 'submissionId': str(ID), 'previousUrl': "http://codeforces.com/contest/" + str(CID) + "/challenge/" + str(ID), 'inputType': 'manual', 'testcase': TestFile, 'testcaseFromFile' : '', 'programTypeId': 50}, cookies=cookies, headers=headers)
						
						if (hack.status_code == 200):
							PrintOK ("Hack Uploaded.")
						else:
							PrintWarn ("Something went wrong with the hack upload.")
					else:
						input("Press Enter to continue...")
					check = True
			
			#RUN RANDOM TESTS
			if (PoisonRun == False):
				for k in range (TestCnt):
					if (check):
						break
					if ((k + 1) % 100 == 0):
						PrintInfo (str(k + 1) + " TESTS PASSED.")
						
					os.system("(TestGen " + str(random.randint(0, 5000000)) + ") > Test")
					os.system("(Correct < Test) > CorrectOut")
					os.system("(Suspect < Test) > SuspectOut")
					
					Correct = open("CorrectOut", "r").read().strip()
					Suspect = open("SuspectOut", "r").read().strip()
					
					if (Correct != Suspect and len(Correct) != 0 and len(Suspect) != 0):
						PoisonCount += 1
						copyfile("Test", "Poisons/" + str(CID) + str(PN) + "/Poison" + str(PoisonCount))
						PrintOK ("FOUND MISMATCH. CHECK NEW POISON FILE " + str(PoisonCount))
						if (Username != ""):
							TestFile = open("Test", "rb").read()
							submissionpage = get("http://codeforces.com/contest/" + str(CID) + "/challenge/" + str(ID), cookies=cookies, headers=headers).text
							submissionpage = submissionpage[submissionpage.find("data-csrf"):]
							csrftoken = submissionpage[submissionpage.find("='") + 2:submissionpage.find("'>")]
							hack = post("http://codeforces.com/data/challenge?csrf_token=" + csrftoken, files={'csrf_token': csrftoken, 'action': 'challengeFormSubmitted', 'submissionId': str(ID), 'previousUrl': "http://codeforces.com/contest/" + str(CID) + "/challenge/" + str(ID), 'inputType': 'manual', 'testcase': TestFile, 'testcaseFromFile' : '', 'programTypeId': 50}, cookies=cookies, headers=headers)
							
							if (hack.status_code == 200):
								PrintOK ("Hack Uploaded.")
							else:
								PrintWarn ("Something went wrong with the hack upload.")
						else:
							input("Press Enter to continue...")
						check = True
		cnt += 1