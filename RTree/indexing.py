import os
from sys import argv, exit
from queue import Queue
from time import sleep
try:
	from numpy import array
	from matplotlib import pyplot as plt
	def plotCoords(coords:list, dpi:int = 1200, plotFp:str = None) -> None:
		coords_array = array(coords)
		plt.rcParams["font.family"] = "Times New Roman"
		plt.rcParams["figure.dpi"] = 300
		plt.rcParams["savefig.dpi"] = 300
		plt.scatter(coords_array[:, 0], coords_array[:, 1], marker = ".", color = "orange")
		plt.rcParams["figure.dpi"] = dpi
		plt.rcParams["savefig.dpi"] = dpi
		try:
			if plotFp is None:
				plt.show()
			else:
				plt.savefig(plotFp, bbox_inches = "tight")
				print("Extra Features: Successfully saved the plot of the coords to \"{0}\". ".format(plotFp))
		except KeyboardInterrupt:
			print("Ploting procedures are interrupted by users. ")
		except BaseException as e:
			print("Exceptions occurred. Details are as follows. \n{0}".format(e))
		plt.close()
	def plotFundamentalMBRs(MBRs:list, dpi:int = 1200, plotFp:str = None) -> None:
		plt.rcParams["font.family"] = "Times New Roman"
		plt.rcParams["figure.dpi"] = 300
		plt.rcParams["savefig.dpi"] = 300
		fig, ax = plt.subplots()
		for mbr in MBRs:
			x_low, x_high, y_low, y_high = mbr
			rect = plt.Rectangle((x_low, y_low), x_high - x_low, y_high - y_low, facecolor = "none", edgecolor = "blue", linewidth = 0.2)
			ax.add_patch(rect)
		ax.autoscale()
		ax.set_aspect("equal", "box")
		plt.rcParams["figure.dpi"] = dpi
		plt.rcParams["savefig.dpi"] = dpi
		try:
			if plotFp is None:
				plt.show()
			else:
				plt.savefig(plotFp, bbox_inches = "tight")
				print("Extra Features: Successfully saved the plot of the fundamental MBRs to \"{0}\". ".format(plotFp))
		except KeyboardInterrupt:
			print("Ploting procedures are interrupted by users. ")
		except BaseException as e:
			print("Exceptions occurred. Details are as follows. \n{0}".format(e))
		plt.close()
	def plotMBRs(MBRs:list, dpi:int = 1200, plotFp:str = None) -> None:
		colors = ["red", "orange", "green", "blue", "black"]
		plt.rcParams["font.family"] = "Times New Roman"
		plt.rcParams["figure.dpi"] = dpi
		plt.rcParams["savefig.dpi"] = dpi
		fig, ax = plt.subplots()
		max_layer = max([mbr[1] for mbr in MBRs])
		for mbr in MBRs:
			x_low, x_high, y_low, y_high = mbr[0]
			rect = plt.Rectangle((x_low, y_low), x_high - x_low, y_high - y_low, facecolor = "none", edgecolor = colors[mbr[1] % len(colors)], linewidth = (max_layer - mbr[1] + 1) / 5, alpha = 1 - mbr[1] / 10)
			ax.add_patch(rect)
		ax.autoscale()
		ax.set_aspect("equal", "box")
		try:
			if plotFp is None:
				plt.show()
			else:
				plt.savefig(plotFp, bbox_inches = "tight")
				print("Extra Features: Successfully saved the plot of the MBRs to \"{0}\". ".format(plotFp))
		except KeyboardInterrupt:
			print("Ploting procedures are interrupted by users. ")
		except BaseException as e:
			print("Exceptions occurred. Details are as follows. \n{0}".format(e))
		plt.close()
except:
	def plotCoords(coords:list, dpi:int = 1200, plotFp:str = None) -> None:
		return None
	def plotFundamentalMBRs(MBRs:list, dpi:int = 1200, plotFp:str = None) -> None:
		return None
	def plotMBRs(MBRs:list, dpi:int = 1200, plotFp:str = None) -> None:
		return None
try:
	os.chdir(os.path.abspath(os.path.dirname(__file__))) # cd into the location path of this script
