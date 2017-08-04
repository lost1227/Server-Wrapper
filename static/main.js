var websocket = new WebSocket(window.location.href.replace("http","ws") + "ws");
var cons = document.getElementById("console");
websocket.onmessage = function(event) {
  var data = JSON.parse(event.data);
  switch(data.type) {
    case "console":
      cons.innerHTML += '<div class="console_entry">' + data.content.output + '</div>\n';
      break;
    case "error":
      console.log("Error: " + data.content.output)
      break;
    default:
      console.log("Recieved improper type from server of " + data.type);
      break;
  }
}
