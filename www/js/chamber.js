var $nprCall = null;
var $nprUncall = null;
var $toggleAP = null;

var onDocumentReady = function() {
    $nprCall = $('.npr-call');
    $nprUncall = $('.npr-uncall');
    $toggleAP = $('.ap-call .btn');

    $nprCall.on('click', onCallClick);
    $nprUncall.on('click', onUncallClick);
    $toggleAP.on('click', onToggleAPClick);
}

$(onDocumentReady);

/*
 * When PR call button is clicked.
 */
var onCallClick = function() {
    var $this = $(this);
    var $row = $this.closest('tr');
    var race_slug = $row.data('state-slug');

    $row.find('.npr-uncall,.npr-call,.npr-winner').addClass('hidden');

    $this.addClass('hidden');

    $this.siblings('.npr-uncall,.npr-winner').removeClass('hidden');

    // POST!
    buttonPOST({
        post_data: {
            race_slug: race_slug,
            first_name: $(this).parent('span').attr('data-first-name'),
            last_name: $(this).parent('span').attr('data-last-name')
        },
        target: this
    });
}

/*
 * When NPR uncall button is clicked.
 */
var onUncallClick = function() {
    var $this = $(this);
    var $row = $this.closest('tr');
    var race_slug = $row.data('state-slug');

    $this.addClass('hidden');

    $row.find('.npr-call').removeClass('hidden');
    $row.find('.npr-winner').addClass('hidden');

    // POST!
    buttonPOST({
        post_data: {
            race_slug: race_slug,
            clear_all: true
        },
        target: this
    });
}

/*
 * When AP toggle button is clicked.
 */
var onToggleAPClick = function() {

    // Identify the race.
    var race_slug = $(this).attr('id');

    // If we're already accepting ap calls, do the opposite.
    if ( $(this).hasClass('btn-success') ) {

        // Here's the options. Ain't javascript fun?
        buttonPOST({
            post_data: {
                race_slug: race_slug,
                accept_ap_call: false
            },
            button: {
                pre_state: 'btn-success',
                post_state: 'btn-warning'
            },
            message: 'Not accepting AP calls',
            target: this
        });

    // Otherwise, do the opposite.
    } else {
        buttonPOST({
            post_data: {
                race_slug: race_slug,
                accept_ap_call: true
            },
            button: {
                pre_state: 'btn-warning',
                post_state: 'btn-success'
            },
            message: 'Accepting AP calls',
            target: this
        });
    }
}

// A sort of generic function to read options and handle changing button state and POSTing to an URL.
function buttonPOST(options){

    function acceptAP(){
        // Check if we have targets.
        if ( options.target != undefined ) {
            // Monkey with buttons.
            if ( options.button.pre_state != undefined ){
                $(options.target).removeClass(options.button.pre_state);
            }
            if ( options.button.post_state != undefined ){
                $(options.target).addClass(options.button.post_state);
            }
            if ( options.message != undefined ){
                $(options.target).html(options.message);
            }
        }
        var target = $(options.target).attr('data-race-slug');

        if (options.post_data.accept_ap_call == false) {
            $('tr.'+target+' .npr-call').removeClass('hidden');
        } else {
            $('tr.'+target+' .npr-call').addClass('hidden');
            $('tr.'+target+' .npr-uncall').addClass('hidden');
            $('tr.'+target+' .npr-winner').addClass('hidden');
        }
    }

    // POST some data.
    $.post(window.location.href + 'call/', options.post_data, function(e){
        if ( options.post_data.accept_ap_call != undefined ) { acceptAP(); }
    });
}


