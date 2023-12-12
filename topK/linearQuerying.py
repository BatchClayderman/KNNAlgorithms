import os
from sys import argv, exit
from ast import literal_eval
from time import sleep, time
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__))) # cd into the location path of this script
except: # it does not work in Jupyter-notebook
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
defaultTime = 5
rndFilepaths = ["rnd.txt"]
seqFilepaths = ["seq1.txt", "seq2.txt"]
defaultK = 5


# sub function #
def getTxt(filepath, index = 0) -> str: # get .txt content
	coding = ("utf-8", "gbk", "utf-16") # codings
	if 0 <= index < len(coding): # in the range
		try:
			with open(filepath, "r", encoding = coding[index]) as f:
				content = f.read()
			return content[1:] if content.startswith("\ufeff") else content # if utf-8 with BOM, remove BOM
		except (UnicodeError, UnicodeDecodeError):
			return getTxt(filepath, index + 1) # recursion
		except:
			return None
	else:
		return None # out of range

def handleLine(node_dict, line, cnt, fname) -> bool: # handle per line
	if line.count(" ") == 1:
		tmp = line.split(" ")
		try:
			key, value = int(tmp[0]), float(tmp[1])
			node_dict.setdefault(key, [])
			node_dict[key].append(value)
			return True
		except:
			print("Line {0} of the file \"{1}\" has been skipped since converting error occurred. ".format(cnt, fname))
			return False
	elif line: # it is not necessary to prompt the empty line
		print("Line {0} of the file \"{1}\" has been skipped since the count of space(s) is not 1. ".format(cnt, fname))
		return False

def getRnds(node_dict, rndFps = rndFilepaths) -> int:
	success_count = 0
	for rndFp in rndFps:
		content = getTxt(rndFp)
		if content is None:
			continue
		content = content.replace("\r", "\n") # filtering "\r"
		while "\n\n" in content: # filtering empty lines
			content = content.replace("\n\n", "\n")
		for cnt, line in enumerate(content.split("\n")):
			handleLine(node_dict, line, cnt, rndFp)
		success_count += 1
	return success_count

def getSeqs(node_dict, accesses, seqFps = seqFilepaths, encoding = "utf-8") -> int: # to simulate the same operation with the improved approach
	success_count = 0
	fs = []
	for seqFp in seqFps:
		try:
			fs.append(open(seqFp, "r", encoding = encoding.replace("-bom", "")))
			accesses.append(0)
			success_count += 1
		except:
			print("Open \"{0}\" failed. ".format(seqFp))
	
	cnt = 0
	while fs and any(fs):
		cnt += 1
		for i, f in enumerate(fs):
			if f is not None:
				try:
					line = f.readline() # do not remove the line separator here so as to judge the EOF of the file
				except:
					success_count -= 1
					print("Read File \"{0}\" failed. Stop reading it. ".format(f.name))
					try: # stop reading if exceptions occurred
						f.close()
					except:
						print("Close File \"{0}\" failed. This may lead to leaks. ".format(f.name))
					fs[i] = None
					continue # do not need to handle the line
				if line:
					accesses[-1] += 1 if handleLine(node_dict, line.replace("\ufeff", "").replace("\n", ""), cnt, seqFp) else 0
				else: # that a line is empty means that the file is finished
					try:
						f.close()
					except:
						print("Close File \"{0}\" failed. This may lead to leaks. ".format(f.name))
					fs[i] = None
	
	for f in fs:
		if f is not None:
			try:
				f.close()
			except:
				print("Close File \"{0}\" failed. This may lead to leaks. ".format(f.name))
	return success_count

def linearScanning(node_dict, k) -> list:
	node_dict = {key:sum(node_dict[key]) for key in list(node_dict.keys())}
	return sorted(node_dict.items(), key = lambda x:x[1], reverse = True)[:k]

def output(linearScanningResults, k, access_count, outputFp = None, encoding = "utf-8") -> bool:
	if outputFp:
		try:
			with open(outputFp, "w", encoding = encoding) as f:
				f.write("Number of sequential accesses: {0}\n".format(access_count))
				f.write("Top {0} objects: \n".format(k))
				for key, value in linearScanningResults:
					f.write("{0}: {1:.2f}\n".format(key, value))
			print("Dump to the result file successfully. ")
			return True
		except Exception as e:
			print("Error writing output file. ")
			print(e)
			return False
	else:
		print("Number of sequential accesses: {0}".format(access_count))
		print("Top {0} objects: ".format(k))
		for key, value in linearScanningResults:
			print("{0}: {1:.2f}".format(key, value))
		return True


# main function #
def preExit(countdownTime = defaultTime) -> None: # we use this function before exiting instead of getch since getch is not OS-independent
	try:
		cntTime = int(countdownTime)
		length = len(str(cntTime))
	except:
		return
	print()
	while cntTime > 0:
		print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime), end = "")
		try:
			sleep(1)
		except:
			print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(0))
			return
		cntTime -= 1
	print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime))

