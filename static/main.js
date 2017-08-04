var websocket = new WebSocket(window.location.href.replace("http","ws") + "ws");
var console = document.getElementById("console");
websocket.onmessage = function(event) {
  var data = JSON.parse(event.data);
  switch(data.type) {
    case "console":
      console.innerHTML += '<div class="console_entry">' + data.content.output + '</div>\n';
      break;
    default:
      console.log("Recieved improper type from server of " + data.type);
      break;
  }
}
