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
var $chromecastChangeState = null;

var $header = null;
var $headerControls = null;
var $fullScreenButton = null;
var $statePickerLink = null;
var $chromecastButton = null;
var $audioPlayer = null;
var $bop = null;
var $stack = null;

var $shareModal = null;
var $commentCount = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);
var IS_FAKE_CASTER = (window.location.search.indexOf('fakecast') >= 0);

var state = null;
var station = null;
var streamUrl = 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3';
var firstShareLoad = true;
var is_casting = false;

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
    $rotate = $('.rotate-phone-wrapper');

    $statePickerForm  = $('form.state-picker-form');
    $statePickerScreen = $('.state-picker');
    $statePickerLink = $ ('.state-picker-link');
    $stateface = $('.stateface');
    $stateName = $('.state-name');

    $chromecastScreen = $('.cast-controls');
    $chromecastMute = $chromecastScreen.find('.mute');
    $chromecastChangeState = $chromecastScreen.find('.change-state');
    $castStart = $('.cast-start');
    $castStop = $('.cast-stop');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen a');
    $chromecastButton = $('.chromecast');
    $bop = $('.leaderboard');
    $stack = $('#stack');
    $header = $('.index');
    $headerControls = $('.header-controls');
    $shareModal = $('#share-modal');
    $commentCount = $('.comment-count');


    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);

    $statePickerForm.submit(onStatePickerSubmit);

    $chromecastMute.on('click', onCastMute);
    $chromecastChangeState.on('click', onStatePickerLink);
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
        CHROMECAST_RECEIVER.onMessage('state', onCastStateChange);

        localizeRadio();

        STACK.start();
    } else if (IS_FAKE_CASTER) {
        is_casting = true;
        state = 'TX';
        onCastStarted();
    } else {
        // Prepare welcome screen
        $welcomeScreen.css('opacity', 1);
        //resizeSlide($welcomeScreen);
        rotatePhone();

        // Configure share panel
        ZeroClipboard.config({ swfPath: 'js/lib/ZeroClipboard.swf' });
        var clippy = new ZeroClipboard($(".clippy"));

        clippy.on('ready', function(readyEvent) {
            clippy.on('aftercopy', onClippyCopy);
        });

        // Geolocate
        if ($.cookie('state')) {
            state = $.cookie('state');
            loadState();
        }
        if (geoip2 && !($.cookie('state'))) {
            geoip2.city(onLocateIP);
        }

        localizeRadio();
    }

    onWindowResize();
    setupStateTypeahead();
    checkBop();
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
 * Prepare typeahead for state picker.
 */
var setupStateTypeahead = function() {
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
    $stack.hide();
    STACK.stop();

    if (!state) {
        $statePickerScreen.show();
        resizeSlide($statePickerScreen);
    } else {
        $statePickerScreen.hide();
        $chromecastScreen.show();
        resizeSlide($chromecastScreen);
    }

    is_casting = true;
}

/*
 * A cast session stopped.
 */
var onCastStopped = function() {
    $chromecastScreen.hide();

    STACK.start();

    is_casting = false;
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
 * Change the state on the receiver.
 */
var onCastStateChange = function(message) {
    state = message;
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
    var width = $(window).width();
    var height = $(window).height();

    var target_width = 1280;
    var target_height = 720;

    var new_height = width * 9 / 16;
    var padding = (height - new_height) / 2;

    if (padding < 0) {
        padding = 0;
    }

    $('#landscape-wrapper').css({
        'height': new_height + 'px',
        'position': 'absolute',
        'top': padding + 'px'
    });

    var thisSlide = $('.slide');
    resizeSlide(thisSlide);
    rotatePhone();
}

/*
 * Resize a slide to fit the viewport.
 */
var resizeSlide = function(slide) {
    var $w = $('#landscape-wrapper').width();
    var $h = $('#landscape-wrapper').height();
    var headerHeight = 0;

    slide.width($w);
    slide.height($h - headerHeight);

    slide.find('.slide-inner').width($w);
    slide.find('.slide-inner').height($h - headerHeight);
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

}

/*
 * Matcher for typeahead.
 */
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

    var fullscreenElement = document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement;

    console.log(fullscreenElement);

    if (fullscreenElement) {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        }
        else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        }
        else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
        $fullScreenButton.find('img').attr('src', APP_CONFIG.S3_BASE_URL + '/assets/icon-expand.svg');
    }
    else {
        if (elem.requestFullscreen) {
          elem.requestFullscreen();
        }
        else if (elem.msRequestFullscreen) {
          elem.msRequestFullscreen();
        }
        else if (elem.mozRequestFullScreen) {
          elem.mozRequestFullScreen();
        }
        else if (elem.webkitRequestFullscreen) {
          elem.webkitRequestFullscreen();
        }

        $fullScreenButton.find('img').attr('src', APP_CONFIG.S3_BASE_URL + '/assets/icon-shrink.svg');
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
        $header.fadeIn(200);
    });
}