def printHelp() -> None:
	print("Python script for mining the top k best objects by linear scanning. ", end = "\n\n")
	print("Option: ")
	print("\t[/rnds|--rnds|rnds]: Specify that the following options are the input files for random access. ")
	print("\t[/seqs|--seqs|seqs]: Specify that the following options are the input files for descending sequential access. ")
	print("\t[/k|-k|k]: Specify that the following option is the input k. ")
	print("\t[/o|-o|o|/output|--output|output]: Specify that the following option is the output result file. ")
	print("\t[/encoding|--encoding|encoding]: Specify that the following option is the encoding. ", end = "\n\n")
	print("Format: ")
	print("\tpython linearQuerying.py [/rnds|--rnds|rnds] rndFilepath1, rndFilepath2, ... [/seqs|--seqs|seqs] seqFilepath1 seqFilepath2 ... [/k|-k|k] k")
	print("\tpython linearQuerying.py [/rnds|--rnds|rnds] rndFilepath1, rndFilepath2, ... [/seqs|--seqs|seqs] seqFilepath1 seqFilepath2 ... [/encoding|--encoding|encoding] encoding")
	print("\tpython linearQuerying.py [/rnds|--rnds|rnds] rndFilepath1, rndFilepath2, ... [/seqs|--seqs|seqs] seqFilepath1 seqFilepath2 ... [/k|-k|k] k [/o|-o|o|/output|--output|output] outputFilepath")
	print("\tpython linearQuerying.py [/rnds|--rnds|rnds] rndFilepath1, rndFilepath2, ... [/seqs|--seqs|seqs] seqFilepath1 seqFilepath2 ... [/k|-k|k] k [/o|-o|o|/output|--output|output] outputFilepath [/encoding|--encoding|encoding] encoding", end = "\n\n")
	print("Example: ")
	print("\tpython linearQuerying.py /rnds rnd.txt /seqs seq1.txt seq2.txt /k 5")
	print("\tpython linearQuerying.py /rnds rnd.txt /seqs seq1.txt seq2.txt /k 5 /encoding utf-8")
	print("\tpython linearQuerying.py /rnds rnd.txt /seqs seq1.txt seq2.txt /k 5 /output linearScanningResults.txt")
	print("\tpython linearQuerying.py /rnds rnd.txt /seqs seq1.txt seq2.txt /k 5 /output linearScanningResults.txt /encoding utf-8", end = "\n\n")
	print("Exit code: ")
	print("\t{0}\tThe Python script finished successfully. ".format(EXIT_SUCCESS))
	print("\t{0}\tThe Python script finished with some of the input files processed failed. ".format(EXIT_FAILURE))
	print("\t{0}\tThe Python script received unrecognized commandline options. ".format(EOF), end = "\n\n")
	print("Note: Sequence files can be not in descending order according to the scores since this script just perform linear querying. The scores can be negative when using the linear querying algorithm. ", end = "\n\n")

def handleCommandline() -> dict:
	for arg in argv[1:]:
		if arg.lower() in ("/h", "-h", "h", "/help", "--help", "help", "/?", "-?", "?"):
			printHelp()
			return True
	dicts = {"rnds":rndFilepaths, "seqs":seqFilepaths, "k":defaultK, "output":None, "encoding":"utf-8"}
	pointer = None
	for arg in argv[1:]:
		if arg.lower() in ("/rnds", "--rnds", "rnds"):
			pointer = "rnds"
			dicts["rnds"] = [] # restore
		elif arg.lower() in ("/seqs", "--seqs", "seqs"):
			pointer = "seqs"
			dicts["seqs"] = [] # restore
		elif arg.lower() in ("/k", "-k", "k"):
			pointer = "k"
		elif arg.lower() in ("/t", "-t", "t", "/tau", "--tau", "tau"):
			print("The upper bound of the scores is not required in the linear querying algorithm. ")
			return False
		elif arg.lower() in ("/o", "-o", "o", "/output", "--output", "output"):
			pointer = "output"
		elif arg.lower() in ("/encoding", "--encoding", "encoding"):
			pointer = "encoding"
		elif pointer is None:
			print("Error handling commandline, please check your commandline or use \"/help\" for help. ")
			return False
		elif pointer in ("rnds", "seqs"):
			dicts[pointer].append(arg)
		else:
			dicts[pointer] = arg
			pointer = None # reset
	try:
		dicts["k"] = int(dicts["k"])
	except:
		print("Error regarding k as an integer. Please check your commandline. ")
		return False
	return dicts

def main() -> int:
	commandlineArgument = handleCommandline()
	if type(commandlineArgument) == bool:
		return EXIT_SUCCESS if commandlineArgument else EOF
	
	start_time = time()
	node_dict = {}
	accesses = []
	success_rnd = getRnds(node_dict, commandlineArgument["rnds"])
	success_seq = getSeqs(node_dict, accesses, commandlineArgument["seqs"], encoding = commandlineArgument["encoding"])
	linearScanningResults = linearScanning(node_dict, commandlineArgument["k"])
	end_time = time()
	print("Processed files for random access: {0} in total, {1} successful, {2} failed, {3:.2f}% success rate. ".format(len(commandlineArgument["rnds"]), success_rnd, len(commandlineArgument["rnds"]) - success_rnd, success_rnd * 100 / len(commandlineArgument["rnds"])))
	print("Processed files for descending random access: {0} in total, {1} successful, {2} failed, {3:.2f}% success rate. ".format(len(commandlineArgument["seqs"]), success_seq, len(commandlineArgument["seqs"]) - success_seq, success_seq * 100 / len(commandlineArgument["seqs"])))
	output(linearScanningResults, commandlineArgument["k"], sum(accesses), outputFp = commandlineArgument["output"], encoding = commandlineArgument["encoding"])
	print("Time consumption: {0:.3f}ms. ".format((end_time - start_time) * 1000))
	
	preExit()
	return EXIT_SUCCESS if success_rnd == len(commandlineArgument["rnds"]) and success_seq == len(commandlineArgument["seqs"]) else EXIT_FAILURE



if __name__ == "__main__":
	exit(main())