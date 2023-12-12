import os
from sys import executable, exit
from shutil import copy, move
from ast import literal_eval
from re import findall
from time import sleep
try:
	from matplotlib import pyplot as plt
except:
	print("Please install the matplotlib correctly in advance. ")
	exit(EOF)
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__)))#解析进入程序所在目录
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
defaultTime = 5
scriptFilepaths = ["linearQuerying.py", "topKQuerying.py"]
dataFilepath = "timeConsumptionResult.txt"
plotFilepath = "timeConsumptionResult.png"
start_value, stop_value, step_size, test_round = 5, 250, 5, 10
defaultLegend = ["linear querying", "advanced querying"]
markers = ["o", "x", "+", "*", "^", "v", "<", ">"]
colors = ["red", "orange", "green", "blue", "yellow", "purple", "pink", "brown"]
defaultFontSize =20
defaultDpi = 1200


def readData(dataFp = dataFilepath, encoding = "utf-8") -> list:
	try:
		if os.path.exists(dataFp):
			with open(dataFp, "r", encoding = encoding) as f:
				return literal_eval(f.read())
		else:
			return []
	except:
		return None

def modify(scriptFps = scriptFilepaths, encoding = "utf-8") -> bool:
	for scriptFp in scriptFps:
		try:
			targetScriptFilepath = os.path.split(scriptFp)[0] + os.path.splitext(os.path.split(scriptFp)[1])[0] + "_backup" + os.path.splitext(os.path.split(scriptFp)[1])[1]
			if os.path.exists(targetScriptFilepath):
				print("Backup script file(s) may already exist. Please remove them. ")
				return False
			copy(scriptFp, targetScriptFilepath)
			with open(scriptFp, "r", encoding = encoding) as f:
				content = f.read()
			toReplaces = findall("\ndefaultTime = .+\\n", content)
			for toReplace in toReplaces:
				content = content.replace(toReplace, "\ndefaultTime = 0\n")
			with open(scriptFp, "w", encoding = encoding) as f:
				f.write(content)
		except:
			return False
	return True

def updateData(data, scriptFps = scriptFilepaths, start = start_value, stop = stop_value, step = step_size, round = test_round) -> None:
	if type(data) != list or len(data) != len(scriptFps): # incorrect data
		data.clear()
		data += [{} for _ in scriptFps]
	for i in range(len(data)):
		if type(data[i]) != dict: # incorrect dict
			data[i] = {}
		with os.popen("\"{0}\" \"{1}\"".format(executable, scriptFps[i])) as p: # to avoid the the time consumption when a new Python script is run for the first time
			_ = p.read()
		for k in range(int(start), int(stop) + 1, int(step)):
			data[i].setdefault(k, [])
			if type(data[i][k]) != list:
				data[i][k] = []
			loopCnt = 0
			while len(data[i][k]) < int(round) and loopCnt < int(round):
				with os.popen("\"{0}\" \"{1}\" /k {2}".format(executable, scriptFps[i], k)) as p:
					content = p.read()
				values = findall("\\d+\\.\\d+ms", content)
				if len(values) == 1:
					try:
						data[i][k].append(float(values[0][:-2]))
						print("The time consumption of (i = {0}, k = {1}, r = {2}) is {3}ms. ".format(i, k, len(data[i][k]) - 1, data[i][k][-1]))
					except:
						print("Errors occurred when converting the time consumption of (i = {0}, k = {1}, r = {2}). ".format(i, k, len(data[i][k]) - 1))
				else:
					print("Errors occurred when handling (i = {0}, k = {1}, r = {2}). ".format(i, k, len(data[i][k]) - 1))
				loopCnt += 1

def restore(scriptFps = scriptFilepaths, encoding = "utf-8") -> bool:
	for scriptFp in scriptFps:
		try:
			targetScriptFilepath = os.path.split(scriptFp)[0] + os.path.splitext(os.path.split(scriptFp)[1])[0] + "_backup" + os.path.splitext(os.path.split(scriptFp)[1])[1]
			if os.path.isfile(targetScriptFilepath):
				os.remove(scriptFp)
				move(targetScriptFilepath, scriptFp)
		except:
			return False
	return True

def dumpData(data, dataFp = dataFilepath, encoding = "utf-8") -> bool:
	try:
		with open(dataFp, "w", encoding = encoding) as f:
			f.write(str(data))
		return True
	except:
		return False

def draw(data, legend = None, plotFp = None, start = start_value, stop = stop_value, step = step_size, round = test_round, font_size = defaultFontSize, dpi = defaultDpi, exception_value = EOF) -> bool:
	try:
		x = list(range(int(start), int(stop) + 1, int(step)))
		ys = [[] for _ in data]
		for key in x:
			for alg in range(len(ys)):
				if key in data[alg] and data[alg][key]:
					ys[alg].append(sum(data[alg][key]) / len(data[alg][key]))
				else:
					ys[alg].append(exception_value)
		plt.rcParams["font.size"] = font_size
		for alg, y in enumerate(ys):
			plt.plot(x, y, marker = markers[alg % len(markers)], color = colors[alg % len(colors)])
		plt.xlim(int(start) - int(step), int(stop) + int(step))
		plt.xlabel("$k$")
		plt.ylabel("Time consumption (ms)")
		if legend and len(legend) == len(ys):
			plt.legend(legend)
		plt.rcParams["figure.dpi"] = dpi
		plt.rcParams["savefig.dpi"] = dpi
		if plotFp:
			plt.savefig(plotFp)
		else:
			plt.show()
		plt.close()
		return True
	except Exception as e:
		print("Draw: {0}. ".format(e))
		return False

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

def main() -> int:
	exit_code = EXIT_SUCCESS
	data = readData(dataFilepath)
	if data is None:
		print("Read data from \"{0}\" failed. ".format(dataFilepath))
		preExit()
		return EXIT_FAILURE
	else:
		print("Read data from \"{0}\" successfully. ".format(dataFilepath))
	if modify(scriptFilepaths):
		print("Modify scripts successfully. ")
	else:
		print("Modify scripts failed. ")
		preExit()
		return EXIT_FAILURE
	updateData(data)
	if restore(scriptFilepaths):
		print("Restore scripts successfully. ")
	else:
		print("Restore scripts failed. Please restore it manually. ")
		exit_code = EXIT_FAILURE
	if dumpData(data, dataFilepath):
		print("Dump data to \"{0}\" successfully. ".format(dataFilepath))
	else:
		print("Dump data to \"{0}\" failed. ".format(dataFilepath))
		preExit()
		return EXIT_FAILURE
	if draw(data, legend = defaultLegend):
		print("Draw successfully. ")
	else:
		print("Draw failed. ")
		preExit()
		return EXIT_FAILURE
	preExit()
	return exit_code



if __name__ == "__main__":
	exit(main())