/*
 * Select the state.
 */

var getState = function() {
    var input = $('.typeahead').typeahead('val');
    if (input) {
        var inverted = _.invert(APP_CONFIG.STATES);
        state = inverted[input]
    }

    $.cookie('state', state, { expires: 30 });
}

var loadState = function() {
    $stateface.removeClass();
    $stateface.addClass('stateface stateface-' + state.toLowerCase());
    $stateName.text(APP_CONFIG.STATES[state])
}

var switchState = function() {
    getState();
    loadState();

    $stateface.css('opacity', 1);
    $stateName.css('opacity', 1);
    $typeahead.css('top', '0');

    $('.typeahead').typeahead('val', '')
    $('.typeahead').typeahead('close');
    $('.typeahead').blur();
}

var hideStateFace = function() {
    $stateface.css('opacity', 0);
    $stateName.css('opacity', 0);

    if ($stateface.height() > 0 && $stateface.width() > 0) {
        $typeahead.css('top', '-15vw');
    }
}

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    $statePickerLink.text(APP_CONFIG.STATES[state]);
    $statePickerScreen.hide();

    if (is_casting) {
        $chromecastScreen.show();
        resizeSlide($chromecastScreen);
        CHROMECAST_SENDER.sendMessage('state', state);
    } else {
        STACK.start();
    }
}

/*
 * Reopen state selector.
 */
var onStatePickerLink = function() {
    $stack.hide();
    $chromecastScreen.hide();
    $statePickerScreen.show();
    resizeSlide($statePickerScreen);
}

/*
 * Set the geolocated state.
 */
var onLocateIP = function(response) {
    var place = response.most_specific_subdivision.iso_code;

    $('#option-' + place).prop('selected', true);
    state = place;
    $.cookie('state', state, { expires: 30 });

    latitude = response.location.latitude;
    longitude = response.location.longitude;

    loadState();
}

var checkBop = function() {
    setInterval(function() {
        $bop.load('/bop.html');
    }, APP_CONFIG.DEPLOY_INTERVAL * 1000);
}

var MOCK_LOCALIZATION_RESPONSE = {
    error: false,
    data: {
        callletters: "WAMU_FM",
        streamGuid: "4fcf71471a22460b8c99eb9f58fac6ca",
        logo: "//media.npr.org/images/stations/logos/wamu_fm.gif"
    }
};

/*
 * Find local radio station.
 */
var localizeRadio = function() {
    if ($.cookie('streamUrl')) {
        station = $.cookie('station');
        streamUrl = $.cookie('streamUrl');

        setUpAudio();
    } else {
        /*$.ajax({
            'dataType': 'jsonp',
            'url': 'http://api.npr.org/v2/local/stream/basic',
            'data': {
            },
            'success': onLocalizeResponse
        });*/

       onLocalizeResponse(MOCK_LOCALIZATION_RESPONSE);
    }
}

/*
 * Local radio station found.
 */
var onLocalizeResponse = function(data) {
    if (data['error']) {
        onLocalizationFailed();
    }

    var callLetters = data['data']['callletters'];

    // Strip "_FM"
    if (callLetters.indexOf('_') > 0) {
        callLetters = callLetters.substring(0, callLetters.indexOf('_'));
    }

    // Note: works thanks to CORS headers on api.npr.org
    $.ajax({
        'dataType': 'json',
        'url': 'http://api.npr.org/stations',
        'data': {
            'callLetters': callLetters,
            'apiKey': APP_CONFIG.NPR_API_KEY,
            'format': 'json'
        },
        'success': onStreamFound,
        'error': onLocalizationFailed

    });
}

/*
 * Station API lookup completed.
 */
var onStreamFound = function(data) {
    var stationData = data['station'][0];

    station = stationData['callLetters']['$text'];
    
    for (var i = 0; i < stationData['url'].length; i++) {
        var url = stationData['url'][i];

        if (url['typeId'] == '10') {
            streamUrl = url['$text']
            break
        }
    }

    $.cookie('station', station, { expires: 30 });
    $.cookie('streamUrl', streamUrl, { expires: 30 });

    setUpAudio();
}

/*
 * Local radio station lookup failed.
 */
var onLocalizationFailed = function() {
    station = null;
    streamUrl = 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3';

    $.cookie('station', station, { expires: 30 });
    $.cookie('streamUrl', streamUrl, { expires: 30 });
    
    setUpAudio();
}

/*
 * Setup audio playback.
 */
var setUpAudio = function(startPaused) {
    $audioPlayer.jPlayer({
        ready: function () {
            $(this).jPlayer('setMedia', {
                mp3: streamUrl 
            })

            if (IS_CAST_RECEIVER) {
                $(this).jPlayer('play');
            } else {
                $(this).jPlayer('pause');
            }
        },
        swfPath: 'js/lib',
        supplied: 'mp3',
        loop: false,
    });
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

$(onDocumentReady);
