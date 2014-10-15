// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;
var $rotate = null;

var $statePickerScreen = null;
var $statePickerSubmitButton = null;
var $statePickerForm = null;
var $stateface = null;
var $stateName = null;
var $typeahead = null;

var $chromecastScreen = null;
var $chromecastMute = null;

var $header = null;
var $headerControls = null;
var $fullScreenButton = null;
var $statePickerLink = null;
var $chromecastButton = null;
var $audioPlayer = null;
var $stack = null;

var $shareModal = null;
var $commentCount = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);

var state = null;
var firstShareLoad = true;

var STATES = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
  'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii',
  'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
  'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
  'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire',
  'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota',
  'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island',
  'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont',
  'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
];

/*
 * Run on page load.
 */
var onDocumentReady = function(e) {
    // Cache jQuery references
    $welcomeScreen = $('.welcome');
    $welcomeButton = $('.welcome-button')
    $welcomeSubmitButton = $('.state-picker-submit');
    $rotate = $('.rotate');

    $statePickerForm  = $('form.state-picker-form');
    $statePickerScreen = $('.state-picker');
    $statePickerLink = $ ('.state-picker-link');
    $stateface = $('.stateface');
    $stateName = $('.state-name');

    $chromecastScreen = $('.cast-controls');
    $chromecastMute = $chromecastScreen.find('.mute');
    $castStart = $('.cast-start');
    $castStop = $('.cast-stop');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen p');
    $chromecastButton = $('.chromecast');
    $stack = $('#stack');
    $header = $('.index');
    $headerControls = $('.header-controls');
    $shareModal = $('#share-modal');
    $commentCount = $('.comment-count');


    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);

    $statePickerForm.submit(onStatePickerSubmit);

    $chromecastMute.on('click', onCastMute);
    $castStart.on('click', onCastStartClick);
    $castStop.on('click', onCastStopClick);

    $fullScreenButton.on('click', onFullScreenButtonClick);
    $statePickerLink.on('click', onStatePickerLink);
    $shareModal.on('shown.bs.modal', onShareModalShown);
    $shareModal.on('hidden.bs.modal', onShareModalHidden);
    $(window).on('resize', onWindowResize);

    if (IS_CAST_RECEIVER) {
        $welcomeScreen.hide();

        CHROMECAST_RECEIVER.setup();
        CHROMECAST_RECEIVER.onMessage('mute', onCastReceiverMute);

        setUpAudio(false);

        STACK.start();
    } else {
        // Prepare welcome screen
        $welcomeScreen.css('opacity', 1);
        resizeSlide($welcomeScreen);
        rotatePhone();


        // Configure share panel
        ZeroClipboard.config({ swfPath: 'js/lib/ZeroClipboard.swf' });
        var clippy = new ZeroClipboard($(".clippy"));

        clippy.on('ready', function(readyEvent) {
            clippy.on('aftercopy', onClippyCopy);
        });

        // Geolocate
        if (geoip2) {
            geoip2.city(onLocateIP);
        }

        setUpAudio(true);
    }
}

/*
 * Setup Chromecast if library is available.
 */
window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    // Don't init sender if in receiver mode
    if (IS_CAST_RECEIVER) {
        return;
    }

    if (loaded) {
        CHROMECAST_SENDER.setup(onCastReady, onCastStarted, onCastStopped);
    }
}

/*
 * A cast device is available.
 */
var onCastReady = function() {
    $chromecastButton.show();
}

/*
 * A cast session started.
 */
var onCastStarted = function() {
    $welcomeScreen.hide();
    $statePickerScreen.hide();
    $stack.hide();
    $chromecastScreen.show();

    STACK.stop();
}

/*
 * A cast session stopped.
 */
var onCastStopped = function() {
    $chromecastScreen.hide();

    STACK.start();
}

/*
 * Mute or unmute the receiver.
 */
var onCastReceiverMute = function(message) {
    if ($audioPlayer.data().jPlayer.status.paused) {
        $audioPlayer.jPlayer('play');
    } else {
        $audioPlayer.jPlayer('pause');
    }
}

/*
 * Send the mute message to the receiver.
 */
var onCastMute = function() {
    CHROMECAST_SENDER.sendMessage('mute', 'toggle');
}

/*
 * Resize current slide.
 */
var onWindowResize = function() {
    var thisSlide = $('.slide');
    resizeSlide(thisSlide);
    rotatePhone();
}

var rotatePhone = function() {
    if (Modernizr.touch && Modernizr.mq('(orientation: portrait)')) {
        $rotate.show();
    }
    else {
        $rotate.hide();
    }
}

/*
 * Begin chromecasting.
 */
var onCastStartClick = function(e) {
    e.preventDefault();

    CHROMECAST_SENDER.startCasting();
}

/*
 * Stop chromecasting.
 */
var onCastStopClick = function(e) {
    e.preventDefault();

    CHROMECAST_SENDER.stopCasting();
}

/*
 * Advance to state select screen.
 */