except: # it does not work in Jupyter-notebook
	pass
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
_DIVISORS = [180.0 / 2 ** n for n in range(32)]
INDICATOR = 0 # 10000 # change the indicator to 10000 if you wish to make it visualized in a better way
lowerBound = 0
defaultTime = 5
coordsFilepath = "coords.txt"
offsetsFilepath = "offsets.txt"
rTreeFilepath = "Rtree.txt"
plotCoordFilepath = "plotCoord.pdf"
plotFundamentalMBRFilepath = "plotFundamentalMBR.pdf"
plotMBRFilepath = "plotMBR.pdf"


# class #
class RTreeNode:
	def __init__(self:object, entries:list = [], identifier:int = 0, MBR:list = None):
		self.entries = entries
		self.identifier = identifier
		self.MBR = MBR
	def __str__(self) -> str:
		if isinstance(self.entries[0], RTreeNode):
			return str([1, self.identifier, [[entry.identifier, entry.MBR] for entry in self.entries]])
		else:
			return str([0, self.identifier, self.entries])


# get input #
def getTxt(filepath:str, index:int = 0) -> str: # get .txt content
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

def getCoords(coordsFp:str = coordsFilepath) -> list:
	content = getTxt(coordsFp)
	if content is None:
		return None
	content = content.replace("\r", "\n") # filtering "\r"
	while "\n\n" in content: # filtering empty lines
		content = content.replace("\n\n", "\n")
	coords = []
	for cnt, line in enumerate(content.split("\n")):
		if line.count(",") == 1:
			tmp = line.split(",")
			try:
				coords.append([float(tmp[0]), float(tmp[1])])
			except:
				print("Line {0} has been skipped since converting errors occured. ".format(cnt))
		elif line: # it is not necessary to prompt the empty line
			print("Line {0} has been skipped since the count of comma(s) is not 1. ".format(cnt))
	return coords

def getOffsets(offsetsFp:str = offsetsFilepath) -> list:
	content = getTxt(offsetsFp)
	if content is None:
		return None
	content = content.replace("\r", "\n") # filtering "\r"
	while "\n\n" in content: # filtering empty lines
		content = content.replace("\n\n", "\n")
	offsets = []
	for cnt, line in enumerate(content.split("\n")):
		if line.count(",") == 2:
			tmp = line.split(",")
			try:
				offsets.append([int(tmp[0]), int(tmp[1]), int(tmp[2])])
			except:
				print("Line {0} has been skipped since converting error occured. ".format(cnt))
		elif line: # it is not necessary to prompt the empty line
			print("Line {0} has been skipped since the count of comma(s) is not 2. ".format(cnt))
	return offsets

def checkOffsetCoords(coords:list, offsets:list) -> bool:
	if offsets:
		for i in range(len(offsets) - 1):
			if offsets[i + 1][1] - offsets[i][2] != 1:
				print("Uncovered coords are detected: From {0} to {1}. ".format(offsets[i][2], offsets[i + 1][1]))
				return False
	else:
		return False
	if offsets[0][1] != 0:
		print("The offsets do not cover the coords as offsets begin at {0} while coords begin at 0. ".format(offsets[0][1]))
		return False
	if offsets[-1][-1] != len(coords) - 1:
		print("The offsets do not cover the coords as offsets end at {0} while coords end at {1}. ".format(offsets[-1][-1], len(coords) - 1))
		return False
	return True

def getFundamentalMBR(rTree:RTreeNode|list, fMBRs:list) -> list:
	if isinstance(rTree, RTreeNode):
		for entry in rTree.entries:
			getFundamentalMBR(entry, fMBRs)
	else:
		fMBRs.append(rTree[1])

def getMBR(rTree:RTreeNode|list, MBRs:list, layer:int = 0) -> list:
	if isinstance(rTree, RTreeNode):
		MBRs.append((rTree.MBR, layer))
		for entry in rTree.entries:
			getMBR(entry, MBRs, layer + 1)
	else:
		MBRs.append((rTree[1], layer))


# handle indexing #
def compute_mbr(coords:list) -> list: # find the bounds
	if coords:
		x_low = min(coords, key = lambda c:c[0])[0]
		x_high = max(coords, key = lambda c:c[0])[0]
		y_low = min(coords, key = lambda c:c[1])[1]
		y_high = max(coords, key = lambda c:c[1])[1]
		return [x_low, x_high, y_low, y_high]
	else:
		return None

