var ObjType = {
	_int :      1,
	_float :    2,
	_str :      3,
	_func :     4,
	_element:   5,
	_array:     6
}

function onConnect(ev) {

    document.getElementById("debug").innerHTML = "CONN";

}
var strsend = "v"
function trySend(socket,msg) {

    socket.send(msg);
    msg = msg + "v"
    

}
var connected = Array();
var socket;
var currApp;
var netElems = {};
var callElems = {};



function init2() {

    //currApp = $("#serverBuilder").load("servbuilder.html",getNetworkElements);
    var TEST = {
        FOO: 0,
        BAR: 1
    }

    d = new Array();
    d2 = new Array();
    d2.push("d2");
    d2.push("d3");
    d.push("hello");
    d.push(d2);
    d2.push("gi");

    
}
function sbt() {
    socket.send(new Blob(["hello"]));
}
var timer = 0;
function getNetworkElements() {
    var d = document.getElementsByClassName("networkEnabled");
    for (var i = 0; i < d.length; i++) {
        networkRecursion(d[i]);
    }
    sb_init();
}

function addUpdateListener(name, f) {
    
    if (!callElems[name])
        callElems[name] = new Array();
    if(typeof(f) == "function")
        callElems[name].push(f);
}

function networkEvent(e) {
    alert(e);
}
var index = 0
function networkRecursion(elem,netObjs) {
    re = RegExp("(?:^|\s)network_([a-zA-Z0-9_]{1,50})");
    if (elem.className) {
        search = re.exec(elem.className.toLowerCase());
        if (search) {
            if (!netObjs)
                netObjs = new Array();
            if (netObjs.indexOf(search[1].toLowerCase()) < 0)
                netObjs.push(search[1].toLowerCase());
        }
    }

    if (netObjs)
        if(elem.tagName){
            id = netObjs.indexOf(elem.tagName.toLowerCase());
            if (id >= 0) {
                if (!netElems[netObjs[id]])
                    netElems[netObjs[id]] = new Array();
                netElems[netObjs[id]].push(elem);
        }

    }

    if (!elem.id) {
        elem.id = "net-" + index;
        index++;
    }
    if (elem.childNodes.length > 0)
        for (var i = 0; i < elem.childNodes.length; i++) {
            
            networkRecursion(elem.childNodes[i],netObjs)
        }
    
}

function encodeMessage(data) {
    var buf = new Uint8Array(data.length + 10)
    if (data.length >= 126 && data.length <= 65535) {
        
    }
}
function onLoad() {
    $("#serverBuilder").load("servbuilder.html", init);
}
function init() {
  
    getNetworkElements();
    socket = new WebSocket("ws://192.168.56.1:9999");
    socket.binaryType = "blob";
    socket.onopen = function () {
        //socket.send("/getEbayListings")
        for (var i = 0; i < connected.length; i++) {
            connected[i]();
        }
        
    };
    socket.onmessage = function (event) {
        fr = new FileReader();
        fr.readAsArrayBuffer(event.data);
        
        readBlob(fr);
    }


}

function getMessageLength(dv,offset) {
    if (dv.getUint8(offset) > 127) {
        console.log("Error in getMessageLength!");
        return [-1,-1];
    }

    len = dv.getUint8(offset);
    if (len == 126) {
        return [(dv.getUint8(offset + 1) << 8) | dv.getUint8(offset + 2),3];
    }
    else if (len == 127) {
        return [(dv.getUint8(offset + 1) << 24) | (dv.getUint8(offset + 2) << 16) | (dv.getUint8(offset + 3) << 8) | dv.getUint8(offset + 4),5];
    }
    else
        return [len,1];
}

var arrayWalkClass = function (walk) {
    if (walk) {
        this.parentArray = walk.parentArray;
        this.currentArray = walk.currentArray;
        this.index = walk.index;
    }
    else {
        this.parentArray = null;
        this.currentArray = null;
        this.index = 0;
    }

}

var arrayWalk = new arrayWalkClass();

