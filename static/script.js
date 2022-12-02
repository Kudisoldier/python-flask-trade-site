function sort_by_bot(element) {
    if ($(element).html() == 'All bots') {
        $('#bots_dropdown_current').html("All bots");
        $('#bot_price').html('0.00');
        $('#bot_selected_items').children().remove();
        $('#bot_items').children().show();
    } else {
        bot = $(element).html().split(' ')[1];
        $('#bots_dropdown_current').html("Bot " + bot);
        $('#bot_selected_items').children().remove();
        $('#bot_price').html('0.00');
        $('#bot_items').children().each(function() {
            if ($(this).attr('bot') != bot) {
                $(this).hide()
            } else {
                $(this).show()
            }
        })
    }
    
    if ((parseFloat($('#bot_price').html()) - parseFloat($('#your_price').html())).toFixed(2) <= 0 && parseFloat($('#your_price').html()).toFixed(2) > 0) {
        $('#trade_button').attr('disabled', false)
    } else {
        $('#trade_button').attr('disabled', true)
    }
}


function setup_tradelink() {
    $('#tradelink_button').attr('disabled', true);
    $.post('/set_tradelink?tradelink=' + encodeURIComponent($("#tradelink_form").val()), function(data) {
        if (data == 'success') {
            $('#tradelinkModal').modal('hide');
            $('#tradelink_error').hide();
            $('#tradelink_button').attr('disabled', false);
        } else {
            $('#tradelink_error').fadeIn(1250).delay(12500).fadeOut(1250);
            setTimeout(function() {
                $('#tradelink_button').attr('disabled', false);
            }, 15000);
        }
    })
}


function send_trade() {
    $('#trade_modal_body').html('<div class="spinner-border" role="status"></div> Processing tradeoffer...');
    if ($('#bot_selected_items').children().attr('bot') == undefined) {
        params = '?bot=0'
    } else {
        params = '?bot=' + $('#bot_selected_items').children().attr('bot')
    }
    params += '&my_ids=';
    elements = $('#your_selected_items').children();
    for (i = 0; i < elements.length; i++) {
        params += elements[i]['id'] + ','
    }
    params = params.substr(0, params.length - 1);

    params += '&bot_ids=';

    elements = $('#bot_selected_items').children();
    for (i = 0; i < elements.length; i++) {
        params += elements[i]['id'] + ','
    }

    params = params.substr(0, params.length - 1);

    $.post('/send_trade' + params, function(data) {
        var jsn = JSON.parse(data);
        if (jsn["tradeofferid"] == 'error') {
            $('#trade_modal_body').html(jsn["error"]);
        } else {
            $('#trade_modal_body').html('<a href="http://steamcommunity.com/tradeoffer/' + jsn['tradeofferid'] + '" target="_blank">Click here to open the trade offer.</a>');
        }
        $('#trade_button').attr('disabled', true);
    })
    
    $('#your_selected_items').html('');
    $('#bot_selected_items').html('');
    $('#bot_price').html('0.00');
    $('#your_price').html('0.00');
    $('#your_items').children().show();
    $('#bot_items').children().show();
    $('#bots_dropdown_current').html("All bots");
}


function update_inventory_user() {
    $.post('/get_user_inventory', function(data) {
        $('#your_price').html('0.00');
        $('#your_items').html('');
        $('#your_selected_items').html('');
        var jsn = JSON.parse(data);
        jsn.sort(function(a, b){
            return b[3] - a[3];
        });
        for (i = 0; i < jsn.length; i++) {
            $('#your_items').append(`<div class="card bg-dark text-white" id="` + jsn[i][0] + `" onclick=move(this)>
                  <div id="name">` + jsn[i][1] + `</div> <img class="card-img" src="http://cdn.steamcommunity.com/economy/image/` + jsn[i][2] + `" alt="Card image"> 
                <div id="price">` + jsn[i][3] + `</div> </div>`);
        }
    })
}


