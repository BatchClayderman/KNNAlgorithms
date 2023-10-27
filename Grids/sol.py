import os
from sys import argv, exit
from random import randint, uniform
from time import time
try:
	from msvcrt import getch
	def press_any_key_to_continue():
		while kbhit():
			getch()
		getch()
except:
	def press_any_key_to_continue():
		tmp = input()
		if tmp:
			return bytes(tmp[0], encoding = "utf-8")
		else:
			return b"\n"
try:
	from numpy import all as np_all, any as np_any, argsort, array, c_, in1d, load, r_, save, savetxt, unique, where
	__import__("numpy").set_printoptions(suppress = True) # just use once
except Exception as e:
	print(e)
	print("Please correctly install numpy library first and press any key to exit. ")
	press_any_key_to_continue()
	exit(-1)
try:
	from matplotlib import pyplot as plt
	def drawData(data, dpi = 300, filepath = None) -> None:
		plt.scatter(data[:, 1], data[:, 0], marker = ".", color = "orange")
		plt.rcParams["figure.dpi"] = dpi
		plt.rcParams["savefig.dpi"] = dpi
		if filepath:
			plt.savefig(filepath)
		else:
			plt.show()
		plt.close()
except: # just an extension function
	pass
try:
	from tqdm import tqdm
	isTqdmAvailable = True
except: # just an extension function
	isTqdmAvailable = False
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__))) # cd into current folder
except:
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
global_offsets = {} # to speed up
global_depth = 0
global_accessed_cell = 0
global_scanned_cell = 0
sourceFilepath = "Gowalla_totalCheckins.txt"
gridNumpyFilepathFormat = "gridNumpy_{0}_{1}.npy" # .format(xGridCount, yGridCount)
gridDictionaryFilepathFormat = "gridDictionary_{0}_{1}.txt" # .format(xGridCount, yGridCount)
gridScatterFilepath = "gridScatter.png"
dpi = 1200
maxK = 1000
N = 10000 # repeat


class KNNSet:
	def __init__(self, q, k, lists = array([], dtype = "float64").reshape(0, 4)):
		self.q = q
		self.k = k
		assert(k > 0)
		self.t = None # max distance
		self.lists = lists # line of array = (latitude, longitude, ID, distance)
	def update(self, lists):
		self.lists = r_[self.lists, lists]
		self.lists = self.lists[argsort(self.lists[:, 3])][:self.k, :]
		if len(self.lists) >= self.k: # can use t to cut
			self.t = self.lists[-1][3]


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

def readSource(sourceFp = sourceFilepath) -> array:
	print("Reading and handling from source file \"{0}\", please wait. ".format(sourceFilepath)) # for info
	content = getTxt(sourceFilepath)
	if content is None:
		return None
	content = content.replace("\r", "\n") # filtering "\r"
	while "\n\n" in content: # filtering empty lines
		content = content.replace("\n\n", "\n")
	data = [(float(line.split("\t")[-3]), float(line.split("\t")[-2]), int(line.split("\t")[-1])) for line in content.split("\n") if line.count("\t") == 4] # clear unexpected lines in incorrect format (if they exist)
	data = array(data, dtype = "float64")
	#print(data) # for debug
	print("Data are gathered, containing {0} items. ".format(len(data))) # for info
	data = unique(data, axis = 0) # clearing repeated items
	#print(data) # for debug
	print("Repeated data cleared, there is/are {0} item(s) remaining. ".format(len(data))) # for info
	data = data[where((data[:, 0] >= -90) & (data[:, 0] <= 90) & (data[:, 1] >= -180) & (data[:, 1] <= 180))] # clearing abnormal items
	#print(data) # for debug
	print("Data clearing performed, there is/are {0} item(s) remaining. ".format(len(data))) # for info
	return data