function r_readPacket(dv, idx) {
	while (idx < dv.byteLength) {
		var objtype = dv.getUint8(idx);
		idx += 1;
		var truelen = getMessageLength(dv, idx);
		idx += truelen[1];


		if (objtype == ObjType._func) {
			var re = String.fromCharCode.apply(null, new Uint8Array(fr.result.slice(idx, idx + truelen[0])));
			a = new Array(2);
			a[0] = re;
			a[1] = new Array();
			cmds.push(a);
			idx += truelen[0];
		}
		else if (objtype == ObjType._str) {
			
			var re = String.fromCharCode.apply(null, new Uint8Array(fr.result.slice(idx, idx + truelen[0])));
			
			if (arrayWalk.currentArray) {
				arrayWalk.currentArray.push(re)
				
				if (arrayWalk.currentArray.length >= arrayWalk.index) {
				    while (true) {
				        if (arrayWalk.parentArray) {
				            arrayWalk = new arrayWalkClass(arrayWalk.parentArray);
				            if (arrayWalk.currentArray.length < arrayWalk.index)
				                break
				        }
				        else {
				            arrayWalk.currentArray = null;
				            break;
				        }
				    }
				}
			}
			else
				cmds[cmds.length - 1][1].push(re)
			idx += truelen[0];
		}
		else if (objtype == ObjType._array) {
			a = new Array()
			
			if (arrayWalk.currentArray) {
				arrayWalk.parentArray = new arrayWalkClass(arrayWalk);
				arrayWalk.currentArray.push(a);

			}
			else
				cmds[cmds.length - 1][1].push(a)
			arrayWalk.currentArray = a
			arrayWalk.index = truelen[0];			
		}
		else if (objtype == ObjType._int) {
		    fl = truelen[0];
		    if (arrayWalk.currentArray) {
		        arrayWalk.currentArray.push(fl)

		        if (arrayWalk.currentArray.length >= arrayWalk.index) {
		            while (true) {
		                if (arrayWalk.parentArray) {
		                    arrayWalk = new arrayWalkClass(arrayWalk.parentArray);
		                    if (arrayWalk.currentArray.length < arrayWalk.index)
		                        break
		                }
		                else {
		                    arrayWalk.currentArray = null;
		                    break;
		                }
		            }
		        }
		    }
		    else
		        cmds[cmds.length - 1][1].push(fl)
		}
		else if (objtype == ObjType._float) {
		    fl = truelen[0] / 256.0;
		    if (arrayWalk.currentArray) {
		        arrayWalk.currentArray.push(fl)

		        if (arrayWalk.currentArray.length >= arrayWalk.index) {
		            while (true) {
		                if (arrayWalk.parentArray) {
		                    arrayWalk = new arrayWalkClass(arrayWalk.parentArray);
		                    if (arrayWalk.currentArray.length < arrayWalk.index)
		                        break
		                }
		                else {
		                    arrayWalk.currentArray = null;
		                    break;
		                }
		            }
		        }
		    }
		    else
		        cmds[cmds.length - 1][1].push(fl)
		    
		}
		
		
	}
}
var buf = "";
var cmds = [];
function readBlob(fr) {
    
    if (!fr.result) {
        window.setTimeout(function () { readBlob(fr); }, 60);
        return;
    }

    var dv = new DataView(fr.result, 0);
    r_readPacket(dv, 0);

    var cmdPos = 0;
    
    

    for (var i = 0; i < cmds.length; i++) {
        cmd = "n_" + cmds[i][0];
        if (window[cmd])
            window[cmd].apply(null, cmds[i][1]);

    }
    cmds = []
 

    


}
function addCommand(cmd){

    buf = "";
    
    var args = []
    for(var i=1; i<arguments.length; i++)
        args.push(arguments[i]);
    buf += String.fromCharCode(ObjType._func);
    buf += writeInt(cmd.length,32);	//Pretty much everything after the initial handshake has to use a 32 bit uint for the size
    buf += cmd;						        //due to javascript bit operations using 32bit ints (max 15.99tb)
    if(args.length > 0)
        writeObjects(args);
    console.log(cmd + " " +arguments.length);
    socket.send(getBlob(), { binary: true });
}
	
