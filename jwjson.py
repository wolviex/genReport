import json
import re

#Quick wrapper for JSON to parse out comments starting with #

commentjson = re.compile(r"\".*?\"|'.*?'|(#.*?)\n")


def loadJSON(jsonText):
	
	found = commentjson.findall(jsonText)

	for s in found:
		if s == "":
			continue
		else:
			jsonText = jsonText.replace(s, "")

	return json.loads(jsonText)






