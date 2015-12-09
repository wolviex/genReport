



function onConnect(ev) {

    document.getElementById("debug").innerHTML = "CONN";

}
var strsend = "v"
function trySend(socket,msg) {

    socket.send(msg);
    msg = msg + "v"
    

}
var socket
function init() {

    
    socket = new WebSocket("ws://192.168.56.1:9999")
    socket.onopen = function () {
       socket.send("/getEbayListings")
    };
    socket.onmessage = function (event) {

        if (event.data[0] == "/") {
            
            ix = event.data.indexOf(" ")
            il = event.data.length
            cmd = "cmd_" + event.data.substr(1, ix - 1)
            window[cmd](event.data.substr(ix,il))
        }
    }


}

function cmd_test(data) {

    var j = JSON.parse(data)
    

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

function readTextFile() {
    var rawFile = new XMLHttpRequest();
    rawFile.open("GET", "testing.txt", true);
    rawFile.onreadystatechange = function () {
        if (rawFile.readyState === 4) {
            var allText = rawFile.responseText;
            socket.send(allText)
        }
    }

    rawFile.send();
}

function test() {
    socket.send("/test");
}

window.onload = init;