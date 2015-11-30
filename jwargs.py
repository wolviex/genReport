import sys
import inspect
import __main__

def printLine():
	try:
		rows, columns = os.popen('stty size', 'r').read().split()
		print("-" * int(columns))
	except Exception as e:
		print("------------------------------")

def getArgs():
	skipCount = 0
	if len(sys.argv) == 1:
		argList = []
		funcList = dir(__main__)
		for func in funcList:
			if len(func) > 2:
				if func[:2] == "m_":
					argList.append(func)
		print "Usage:"
		
		for a in argList:

			argFunc = getattr(__main__,a)
			print "-{} {}".format(a[2:]," ".join(inspect.getargspec(argFunc).args))
			if inspect.getcomments(argFunc) is not None:
				print inspect.getcomments(argFunc)
			
		sys.exit(0)
	for i in range(1,len(sys.argv)):
		if skipCount > 0:
			skipCount -= 1
			continue
	
		if sys.argv[i][0] != "-":
			getattr(__main__,"default")(sys.argv[i])
			#localFuncs.get("default")
			continue
		arg = getattr(__main__,"m_{}".format(sys.argv[i][1:]))  #localFuncs.get("m_{}".format(sys.argv[i][1:]))
		if arg is not None:
			argCount = len(inspect.getargspec(arg).args)
			argList = [sys.argv[i + x] for x in range(1,argCount+1)]
			arg(*argList)
			skipCount = argCount