function getBlob() {
    var blob = new Blob([buf])
    
    return blob;
    
}

function writeObjects(args){

    for(var i=0; i<args.length; i++) {
        var arg = args[i];
        if(Object.prototype.toString.call(arg) == Object.prototype.toString.call(String.prototype)) {
            buf += String.fromCharCode(ObjType._str);
            buf += writeInt(arg.length, 32);
            buf += arg;
            
        }
        else if (Object.prototype.toString.call(arg) == Object.prototype.toString.call(Array.prototype)) {
            buf += String.fromCharCode(ObjType._array);
            buf += writeInt(arg.length, 32);           
            writeObjects(arg);
        }
        else if (Object.prototype.toString.call(arg) == Object.prototype.toString.call(Number.prototype)) {
            buf += String.fromCharCode(ObjType._int);
            buf += writeInt(arg);
        }
    }
}

function n_cmdRecv(success) {
    console.log("Server got command!");
}

function n_updateNetElem(name) {
    var args = new Array();
    for (var i = 1; i < arguments.length; i++)
        args.push(arguments[i]);
    elems = document.getElementsByName(name);
    for (var i = 0; i < elems.length; i++) {
        if (elems[i].tagName == "INPUT") {
            elems[i].value = args.join("");
        }
        else if (elems[i].tagName == "SELECT") {
            elems[i].innerHTML = "";
            for (var y = 0; y < args[0].length; y++) {
                console.log(args[0]);
                e = document.createElement("option");
                e.innerHTML = args[0][0][0];
                e.setAttribute("value", args[0][0][1]);
                elems[i].appendChild(e);
            }
        }
    }
}

function n_updateNetElems(type) {


    e = callElems[type];
    var args = new Array();
    for (var i = 1; i < arguments.length; i++)
        args.push(arguments[i]);
    if (e)
        for (var i = 0; i < e.length; i++) {
            func = e[i];
            if (typeof (func) == "function")
                func.apply(null, args);
        }
}

function writeInt(l) {
    var encoded = "";
    if (l < 126) {
        encoded += String.fromCharCode(l);
    }
    else if(l >= 126 && l <= 65535) {
        encoded += String.fromCharCode(126)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 8)) >> 8)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 0)) >> 0)
    }
    else if(l > 65535) {
        encoded += String.fromCharCode(127)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 24)) >> 24)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 16)) >> 16)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 8)) >> 8)
        encoded += String.fromCharCode((l & (((1 << 8) - 1) << 0)) >> 0)
    }
    return encoded;
    
}

function sendCommand(cmd) {
    var packet = "hello";

    var blob = new Blob([packet], { type: "application/octet-stream" });
    socket.send(blob);

}

function cmd_updateEbayList(data) {
    var ebayTable = document.getElementById("ebayListingTable");
    var listingArray = data.split("\n");
    var tbody = ebayTable.getElementsByTagName("tbody");
    if (tbody.length > 0)
        tbody = tbody[0]
    tbody.innerHTML = "";
    for (var i = 0; i < listingArray.length; i++) {
        itemData = listingArray[i].split("\r");
        tbody.innerHTML += "<td>"
        tbody.innerHTML += "<tr><a href ='" + itemData[1] + "'>" + itemData[0] + "</a></tr>"
        tbody.innerHTML += "</td></a>"

    }
}

function debugFileReader() {
    var fileInput = document.getElementById('fileInput');
    fileInput.addEventListener('change', function (e) {
        var file = fileInput.files[0];
        var textType = /text.*/;

        if (file.type.match(textType)) {
            var reader = new FileReader();

            reader.onload = function (e) {
                socket.send(reader.result);
            }

            reader.readAsText(file);
        } else {
            fileDisplayArea.innerText = "File not supported!"
        }
    });
}

window.onload = onLoad;