function update_inventory_bot() {
    $.post('/get_bots_inventory', function(data) {
        $('#bot_price').html('0.00');
        $('#bot_items').html('');
        $('#bot_selected_items').html('');
        $('#bots_dropdown_current').html("All bots");
        $('#bots_dropdown_items').html('<a class="dropdown-item" onclick=sort_by_bot(this)>All bots</a>');
        var jsn = JSON.parse(data);
        bots_len = jsn[jsn.length - 1][4] + 1;
        jsn.sort(function(a, b){
            return b[3] - a[3];
        });
        for (i = 0; i < jsn.length; i++) {
            $('#bot_items').append(`<div class="card bg-dark text-white" id="` + jsn[i][0] + `" bot="` + jsn[i][4] + `" onclick=move(this)>
                  <div id="name">` + jsn[i][1] + `</div> <img class="card-img" src="http://cdn.steamcommunity.com/economy/image/` + jsn[i][2] + `" alt="Card image"> 
                <div id="price">` + jsn[i][3] + `</div> </div>`);
        }
        
        for (i = 0; i < bots_len; i++) {
            $('#bots_dropdown_items').append('<a class="dropdown-item" onclick=sort_by_bot(this)>Bot ' + i + '</a>');
        }
    })
}


update_inventory_bot();
update_inventory_user();


function move(element) {
    if ($(element).parent()[0]['id'] == 'your_items') {
        $(element).clone().appendTo("#your_selected_items");
        $(element).hide();
        $('#your_price').html((parseFloat($('#your_price').html()) + parseFloat($(element).find("#price").html())).toFixed(2));
    } else if ($(element).parent()[0]['id'] == 'your_selected_items') {
        $(element).remove();
        $('#your_items').find("#" + $(element).attr('id')).show();
        $('#your_price').html((parseFloat($('#your_price').html()) - parseFloat($(element).find("#price").html())).toFixed(2));
    } else if ($(element).parent()[0]['id'] == 'bot_items') {
        $('#bots_dropdown_current').html("Bot " + $(element).attr('bot'));
        $(element).clone().appendTo("#bot_selected_items");
        $(element).hide();
        if ($('#bot_selected_items').children().length == 1) {
            $('#bot_items').children().each(function() {
                if ($(this).attr('bot') != $(element).attr('bot')) {
                    $(this).hide()
                }
            })
        }
        $('#bot_price').html((parseFloat($('#bot_price').html()) + parseFloat($(element).find("#price").html())).toFixed(2));
    } else if ($(element).parent()[0]['id'] == 'bot_selected_items') {
        $(element).remove();
        $('#bot_items').find("#" + $(element).attr('id')).show();
        if ($('#bot_selected_items').children().length == 0) {
            $('#bot_items').children().show();
            $('#bots_dropdown_current').html("All bots");
        }
        $('#bot_price').html((parseFloat($('#bot_price').html()) - parseFloat($(element).find("#price").html())).toFixed(2));
    }
    
    if ((parseFloat($('#bot_price').html()) - parseFloat($('#your_price').html())).toFixed(2) <= 0 && parseFloat($('#your_price').html()).toFixed(2) > 0) {
        $('#trade_button').attr('disabled', false)
    } else {
        $('#trade_button').attr('disabled', true)
    }
}


function sort_your_invetory() {
    ul = $('#your_items');
    ul.children().each(function(i,li){ul.prepend(li)});
    if ($('#your_sort_state').find("i").attr('class') == "fas fa-sort-amount-up") {
        $('#your_sort_state').find("i").attr('class', 'fas fa-sort-amount-down')
    } else {
        $('#your_sort_state').find("i").attr('class', 'fas fa-sort-amount-up')
    }
}


function sort_bot_invetory() {
    ul = $('#bot_items');
    ul.children().each(function(i,li){ul.prepend(li)});
    if ($('#bot_sort_state').find("i").attr('class') == "fas fa-sort-amount-up") {
        $('#bot_sort_state').find("i").attr('class', 'fas fa-sort-amount-down')
    } else {
        $('#bot_sort_state').find("i").attr('class', 'fas fa-sort-amount-up')
    }
}
