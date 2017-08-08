var websocket = new WebSocket(window.location.href.replace("http","ws") + "ws");

var serveractive = false;

var serverstatus;

function appendToConsole(text,clas) {
  var cons = $("#console");
  var bottom = (Math.abs(cons.outerHeight() - (cons[0].scrollHeight - cons.scrollTop())) < 5);
  /*console.log(bottom);*/
  cons.append('<div class="' + clas + '">' + text + '</div>');
  if(bottom) {
    cons.animate({scrollTop: cons[0].scrollHeight},{"duration":0});
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
    case "status":
      serverstatus = data.content;
      updatestatus(data.content);
      break;
    default:
      console.log("Recieved improper type from server of " + data.type);
      break;
  }
}

websocket.onopen = function() {
  askforstatus();
}

$("#consolebox").keypress(function(e) {
  if(e.which == 13) {
    appendToConsole($("#consolebox").val(), "command_entry");
    /*console.log("Sending: " + JSON.stringify({
      "type":"console",
      "data":$("#consolebox").val()
    }));*/
    websocket.send(JSON.stringify({
      "type":"console",
      "data":$("#consolebox").val()
    }));
    $("#consolebox").val("")
  }
})

$("#serverstart").click(function() {
  websocket.send(JSON.stringify({
    "type":"start",
    "data":$("#serverselect").val()
  }))
})

function askforstatus() {
  websocket.send(JSON.stringify({
    "type":"status"
  }));
}
function updatestatus(status) {
  if(status.active) {
    $("#consolebox").prop('disabled',false);
    $("#console").removeClass("disabledconsole");
    $("#serverselect").prop('disabled',true);
    $("#serverstart").prop('disabled',true);
  }  else {
    $("#consolebox").prop('disabled',true);
    $("#console").addClass("disabledconsole");
    $("#serverselect").prop('disabled',false);
    $("#serverstart").prop('disabled',false);
  }
}
$("#sigint").click(function() {
  websocket.send(JSON.stringify({
    "type":"sigint"
  }))
})
$("#kill").click(function() {
  websocket.send(JSON.stringify({
    "type":"kill"
  }))
})
