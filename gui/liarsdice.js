// Liar's Dice GUI WAMP Endpoint
// Evan Widloski - 2017-10-26

if (document.location.origin === "null" || document.location.origin === "file://") {
    wsuri = "ws://127.0.0.1:8080/ws";
}
else {
    wsuri = (document.location.protocol === "http:" ? "ws:" : "wss:") + "//" + document.location.hostname + ":8080/ws";
}

// the WAMP connection to the Router
var connection = new autobahn.Connection({
    url: wsuri,
    realm: "realm1",
    max_retries: -1
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
    // console.log("received event for gameboard");
    gameboard = gb[0];
    $("#dump").html(JSON.stringify(gameboard, null, '\t'));
    var table = $("#gameboard");
    $("#gameboard tbody tr").remove()
    $("#gameboard tbody td").remove()

    console.log(gameboard.player_list)
    gameboard.player_list.forEach(function (player_id, index) {
        if (player_id == gameboard.winning_player) {
            tr_class = "success";
        }
        else if (player_id == gameboard['current_player']){
            tr_class = "active";
        }
        else if (gameboard.active_players.indexOf(player_id) > -1) {
            tr_class = "";
        }
        else {
            tr_class = "danger";
        }

        // if stash for a certain player is known, show their stash
        if(gameboard.stashes[player_id]){
            dice_html = "<td>"
            gameboard.stashes[player_id].forEach(function (dice){
                dice_html += "<img class=\"dice\" src=/dice/" + dice + ".png>"
            });
            dice_html += "</td>";
        }
        // otherwise, fill in with grey boxes
        else {
            console.log("no stash");
            dice_html = "<td>" +
                "<img class=\"dice\" src=/dice/unknown.png>".repeat(gameboard.stash_sizes[player_id]) +
                "</td>";

        }
        $('#gameboard tbody').append(['<tr class="', tr_class, '">',
                                      '<td>', index, '</td>',
                                      '<td>', player_id, '</td>',
                                      dice_html,
                                      '<td>', gameboard.last_wins[player_id], '</td>',
                                      '</tr>'].join(''));
    });
}


// ----------------------------------------------

// return a subscribe success callback function
// if history is true, return a function that calls the handler with the latest history event
function get_success_callback(history=false) {
    function subscription_success(subscription) {
        console.log('subscribed to topic', subscription.topic);
        if (history) {
            session.call('wamp.subscription.get_events', [subscription.id, 100]).then(
                function (history){
                    console.log('getting previous events for topic ' + subscription.topic);
                    // if history available, pass events one by one to callback function
                    console.log(history.length)
                    if (history.length > 0) {
                        history.reverse().forEach(function(element) {
                            console.log(element.args);
                            subscription.handler(element.args);
                        });
                    }
                    // if there's no events, pass a null value
                    else {
                        subscription.handler(null);
                    }
                }
            );
        }
    }
    return subscription_success;
}

// subscribe failure callback
function subscription_fail(err) {
    console.log('failed to subscribe to topic', err);
}
// subscribe failure callback

// receive messages to display in gui log
function subscribe_console(message) {
    log = $('#log');
    autoscroll = log.scrollTop() + log.height() >= log[0].scrollHeight - 10;
    log.val(log.val() + '\n' + message);
    if (autoscroll) {
        log.scrollTop(log[0].scrollHeight - log.height());
    }
}


// fired when connection is established and session attached
connection.onopen = function (s, details) {
    session = s;

    console.log("Connected");
    $("#connection_true").show();
    $("#connection_false").hide();

    session.subscribe('server.gameboard', subscribe_gameboard).then(
        get_success_callback(history=true), subscription_fail
    );
    session.subscribe('server.console', subscribe_console).then(
        get_success_callback(history=true), subscription_fail
    );

};

// fired when connection was lost (or could not be established)
connection.onclose = function (reason, details) {
    console.log("Connection lost: " + reason);
    // clear gameboard display
    subscribe_gameboard([]);
    $("#connection_true").hide();
    $("#connection_false").show();
};

// open the connection
connection.open();
