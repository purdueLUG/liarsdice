// Liar's Dice GUI WAMP Endpoint
// Evan Widloski - 2017-10-26

// if (document.location.origin === "null" || document.location.origin === "file://") {
//     wsuri = "ws://127.0.0.1:8080/ws";
// }
// else {
//     wsuri = (document.location.protocol === "http:" ? "ws:" : "wss:") + "//" +
//         document.location.host + "/ws";
// }

var wsuri = "ws://10.186.81.49:8080/ws";

// the WAMP connection to the Router
var connection = new autobahn.Connection({
    url: wsuri,
    realm: "realm1"
});

var table;

var gameboard;

var alert_template = `<div id="alert" class="alert %s" role="alert">%s</div>`;

function alert_message(text) {
    alert_html = sprintf(alert_template, "alert-info", text);
    $("#alert-box").html(alert_html);
    $("#alert").fadeTo(2000, 500).slideUp(500, function(){
        $("#alert").slideUp(500);
    });
}
function alert_warning(text) {
    alert_html = sprintf(alert_template, "alert-warning", text);
    $("#alert-box").html(alert_html);
    $("#alert").fadeTo(2000, 500).slideUp(500, function(){
        $("#alert").slideUp(500);
    });
}
function alert_error(text) {
    alert_html = sprintf(alert_template, "alert-danger", text);
    $("#alert-box").html(alert_html);
    $("#alert").fadeTo(2000, 500).slideUp(500, function(){
        $("#alert").slideUp(500);
    });
}

// ---------------- PUB/SUB --------------------

// subscribe to gameboard updates
function subscribe_gameboard(gb) {
    console.log("received event for gameboard");
    gameboard = gb[0];
    $("#dump").html(JSON.stringify(gameboard, null, '\t'));
    var table = $("#gameboard");
    $("#gameboard tr").remove()
    $("#gameboard td").remove()
    // var stashes = {"db1": [1,1,1,1]}

    gameboard.player_list.forEach(function (player_id, index) {
        console.log(player_id);
        if (player_id == gameboard['player_id']){
            tr_class = "active";
        }
        else {
            tr_class = "";
        }
        $('#gameboard tbody').append(['<tr class="', tr_class, '">',
                                      '<td>', index, '</td>',
                                      '<td>', player_id, '</td>',
                                      '<td><img src=/dice/', 1, '.png></td>',
                                      '</tr>'].join(''));
    });
}


// ----------------------------------------------

// subscribe success callback
function subscription_success(subscription) {
    console.log('successfully to subscribe to topic', subscription);
}

// subscribe failure callback
function subscription_fail(err) {
    console.log('failed to subscribe to topic', err);
}


// fired when connection is established and session attached
connection.onopen = function (s, details) {
    session = s;

    console.log("Connected");
    $("#connection_true").show();
    $("#connection_false").hide();

    // session.subscribe('wamp.session.on_leave', subscribe_session_leave).then(
    //     subscription_success, subscription_fail
    // );
    // session.subscribe('wamp.session.on_join', subscribe_session_join).then(
    //     subscription_success, subscription_fail
    // );
    session.subscribe('server.gameboard', subscribe_gameboard).then(
        subscription_success, subscription_fail
    );

};

// fired when connection was lost (or could not be established)
connection.onclose = function (reason, details) {
    console.log("Connection lost: " + reason);
    $("#connection_true").hide();
    $("#connection_false").show();
    // hide quadcopter connection status
    // $("#connection_true").hide();
    // $("#connection_false").hide();
};

// open the connection
connection.open();