def buildGrid(xGridCnt, yGridCnt,  gridNumpyFp = gridNumpyFilepathFormat.format(100, 100), gridDictionaryFp = gridDictionaryFilepathFormat.format(100, 100), encoding = "utf-8") -> tuple:
	# read source #
	data = readSource()
	if data is None:
		print("Error reading sources, please press any key to exit. ")
		press_any_key_to_continue()
		return None, None
	
	# grid indexing #
	assert(type(xGridCnt) == int and type(yGridCnt) == int and xGridCnt > 0 and yGridCnt > 0)
	max_latitude = max(data[:, 0])
	min_latitude = min(data[:, 0])
	max_longitude = max(data[:, 1])
	min_longitude = min(data[:, 1])
	print({"max_latitude":max_latitude, "min_latitude":min_latitude, "max_longitude":max_longitude, "min_longitude":min_longitude}) # for info
	distance_latitude = (max_latitude - min_latitude) / xGridCnt
	distance_longitude = (max_longitude - min_longitude) / yGridCnt
	print("The distance of latitude per grid is {0} whilst the distance of longitude per grid is {1}. ".format(distance_latitude, distance_longitude)) # for info
	data = c_[data, (data[:, 0] - min_latitude) // distance_latitude, (data[:, 1] - min_longitude) // distance_longitude]
	mask = data[:, 0] == max_latitude # handle the boundary
	data[mask, -2] = xGridCnt - 1
	mask = data[:, 1] == max_longitude # handle the boundary
	data[mask, -1] = yGridCnt - 1
	#print(data) # for debug
	
	# handle grid dicts
	gridDicts = {					\
		"max_latitude":max_latitude, 			\
		"min_latitude":min_latitude, 			\
		"max_longitude":max_longitude, 		\
		"min_longitude":min_longitude, 		\
		"distance_latitude":distance_latitude, 		\
		"distance_longitude":distance_longitude, 		\
		"xGridCount":xGridCnt, 			\
		"yGridCount":yGridCnt, 			\
		"pointCnt":len(data)				\
	}
	#for line in data: # dicts indexing for debug
	#	gridDicts.setdefault((int(line[-2]), int(line[-1])), [])
	#	gridDicts[(int(line[-2]), int(line[-1]))].append(line[:-2])
	#assert(min([key[0] for key in gridDicts.keys() if type(key) == tuple]) >= 0 and max([key[0] for key in gridDicts.keys() if type(key) == tuple]) < xGridCnt)
	#assert(min([key[1] for key in gridDicts.keys() if type(key) == tuple]) >= 0 and max([key[1] for key in gridDicts.keys() if type(key) == tuple]) < yGridCnt)
	
	# handle saving data
	try:
		if gridNumpyFp:
			save(gridNumpyFp, data)
			print("The numpy array has been dumped to \"{0}\". ".format(gridNumpyFp))
		if gridDictionaryFp:
			with open(gridDictionaryFp, "w", encoding = encoding) as f:
				f.write("\n".join(["{0}\t{1}".format(key, value) for key, value in gridDicts.items()]))
				#f.write(str(gridDicts)) # for debug
			print("The grid dictionary has been dumped to \"{0}\". ".format(gridDictionaryFp))
		try:
			if not os.path.isfile(gridScatterFilepath): # do not generate while existing
				drawData(data, dpi = dpi, filepath = gridScatterFilepath)
				print("A figure has been dumped to \"{0}\". This is an extension function. ".format(gridScatterFilepath))
		except: # just an extension function
			pass
		return data, gridDicts
	except Exception as e:
		print(e)
		return None, None

def handleInputData(xGridCount = 100, yGridCount = 100) -> tuple:
	gridNumpyFilepath = gridNumpyFilepathFormat.format(xGridCount, yGridCount)
	gridDictionaryFilepath = gridDictionaryFilepathFormat.format(xGridCount, yGridCount)
	if os.path.isfile(gridNumpyFilepath) and os.path.isfile(gridDictionaryFilepath): # if built before
		try:
			data = load(gridNumpyFilepath)
			print("The numpy data are loaded successfully. ")
			with open(gridDictionaryFilepath, "r", encoding = "utf-8") as f:
				gridDicts = {line.split("\t")[0]:float(line.split("\t")[1]) for line in f.read().split("\n")} # considering the security issues, eval(f.read()) is forbidden
				gridDicts["xGridCount"] = int(gridDicts["xGridCount"])
				gridDicts["yGridCount"] = int(gridDicts["yGridCount"])
				gridDicts["pointCnt"] = int(gridDicts["pointCnt"])
				#gridDicts = eval(f.read()) # for debug
			print("The grid dictionary is loaded successfully. ")
		except Exception as e:
			data, gridDicts = None, None
			print(e)
	else: # if no grid file was built before
		data, gridDicts = buildGrid(xGridCount, yGridCount, gridNumpyFp = gridNumpyFilepath, gridDictionaryFp = gridDictionaryFilepath)
	if data is None or gridDicts is None:
		print("Error building or indexing grids, please press any key to exit. ")
		press_any_key_to_continue()
		return False, None, None
	else:
		return True, data, gridDicts


def getCellFromLocation(location, gridDicts) -> tuple:
	assert(gridDicts["min_latitude"] <= location[0] <= gridDicts["max_latitude"] and gridDicts["min_longitude"] <= location[1] <= gridDicts["max_longitude"])
	return (																\
		gridDicts["xGridCount"] - 1 if location[0] == gridDicts["max_latitude"] else int((location[0] - gridDicts["min_latitude"]) // gridDicts["distance_latitude"]), 		\
		gridDicts["yGridCount"] - 1 if location[1] == gridDicts["max_longitude"] else int((location[1] - gridDicts["min_longitude"])  // gridDicts["distance_longitude"])		\
	)

def getLocationsFromCell(cell, gridDicts) -> dict:
	return {										\
		"up":cell[0] * gridDicts["distance_latitude"] + gridDicts["min_latitude"], 			\
		"down":(cell[0] + 1) * gridDicts["distance_latitude"] + gridDicts["min_latitude"], 		\
		"left":cell[1] * gridDicts["distance_longitude"] + gridDicts["min_longitude"], 		\
		"right":(cell[1] + 1) * gridDicts["distance_longitude"] + gridDicts["min_longitude"]		\
	}

def linearSearch(data, gridDicts, q, k, numpyGrade = 2, isPrint = False) -> array:
	#assert(1 <= k <= gridDicts["pointCnt"] and numpyGrade in (0, 1, 2, 3)) # for debug
	kNNSet = KNNSet(q, k)
	if 3 == numpyGrade: # whole grid
		kNNSet.lists = c_[data[:, :3], ((data[:, 0] - q[0]) ** 2 + (data[:, 1] - q[1]) ** 2) ** (1 / 2)]
		kNNSet.lists = kNNSet.lists[argsort(kNNSet.lists[:, 3])][:k, :]
	elif 2 == numpyGrade: # per depth
		depth = 0
		idx = getCellFromLocation(q, gridDicts)
		if idx[0] in data[:, 3] and idx[1] in data[:, 4]:
			gridList = data[where((data[:, 3] == idx[0]) & (data[:, 4] == idx[1]))]
			kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
		max_depth = max(idx[0], gridDicts["xGridCount"] - idx[0], idx[1], gridDicts["yGridCount"] - idx[1])
		while depth < max_depth:
			depth += 1
			if depth not in global_offsets: # to speed up
				global_offsets[depth] = array([(-depth, j) for j in range(-depth, depth)] + [(i, depth) for i in range(-depth, depth)] + [(depth, j) for j in range(depth, -depth, -1)] + [(i, -depth) for i in range(depth, -depth, -1)], dtype = "int")
			offsets = global_offsets[depth] + idx
			offsets = offsets[where((0 <= offsets[:, 0] ) & (offsets[:, 0] < gridDicts["xGridCount"]) & (0 <= offsets[:, 1]) & (offsets[:, 1] < gridDicts["yGridCount"]))]
			#gridList = data[np_any(np_all(data[:, None, 3:] == offsets, axis = 2), axis = 1)]
			compressedOffsets = offsets[:, 0] * gridDicts["yGridCount"] + offsets[:, 1]
			mask = in1d(data[:, 3] * gridDicts["yGridCount"] + data[:, 4], compressedOffsets)
			gridList = data[mask]
			kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
	elif 1 == numpyGrade: # per cell
		for i in range(gridDicts["xGridCount"]):
			for j in range(gridDicts["yGridCount"]):
				gridList = data[where((data[:, 3] == i) & (data[:, 4] == j))]
				kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
	elif 0 == numpyGrade: # per point
		for i in range(gridDicts["xGridCount"]):
			for j in range(gridDicts["yGridCount"]):
				gridList = data[where((data[:, 3] == i) & (data[:, 4] == j))]
				for line in gridList.tolist():
					kNNSet.update(array(line[:3] + [((line[0] - q[0]) ** 2 + (line[1] - q[1]) ** 2) ** (1 / 2)], dtype = "float64").reshape(1, 4))
	if isPrint:
		print(kNNSet.lists)
	return kNNSet.lists

def searchKNNSet(data, gridDicts, q, k, numpyGrade = 2, isPrint = False) -> array:
	#assert(1 <= k <= gridDicts["pointCnt"] and numpyGrade in (0, 1, 2, 3)) # for debug
	kNNSet = KNNSet(q, k)
	idx = getCellFromLocation(q, gridDicts)
	if isPrint: # turn off or comment it if the program is tested for time
		print("The location q ({0}, {1}) is in the No. {2} block. ".format(q[0], q[1], idx))
	
	if numpyGrade == 3:
		data_with_distance = c_[data[:, :3], ((data[:, 0] - q[0]) ** 2 + (data[:, 1] - q[1]) ** 2) ** (1 / 2)]
	accessed_cell = 1
	if idx[0] in data[:, 3] and idx[1] in data[:, 4]:
		gridList = data[where((data[:, 3] == idx[0]) & (data[:, 4] == idx[1]))]
		kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
		scanned_cell = 1 # the original one
	else:
		scanned_cell = 0
	
	depth = 0
	max_depth = max(idx[0], gridDicts["xGridCount"] - idx[0], idx[1], gridDicts["yGridCount"] - idx[1])
	while depth < max_depth:
		depth += 1
		if depth not in global_offsets: # to speed up
			global_offsets[depth] = array([(-depth, j) for j in range(-depth, depth)] + [(i, depth) for i in range(-depth, depth)] + [(depth, j) for j in range(depth, -depth, -1)] + [(i, -depth) for i in range(depth, -depth, -1)], dtype = "int")
		offsets = global_offsets[depth] + idx
		offsets = offsets[where((0 <= offsets[:, 0] ) & (offsets[:, 0] < gridDicts["xGridCount"]) & (0 <= offsets[:, 1]) & (offsets[:, 1] < gridDicts["yGridCount"]))]
		#print(global_offsets[depth], idx, offsets, sep = "\n") # for debug
		#press_any_key_to_continue() # for debug

		if 3 == numpyGrade: # whole grid
			#gridList = data[np_any(np_all(data[:, None, 3:] == offsets, axis = 2), axis = 1)]
			compressedOffsets = offsets[:, 0] * gridDicts["yGridCount"] + offsets[:, 1]
			mask = in1d(data[:, 3] * gridDicts["yGridCount"] + data[:, 4], compressedOffsets)
			toUpdate = data_with_distance[mask]
			if kNNSet.t is not None and len(toUpdate) and min(toUpdate[:, 3]) >= kNNSet.t:
				break
			else:
				kNNSet.update(toUpdate)
		elif 2 == numpyGrade: # per depth
			#gridList = data[np_any(np_all(data[:, None, 3:] == offsets, axis = 2), axis = 1)]
			compressedOffsets = offsets[:, 0] * gridDicts["yGridCount"] + offsets[:, 1]
			mask = in1d(data[:, 3] * gridDicts["yGridCount"] + data[:, 4], compressedOffsets)
			gridList = data[mask]
			toUpdate = c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)]
			if kNNSet.t is not None and len(toUpdate) and min(toUpdate[:, 3]) >= kNNSet.t:
				break
			else:
				kNNSet.update(toUpdate)
		elif 1 == numpyGrade: # per cell
			flags = []
			for cell in offsets:
				loc = getLocationsFromCell(cell, gridDicts)
				#print(loc) # for debug
				if kNNSet.t is None: # not enough
					flags.append(True) # cannot be pruned
					accessed_cell += 1
					if cell[0] in data[:, 3] and cell[1] in data[:, 4]: # add no matter how large it is since no adequate items in the list
						scanned_cell += 1
						gridList = data[where((data[:, 3] == cell[0]) & (data[:, 4] == cell[1]))]
						kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
				else: # require update
					dx = 0 if loc["left"] <= q[1] <= loc["right"] else min(abs(loc["left"] - q[1]), abs(loc["right"] - q[1]))
					dy = 0 if loc["up"] <= q[0] <= loc["down"] else min(abs(loc["up"] - q[0]), abs(loc["down"] - q[0]))
					d = (dx ** 2 + dy ** 2) ** (1 / 2)
					#print("depth = {0}, len(kNNSet.lists) = {1}, k = {2}, d = {3}, t = {4}. ".format(depth, len(kNNSet.lists), k, d, kNNSet.t)) # for debug
					#press_any_key_to_continue()
					if d >= kNNSet.t: # no nearer points in the cell since the distance to cell is not smaller than t
						flags.append(False) # ignore the cell
					else: # prune
						flags.append(True) # this layer cannot be pruned
						accessed_cell += 1
						if cell[0] in data[:, 3] and cell[1] in data[:, 4]:
							scanned_cell += 1
							gridList = data[where((data[:, 3] == cell[0]) & (data[:, 4] == cell[1]))]
							kNNSet.update(c_[gridList[:, :3], ((gridList[:, 0] - q[0]) ** 2 + (gridList[:, 1] - q[1]) ** 2) ** (1 / 2)])
			#print(depth, len(offsets), flags) # for debug
			#press_any_key_to_continue()
			if not any(flags): # Finished
				break
		elif 0 == numpyGrade: # per point
			flags = []
			for cell in offsets:
				loc = getLocationsFromCell(cell, gridDicts)
				#print(loc) # for debug
				if kNNSet.t is None: # not enough
					flags.append(True) # cannot be pruned
					accessed_cell += 1
					if cell[0] in data[:, 3] and cell[1] in data[:, 4]: # add no matter how large it is since no adequate items in the list
						scanned_cell += 1
						gridList = data[where((data[:, 3] == cell[0]) & (data[:, 4] == cell[1]))]
						for line in gridList.tolist():
							kNNSet.update(array(line[:3] + [((line[0] - q[0]) ** 2 + (line[1] - q[1]) ** 2) ** (1 / 2)], dtype = "float64").reshape(1, 4))
				else: # require update
					dx = 0 if loc["left"] <= q[1] <= loc["right"] else min(abs(loc["left"] - q[1]), abs(loc["right"] - q[1]))
					dy = 0 if loc["up"] <= q[0] <= loc["down"] else min(abs(loc["up"] - q[0]), abs(loc["down"] - q[0]))
					d = (dx ** 2 + dy ** 2) ** (1 / 2)
					#print("depth = {0}, len(kNNSet.lists) = {1}, k = {2}, d = {3}, t = {4}. ".format(depth, len(kNNSet.lists), k, d, kNNSet.t)) # for debug
					#press_any_key_to_continue()
					if d >= kNNSet.t: # no nearer points in the cell since the distance to cell is not smaller than t
						flags.append(False) # ignore the cell
					else: # prune
						flags.append(True) # this layer cannot be pruned
						accessed_cell += 1
						if cell[0] in data[:, 3] and cell[1] in data[:, 4]:
							scanned_cell += 1
							gridList = data[where((data[:, 3] == cell[0]) & (data[:, 4] == cell[1]))]
							for line in gridList.tolist():
								kNNSet.update(array(line[:3] + [((line[0] - q[0]) ** 2 + (line[1] - q[1]) ** 2) ** (1 / 2)], dtype = "float64").reshape(1, 4))
			#print(depth, len(offsets), flags) # for debug
			#press_any_key_to_continue()
			if not any(flags): # Finished
				break

	global global_depth, global_accessed_cell, global_scanned_cell
	global_depth += depth
	global_accessed_cell += accessed_cell
	global_scanned_cell += scanned_cell
	if isPrint:
		print("The depth is finished at {0} with {1} cell(s) accessed and {2} cell(s) scanned. The list is as follows. \n{3}\n".format(depth, accessed_cell, scanned_cell, kNNSet.lists))
	return kNNSet.lists

def doKNNSearch(data, gridDicts, qs, ks, useMethod = 0, numpyGrade = 2, outputFilepath = None, isPrint = False) -> None:
	#assert(g in (50, 100, 200) and useMethod in (0, 1, 2) and numpyGrade in (0, 1, 2, 3)) # for debug
	global global_depth, global_accessed_cell, global_scanned_cell
	global_depth = 0
	global_accessed_cell = 0
	global_scanned_cell = 0
	
	print("Seeds q and k generated, there is/are {0} datum/data in total. ".format(len(qs)))
	length = len(qs)
	if outputFilepath:
		try:
			with open(outputFilepath, "w", encoding = "utf-8") as f:
				f.write(str(gridDicts) + "\n")
		except Exception as e:
			print(e)
			return
	
	time_cost = 0
	if useMethod != 2:
		print("\nStart to test linear scanning. ")
		for q, k in (tqdm(zip(qs, ks), total = length, ncols = 80) if isTqdmAvailable else zip(qs, ks)):
			start_time = time()
			kNNResult = linearSearch(data, gridDicts, q, k, numpyGrade = numpyGrade, isPrint = False)
			end_time = time()
			time_cost += (end_time - start_time) * 1000
			if outputFilepath:
				try:
					with open(outputFilepath, "at", encoding = "utf-8") as f:
						f.write("\nq  = {0}, k = {1}, grid = {2} * {3}, method = 1, numpy = {4}\n".format(q, k, gridDicts["xGridCount"], gridDicts["yGridCount"], numpyGrade))
						savetxt(f, kNNResult, fmt = "%f", newline = "\n")
				except Exception as e:
					print(e)
					return
		print("Linear KNN searching performed, the average time cost is {0}ms / {1} = {2}ms. ".format(time_cost, length, time_cost / length))
	
	time_cost = 0
	if useMethod != 1:
		print("\nStart to test KNN searching with griding. ")
		for q, k in (tqdm(zip(qs, ks), total = length, ncols = 80) if isTqdmAvailable else zip(qs, ks)):
			start_time = time()
			kNNResult = searchKNNSet(data, gridDicts, q, k, numpyGrade = numpyGrade, isPrint = False)
			end_time = time()
			time_cost += (end_time - start_time) * 1000
			if outputFilepath:
				try:
					with open(outputFilepath, "at", encoding = "utf-8") as f:
						f.write("\nq  = {0}, k = {1}, grid = {2} * {3}, method = 1, numpy = {4}\n".format(q, k, gridDicts["xGridCount"], gridDicts["yGridCount"], numpyGrade))
						savetxt(f, kNNResult, fmt = "%f", newline = "\n")
				except Exception as e:
					print(e)
					return
		print("KNN searching with griding performed, the average time cost is {0}ms / {1} = {2}ms. ".format(time_cost, length, time_cost / length))
		print("The average depth is {0} / {1} = {2}. ".format(global_depth, length, global_depth / length))
		print("The average count of accessed grid cells is {0} / {1} = {2}. ".format(global_accessed_cell, length, global_accessed_cell / length))
		print("The average count of scanned grid cells is {0} / {1} = {2}. ".format(global_scanned_cell, length, global_scanned_cell / length))


def printHelp() -> None:
	print("Python script for finding the top k nearest neighbors of q. ", end = "\n\n")
	print("Option: ")
	print("\t[/q|-q|q]: Specify that the following two options are the latitude and longitude of q. ")
	print("\t[/k|-k|k]: Specify that the following option is the value of k. ")
	print("\t[/g|-g|g]: Specify that the following option is the grid among 50, 100 (default), and 200. ")
	print("\t[/useMethod|--useMethod]: Specify that the following option is the method ID among 0 (default), 1, and 2. ")
	print("\t[/numpyGrade|--numpyGrade]: Specify that the following option is the numpy grade in 0, 1, 2 (default), and 3. ")
	print("\t[/i|-i]: Specify that the following option is the input filepath with qx, qy, and k split by \'\\t\' per line. ")
	print("\t[/o|-o]: Specify that the following option is the output filepath. ")
	print("\t[/d|-d|/debug|--debug]: Include this option to turn on debug mode. ", end = "\n\n")
	print("Format: ")
	print("\tpython sol.py [q|-q|/q] qx qy [/k|-k|k] k ...")
	print("\tpython sol.py --input inputFilepath ...", end = "\n\n")
	print("Example: ")
	print("\tpython sol.py -q 42.21245899 -104.81922482 -k 200")
	print("\tpython sol.py -q 42.21245899 -104.81922482 -k 200 -g 50 --input \"input.txt\" --debug")
	print("\tpython sol.py -q 42.21245899 -104.81922482 -k 200 --useMethod 0 --numpyGrade 2 --output \"output.txt\"", end = "\n\n")
	print("Note 1: You must specify at least {q and k} or {input filepath}. Other options are optional. ")
	print("Note 2: Repeated options are subject to the last one. ", end = "\n\n")

def parseCommandline(argv):
	if len(argv) < 2:
		return None
	for arg in argv[1:]:
		if arg.lower() in ("/h", "-h", "h", "/help", "--help", "help", "/?", "-?", "?"):
			printHelp()
			return True
	commandlineDict = {}
	i = 1
	while i < len(argv):
		if argv[i].lower() in ("/q", "-q", "q"):
			try:
				commandlineDict["q"] = (float(argv[i + 1]), float(argv[i + 2]))
				i += 3 # skip 2 commandline options
			except:
				print("Failed getting the coordinate of q, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/k", "-k", "k"):
			try:
				commandlineDict["k"] = int(argv[i + 1])
				#assert(1 <= commandlineDict["k"] <= gridDicts["pointCnt"])
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting the valid value of k, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/g", "-g", "g"):
			try:
				commandlineDict["g"] = int(argv[i + 1])
				assert(commandlineDict["g"] in (50, 100, 200))
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting the valid value of k, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/usemethod", "--usemethod"):
			try:
				commandlineDict["m"] = int(argv[i + 1])
				assert(commandlineDict["m"] in (0, 1, 2))
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting methods, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/numpygrade", "--numpygrade"):
			try:
				commandlineDict["n"] = int(argv[i + 1])
				assert(commandlineDict["n"] in (0, 1, 2, 3))
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting the numpy grade, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/input", "--input"):
			try:
				commandlineDict["i"] = argv[i + 1]
				assert(os.path.isfile(commandlineDict["i"]))
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting or detecting input filepath, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/output", "--output"):
			try:
				commandlineDict["o"] = argv[i + 1]
				assert(commandlineDict["o"] != sourceFilepath and not commandlineDict["o"].startswith(gridNumpyFilepathFormat.split("_")[0]) and not commandlineDict["o"].startswith(gridDictionaryFilepathFormat.split("_")[0]))
				i += 2 # skip 1 commandline options
			except:
				print("Failed getting output filepath or conflicts existing, please check your commandline. ")
				return False
		elif argv[i].lower() in ("/d", "-d", "/debug", "--debug"):
			commandlineDict["d"] = True
			i += 1 # move to the next commandline option
		else:
			print("Unrecognized commandline option: argv[{0}]. ".format(i))
			return False
	if "q" in commandlineDict and "k" in commandlineDict or "i" in commandlineDict:
		return commandlineDict
	else:
		print("No {q and k} or {input filepath} given, please check your commandline. ")
		return False



def main() -> int:
	# Handle commandline option #
	# python sol.py -q 42.21245899 -104.81922482 -k 200 -g 100 --useMethod 0 --numpyGrade 2 --input "input.txt" --output "output.txt"
	commandlineDict = parseCommandline(argv)
	if commandlineDict == False:
		print("Illegal commandline detected, please check your commandline. ")
		return EOF
	elif commandlineDict == True:
		return EXIT_SUCCESS
	elif type(commandlineDict) == dict:
		g = commandlineDict["g"] if "g" in commandlineDict else 100
		status, data, gridDicts = handleInputData(xGridCount = g, yGridCount = g)
		if not status:
			return EXIT_FAILURE
		qs = []
		ks = []
		if "i" in commandlineDict:
			content = getTxt(commandlineDict["i"])
			if not content:
				print("Error reading input file or empty input file detected, please check your commandline. ")
				return EXIT_FAILURE
			try: # The qs list excludes comment symbols
				qs += [(float(line.split("\t")[0]), float(line.split("\t")[1])) for line in content.split("\n")		\
					if not line.startswith("#") and not line.startswith("%") and not line.startswith("//") and not line.startswith(";") and line.count("\t") == 2]
				ks += [int(line.split("\t")[2]) for line in content.split("\n") if not line.startswith("#") and not line.startswith("%") and not line.startswith("//") and not line.startswith(";") and line.count("\t") == 2]
			except:
				print("Error recognizing input file, please check your commandline. ")
				return EXIT_FAILURE
		if "q" in commandlineDict and "k" in commandlineDict:
			qs.append(commandlineDict["q"])
			ks.append(commandlineDict["k"])
		if len(qs) == 0 or len(ks) == 0:
			print("Input data empty, please check your commandline. ")
			return EXIT_FAILURE
		if len(qs) != len(ks):
			print("Lengths of input data unmatched, please check your commandline. ")
			return EXIT_FAILURE
		doKNNSearch(									\
			data, 									\
			gridDicts, 									\
			qs, 									\
			ks, 									\
			useMethod = commandlineDict["m"] if "m" in commandlineDict else 0, 			\
			numpyGrade = commandlineDict["n"] if "n" in commandlineDict else 2, 			\
			outputFilepath = commandlineDict["o"] if "o" in commandlineDict else None, 		\
			isPrint = "d" in commandlineDict and commandlineDict["d"]				\
		)
		return EXIT_SUCCESS
	
	# Handle grid indexing #
	try:
		g = int(input("Input grid count for indexing (50, 100 (default), 200): "))
		assert(g in (50, 100, 200))
	except:
		print("Wrong grid input detected, the grid count is reset to 100. ")
		g = 100
	status, data, gridDicts = handleInputData(xGridCount = g, yGridCount = g)
	if not status:
		return EXIT_FAILURE
		
	# Handle KNN Searching #
	#print(getCellFromLocation((-86, -172), gridDicts)) # for debug
	#print(getLocationsFromCell(9999, gridDicts)) # for debug
	#linearSearch(data, gridDicts, (42.21245899, -104.81922482), 200, isPrint = True) # for debug
	#searchKNNSet(data, gridDicts, (42.21245899, -104.81922482), 200, isPrint = True) # for debug
	#press_any_key_to_continue() # for  debug
	
	qs = [(uniform(gridDicts["min_latitude"], gridDicts["max_latitude"]), uniform(gridDicts["min_longitude"], gridDicts["max_longitude"])) for _ in range(N)]
	ks = [randint(1, gridDicts["pointCnt"] if maxK is None else maxK) for _ in range(N)]
	try:
		numpyGrade = int(input("Input numpy grade for testing (0, 1, 2 (default), or 3): "))
		assert(numpyGrade in (0, 1, 2, 3))
	except:
		print("Wrong numpy grade input detected, the numpy grade is reset to 2. ")
		numpyGrade = 2
	doKNNSearch(data, gridDicts, qs, ks, useMethod = 0, numpyGrade = numpyGrade, isPrint = False)
	print("\nPlease press any key to exit. ")
	press_any_key_to_continue()
	return EXIT_SUCCESS





if __name__ == "__main__":
	exit(main())