var onWelcomeButtonClick = function() {
    $welcomeScreen.hide();
    $statePickerScreen.show();
    resizeSlide($statePickerScreen);

    $('.typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
    },
    {
        name: 'states',
        displayKey: 'value',
        source: substringMatcher(STATES)
    });

    $typeahead = $('.twitter-typeahead');

    $('.typeahead').on('typeahead:selected', switchState)
    $('.typeahead').on('typeahead:opened', hideStateFace)

}

var substringMatcher = function(strs) {
    return function findMatches(q, cb) {
        var matches = [];

        // iterate through the pool of strings and for any string that
        // contains the substring `q`, add it to the `matches` array
        $.each(strs, function(i, str) {
            var queryLength = q.length;
            var normalizedString = str.toLowerCase();
            if (normalizedString.substring(0, queryLength) === q.toLowerCase()) {
                // the typeahead jQuery plugin expects suggestions to a
                // JavaScript object, refer to typeahead docs for more info
                matches.push({ value: str });
            }
        });

        cb(matches);
    };
};

/*
 * Fullscreen the app.
 */
var onFullScreenButtonClick = function() {
    var elem = document.getElementById("stack");
    if (elem.requestFullscreen) {
      elem.requestFullscreen();
    } else if (elem.msRequestFullscreen) {
      elem.msRequestFullscreen();
    } else if (elem.mozRequestFullScreen) {
      elem.mozRequestFullScreen();
    } else if (elem.webkitRequestFullscreen) {
      elem.webkitRequestFullscreen();
    }
}



/*
 * Enable header hover.
 */
var onControlsHover = function() {
    $headerControls.data('hover', true);
    $header.fadeOut(200, function() {
        $headerControls.fadeIn(200);
    });
}

/*
 * Disable header hover.
 */
var offControlsHover = function() {
    $headerControls.data('hover', false);
    $headerControls.fadeOut(200, function() {
        $header.fadeIn(200, function() {
            $('body').data('mouse-moving', true);
        });
    });
}

/*
 * Select the state.
 */

var getState = function() {
    var input = $('.typeahead').typeahead('val');
    if (input) {
        state = getStatePostal(input)
    }
}

var switchState = function() {
    $stateface.css('opacity', 1);
    $stateName.css('opacity', 1);

    $typeahead.css('top', '0');

    var input = $('.typeahead').typeahead('val');
    var postal = getStatePostal(input)

    $stateface.removeClass();
    $stateface.addClass('stateface stateface-' + postal.toLowerCase());

    $stateName.text(input);
    getState();
    $('.typeahead').typeahead('val', '')
    $('.typeahead').typeahead('close');
    $('.typeahead').blur();
}

var hideStateFace = function() {
    $stateface.css('opacity', 0);
    $stateName.css('opacity', 0);

    if ($stateface.height() > 0 && $stateface.width() > 0) {
        $typeahead.css('top', '-23vw');
    }
}

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    $.cookie('state', state);

    $statePickerLink.text(APP_CONFIG.STATES[state]);

    $statePickerScreen.hide();

    STACK.start();
}

var getStatePostal = function(input) {
    var inverted = _.invert(APP_CONFIG.STATES);
    return inverted[input];
}

/*
 * Reopen state selector.
 */
var onStatePickerLink = function() {
    $stack.hide();
    $statePickerScreen.show();
}

/*
 * Set the geolocated state.
 */
var onLocateIP = function(response) {
    var place = response.most_specific_subdivision.iso_code;
    $('#option-' + place).prop('selected', true);

    $stateface.addClass('stateface-' + place.toLowerCase());
    var stateName = APP_CONFIG.STATES[place];
    $stateName.text(stateName)

    state = place;
}

/*
 * Display the comment count.
 */
var showCommentCount = function(count) {
    $commentCount.text(count);

    if (count > 0) {
        $commentCount.addClass('has-comments');
    }

    if (count > 1) {
        $commentCount.next('.comment-label').text('Comments');
    }
}

/*
 * Share modal opened.
 */
var onShareModalShown = function(e) {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'open-share-discuss']);

    if (firstShareLoad) {
        loadComments();

        firstShareLoad = false;
    }
}

/*
 * Share modal closed.
 */
var onShareModalHidden = function(e) {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'close-share-discuss']);
}

/*
 * Text copied to clipboard.
 */
var onClippyCopy = function(e) {
    alert('Copied to your clipboard!');

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'summary-copied']);
}

/*
 * Resize a slide to fit the viewport.
 */
var resizeSlide = function(slide) {
    var $w = $(window).width();
    var $h = $(window).height();
    var headerHeight = $header.height();

    slide.width($w);
    slide.height($h - headerHeight - 50);

    slide.find('.slide-content').width($w);
    slide.find('.slide-content').height($h - headerHeight - 50);
}


/*
 * Setup audio playback.
 */
var setUpAudio = function(startPaused) {
    $audioPlayer.jPlayer({
        ready: function () {
            $(this).jPlayer('setMedia', {
                mp3: 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3'
            })

            if (startPaused) {
                $(this).jPlayer('pause');
            } else {
                $(this).jPlayer('play');
            }
        },
        swfPath: 'js/lib',
        supplied: 'mp3',
        loop: false,
    });
}

$(onDocumentReady);