def interleave_latlng(lat:float, lng:float) -> str: # get code
	if not isinstance(lat, float) or not isinstance(lng, float):
		return None
	if lng > 180:
		x = (lng % 180) + 180.0
	elif lng < -180:
		x = (-((-lng) % 180)) + 180.0
	else:
		x = lng + 180.0
	if lat > 90:
		y = (lat % 90) + 90.0
	elif lat < -90:
		y = (-((-lat) % 90)) + 90.0
	else:
		y = lat + 90.0
	
	morton_code = ""
	for dx in _DIVISORS:
		digit = 0
		if y >= dx:
			digit |= 2
			y -= dx
		if x >= dx:
			digit |= 1
			x -= dx
		morton_code += str(digit)
	
	return morton_code

def allocateId(idToBeAllocated:int) -> int:
	global lowerBound
	if idToBeAllocated >= lowerBound:
		lowerBound = idToBeAllocated + 1
		return idToBeAllocated
	else:
		lowerBound += 1
		return lowerBound - 1

def buildRTree(entries:list, min_capacity:int = 8, max_capacity:int = 20, level:int = 0, level_indicator:int = INDICATOR, isPrint:bool = False) -> RTreeNode:
	if isPrint:
		print("{0} node{1} at level {2}".format(len(entries), ("s" if len(entries) > 1 else ""), level - 1))
	if len(entries) <= max_capacity:
		print("1 node at level {0}".format(level)) # last level
		return RTreeNode(entries = entries, identifier = allocateId(level * level_indicator)) # root
	else:
		return buildRTree(																		\
			entries = [RTreeNode(entries = entries[i * max_capacity:(i + 1) * max_capacity], identifier = allocateId(i + level * level_indicator)) for i in range((len(entries) - 1) // max_capacity + 1)], 	\
			min_capacity = min_capacity, 																\
			max_capacity = max_capacity, 																\
			level = level + 1, 																	\
			level_indicator = level_indicator, 															\
			isPrint = True																	\
		)

def computeNodeMBR(nodes:list) -> list: # find the bounds
	if nodes:
		x_low = min(nodes, key = lambda c:c[0])[0]
		x_high = max(nodes, key = lambda c:c[1])[1]
		y_low = min(nodes, key = lambda c:c[2])[2]
		y_high = max(nodes, key = lambda c:c[3])[3]
		return [x_low, x_high, y_low, y_high]
	else:
		return None

def computeRTreeMBR(rTree:RTreeNode) -> None:
	if isinstance(rTree.entries[0], RTreeNode):
		for entry in rTree.entries:
			if entry.MBR is None:
				computeRTreeMBR(entry)
		rTree.MBR = computeNodeMBR([entry.MBR for entry in rTree.entries])
	else:
		rTree.MBR = computeNodeMBR([entry[1] for entry in rTree.entries])

def doBuildRTree(entries:list, min_capacity:int = 8, max_capacity:int = 20, level_indicator:int = INDICATOR) -> RTreeNode:
	if not isinstance(entries, list) or len(entries) < 1:
		return None
	lowerBound = 0
	rTree = buildRTree(entries, min_capacity = min_capacity, max_capacity = max_capacity, level_indicator = level_indicator)
	lastNode = rTree
	while isinstance(lastNode.entries[-1], RTreeNode):
		while len(lastNode.entries[-1].entries) < min_capacity:
			lastNode.entries[-1].entries.insert(0, lastNode.entries[-2].entries.pop())
		lastNode = lastNode.entries[-1]
	computeRTreeMBR(rTree)
	return rTree

def index(coords:list, offsets:list) -> RTreeNode: # build index
	entries = []
	for offset in offsets:
		polygon_id, start_offset, end_offset = offset
		polygon_coords = coords[start_offset:end_offset + 1]
		mbr = compute_mbr(polygon_coords)
		center = [(mbr[0] + mbr[1]) / 2, (mbr[2] + mbr[3]) / 2] # [sum(coord[0] for coord in polygon_coords) / len(polygon_coords), sum(coord[1] for coord in polygon_coords) / len(polygon_coords)] if polygon_coords else None
		if mbr is None or center is None:
			print("Warning: illegal coords[{0}:{1}] are found. ".format(start_offset, end_offset + 1))
		else:
			z_order = interleave_latlng(center[1], center[0])
			entries.append([polygon_id, mbr, z_order])
	entries.sort(key = lambda x:x[-1])
	for i in range(len(entries)): # remove z-order
		entries[i].pop()
	return doBuildRTree(entries)


# make output #
def dumpRTree(rTree:RTreeNode, fp:object = None) -> None:
	for entry in rTree.entries:
		if isinstance(entry, RTreeNode):
			dumpRTree(entry, fp)
	if fp:
		fp.write("{0}\n".format(rTree))
	else:
		print(rTree)

def doDumpRTree(rTree:RTreeNode, layerByLayer:bool = True, filepath:str = rTreeFilepath, encoding:str = "utf-8") -> bool:
	if filepath:
		try:
			with open(filepath, "w", encoding = encoding) as f:
				if layerByLayer:
					q = Queue()
					q.put(rTree) # root
					results = []
					while not q.empty():
						levelSize = q.qsize()
						levelNodes = []
						for i in range(levelSize):
							node = q.get()
							levelNodes.append("{0}\n".format(node))
							if isinstance(node.entries[0], RTreeNode):
								for child in node.entries:
									q.put(child)
						results.insert(0, levelNodes)
					for result in results:
						for r in result:
							f.write(r)
				else:
					dumpRTree(rTree, fp = f)
			return True
		except Exception as e:
			print(e)
			return False
	else:
		dumpRTree(rTree, fp = f)
		return True



# main function #
def preExit(countdownTime:int = defaultTime) -> None: # we use this function before exiting instead of getch since getch is not OS-independent
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
	print("Python script for indexing RTree. ", end = "\n\n")
	print("Option: ")
	print("\t[/coords|--coords|coords]: Specify that the following option is the input coord file. ")
	print("\t[/offsets|--offsets|offsets]: Specify that the following option is the input offset file. ")
	print("\t[/rTree|--rTree|rTree]: Specify that the following option is the output rTree file. ", end = "\n\n")
	print("Format: ")
	print("\tpython indexing.py [/coords|--coords|coords] coordsFilepath [/offsets|--offsets|offsets] offsetsFilepath [/rTree|--rTree|rTree] rTreeFilepath", end = "\n\n")
	print("Example: ")
	print("\tpython indexing.py /coords coords.txt /offsets offsets.txt")
	print("\tpython indexing.py /coords coords.txt /offsets offsets.txt /rTree Rtree.txt", end = "\n\n")

def handleCommandline() -> dict:
	for arg in argv[1:]:
		if arg.lower() in ("/h", "-h", "h", "/help", "--help", "help", "/?", "-?", "?"):
			printHelp()
			return True
	if len(argv) > 1 and len(argv) not in (3, 5, 7):
		print("The count of the commandline options is incorrect. Please check your commandline. ")
		return False
	dicts = {"coords":coordsFilepath, "offsets":offsetsFilepath, "rTree":rTreeFilepath}
	pointer = None
	for arg in argv[1:]:
		if arg.lower() in ("/coords", "--coords", "coords"):
			pointer = "coords"
		elif arg.lower() in ("/offsets", "--offsets", "offsets"):
			pointer = "offsets"
		elif arg.lower() in ("/rtree", "--rtree", "rtree"):
			pointer = "rTree"
		elif pointer is None:
			print("Error handling commandline, please check your commandline. ")
			return False
		else:
			dicts[pointer] = arg
			pointer = None # reset
	return dicts

def main() -> int:
	# get input #
	commandlineArgument = handleCommandline()
	if isinstance(commandlineArgument, bool):
		return EXIT_SUCCESS if commandlineArgument else EXIT_FAILURE
	coords = getCoords(commandlineArgument["coords"])
	if coords is None:
		print("Error reading coords, please check. ")
		preExit()
		return EXIT_FAILURE
	offsets = getOffsets(commandlineArgument["offsets"])
	if offsets is None:
		print("Error reading offsets, please check. ")
		preExit()
		return EXIT_FAILURE
	if not checkOffsetCoords(coords, offsets):
		preExit()
		return EXIT_FAILURE
	plotCoords(coords, plotFp = plotCoordFilepath)
	
	# handle indexing #
	rTree = index(coords, offsets)
	fMBRs = []
	MBRs = []
	getFundamentalMBR(rTree, fMBRs)
	getMBR(rTree, MBRs)
	MBRs.reverse()
	plotFundamentalMBRs(fMBRs, plotFp = plotFundamentalMBRFilepath)
	plotMBRs(MBRs, plotFp = plotMBRFilepath)
	
	# make output #
	doDumpRTree(rTree, filepath = commandlineArgument["rTree"])
	preExit()
	return EXIT_SUCCESS





if __name__ == "__main__":
	exit(main())