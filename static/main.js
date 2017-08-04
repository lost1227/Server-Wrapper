var websocket = new WebSocket(window.location.href.replace("http","ws") + "ws");

function appendToConsole(text,clas) {
  var cons = $("#console");
  var bottom = (Math.abs(cons.outerHeight() - (cons[0].scrollHeight - cons.scrollTop())) < 1);
  console.log(bottom);
  cons.append('<div class="' + clas + '">' + text + '</div>');
  if(bottom) {
    cons.animate({scrollTop: cons[0].scrollHeight});
  }
}

websocket.onmessage = function(event) {
  var data = JSON.parse(event.data);
  switch(data.type) {
    case "console":
      appendToConsole(data.content.output,"console_entry");
      break;
    case "error":
      console.log("Error: " + data.content.output)
      break;
    default:
      console.log("Recieved improper type from server of " + data.type);
      break;
  }
}
$("#consolebox").keypress(function(e) {
  if(e.which == 13) {
    appendToConsole($("#consolebox").val(), "command_entry");
    console.log("Sending: " + JSON.stringify({
      "type":"console",
      "data":$("#consolebox").val()
    }));
    websocket.send(JSON.stringify({
      "type":"console",
      "data":$("#consolebox").val()
    }));
    $("#consolebox").val("")
  }
})
