// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;
var $rotate = null;

var $statePickerScreen = null;
var $statePickerForm = null;
var $stateWrapper = null;
var $stateface = null;
var $stateName = null;
var $typeahead = null;
var $statePickerHed = null;

var $chromecastScreen = null;
var $chromecastMute = null;
var $chromecastChangeState = null;
var $chromecastIndexHeader = null;

var $header = null;
var $headerControls = null;
var $fullScreenButton = null;
var $statePickerLink = null;
var $chromecastButton = null;
var $audioPlayer = null;
var $bop = null;
var $stack = null;
var $audioButtons = null;
var $countdown = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);
var IS_FAKE_CASTER = (window.location.search.indexOf('fakecast') >= 0);
var reloadTimestamp = null;

var state = null;
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
    $rotate = $('.rotate-phone-wrapper');

    $statePickerScreen = $('.state-picker');
    $statePickerForm  = $('form.state-picker-form');
    $statePickerLink = $ ('.state-picker-link');
    $stateWrapper = $('.state');
    $stateface = $('.stateface');
    $stateName = $('.state-name');
    $statePickerHed = $('.state-picker-hed');

    $chromecastScreen = $('.cast-controls');
    $chromecastMute = $chromecastScreen.find('.mute');
    $chromecastChangeState = $chromecastScreen.find('.change-state');
    $chromecastIndexHeader = $welcomeScreen.find('.cast-header');
    $castStart = $('.cast-start');
    $castStop = $('.cast-stop');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen a');
    $chromecastButton = $('.chromecast');
    $bop = $('.leaderboard');
    $stack = $('#stack');
    $header = $('.index');
    $headerControls = $('.header-controls');
    $audioButtons = $('.jp-controls .nav-btn');
    $countdown = $('#countdown');

    reloadTimestamp = moment();

    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);

    $statePickerForm.submit(onStatePickerSubmit);

    $chromecastMute.on('click', onCastMute);
    $chromecastChangeState.on('click', onStatePickerLink);
    $castStart.on('click', onCastStartClick);
    $castStop.on('click', onCastStopClick);

    $fullScreenButton.on('click', onFullScreenButtonClick);
    $statePickerLink.on('click', onStatePickerLink);
    $audioButtons.on('click', onAudioButtonsClick);
    $(window).on('resize', onWindowResize);

    if (IS_CAST_RECEIVER) {
        $welcomeScreen.hide();

        CHROMECAST_RECEIVER.setup();
        CHROMECAST_RECEIVER.onMessage('mute', onCastReceiverMute);
        CHROMECAST_RECEIVER.onMessage('state', onCastStateChange);

        setUpAudio(false);

        STACK.start();
    } else if (IS_FAKE_CASTER) {
        is_casting = true;
        state = 'TX';
        onCastStarted();
    }
    else if ($.cookie('reload')) {
        $.removeCookie('reload');
        $welcomeScreen.hide();
        setupUI();
        STACK.start();
    }
    else {
        // Prepare welcome screen
        $welcomeScreen.css('opacity', 1);
        $chromecastIndexHeader.css('opacity', 1);

        setupUI();
    }

    onWindowResize();
    setupStateTypeahead();
    checkBop();
    checkTimestamp();
    
    start_countdown();
}

var setupUI = function() {
    rotatePhone();
    checkTimestamp();

    // Geolocate
    if ($.cookie('state')) {
        state = $.cookie('state');
        showState();
    }

    if (typeof geoip2 == 'object' && !($.cookie('state'))) {
        geoip2.city(onLocateIP);
    }

    if (typeof geoip2 != 'object' && !($.cookie('state'))) {
        $('.typeahead').attr('placeholder', 'Select a state');
        $statePickerHed.text('We are having trouble determining your state.')
    }

    setUpAudio(true);
}

/*
 * Setup Chromecast if library is available.
 */
window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    $chromecastIndexHeader = $('.welcome').find('.cast-header');

    // Don't init sender if in receiver mode
    if (IS_CAST_RECEIVER) {
        return;
    }

    if (loaded) {
        CHROMECAST_SENDER.setup(onCastReady, onCastStarted, onCastStopped);
    	$chromecastIndexHeader.find('.cast-enabled').show();
    	$chromecastIndexHeader.find('.cast-disabled').hide();
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
    } else {
        $statePickerScreen.hide();
        $chromecastScreen.show();
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
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'chromecast-muted']);
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

    $stack.css({
        'height': new_height + 'px',
        'position': 'absolute',
        'top': padding + 'px'
    });

    var thisSlide = $('.slide');
    rotatePhone();
}

/*
 * Resize a slide to fit the viewport.
 */
var resizeSlide = function(slide) {
    var $w = $stack.width();
    var $h = $stack.height();
    var headerHeight = 0;

    slide.width($w);
    slide.height($h - headerHeight);

    slide.find('.slide-inner').width($w);
    slide.find('.slide-inner').height($h - headerHeight);
}

var rotatePhone = function() {
    if (Modernizr.touch && Modernizr.mq('(orientation: portrait)')) {
        $rotate.show();
        $('html').addClass('device-portrait');
		$stack.css({
			'top': '3vw'
		});
    }
    else {
        $rotate.hide();
        $('html').removeClass('device-portrait');
    }
}

/*
 * Begin chromecasting.
 */
var onCastStartClick = function(e) {
    e.preventDefault();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'chromecast-initiated']);

    CHROMECAST_SENDER.startCasting();
}

/*
 * Stop chromecasting.
 */
var onCastStopClick = function(e) {
    e.preventDefault();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'chromecast-stopped']);

    CHROMECAST_SENDER.stopCasting();
}

/*
 * Advance to state select screen.
 */
var onWelcomeButtonClick = function() {
    $welcomeScreen.hide();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'state-selected', state]);

    // TODO
    /*if (is_casting) {
        $chromecastScreen.show();
        resizeSlide($chromecastScreen);
        CHROMECAST_SENDER.sendMessage('state', state);
    } else {
        STACK.start();
    }*/
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
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'fullscreen']);
    var elem = document.getElementById("stack");

    var fullscreenElement = document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement;

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
 * Select the state.
 */

var getState = function($typeahead) {
    var input = $typeahead.typeahead('val');

    if (input) {
        var inverted = _.invert(APP_CONFIG.STATES);
        state = inverted[input]
    }

    $.cookie('state', state, { expires: 30 });
}

var showState = function() {
    console.log(state);
    console.log($stateName);
    $stateface.removeClass().addClass('stateface stateface-' + state.toLowerCase());
    $stateName.text(APP_CONFIG.STATES[state])
}

var switchState = function() {
    var $this = $(this);

    getState($this);
    showState();

    $stateface.css('opacity', 1);
    $stateName.css('opacity', 1);
    $typeahead.css('top', '0');
    $statePickerHed.text('You have selected');

    $this.typeahead('val', '')
    $this.typeahead('close');
    $this.blur();
}

var hideStateFace = function() {
    $stateface.css('opacity', 0);
    $stateName.css('opacity', 0);

    if ($stateWrapper.height() > 0 && $stateWrapper.width() > 0) {
        $typeahead.css('top', '-20vw');
    }
}

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'state-selected', state]);

    $statePickerScreen.hide();

    if (is_casting) {
        $chromecastScreen.show();
        CHROMECAST_SENDER.sendMessage('state', state);
    } else {
        STACK.start();
    }
}

/*
 * Reopen state selector.
 */
var onStatePickerLink = function() {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'switch-state-from-nav']);
    $stack.hide();
    $chromecastScreen.hide();
    $statePickerScreen.show();
}

/*
 * Set the geolocated state.
 */
var onLocateIP = function(response) {
    var place = response.most_specific_subdivision.iso_code;
    $('#option-' + place).prop('selected', true);
    state = place;
    $.cookie('state', state, { expires: 30 });

    showState();
}

var checkBop = function() {
    setInterval(function() {
        $bop.load('/bop.html');
    }, APP_CONFIG.CLIENT_BOP_INTERVAL * 1000);
}

var checkTimestamp = function() {
    setInterval(function() {
        $.ajax({
            'url': '/live-data/timestamp.json',
            'cache': false,
            'success': function(data) {
                var newTime = moment(data);

                if (reloadTimestamp.isBefore(newTime)) {
                    $.cookie('reload', true);
                    window.location.reload(true);
                }
            }
        })
    }, APP_CONFIG.RELOAD_CHECK_INTERVAL * 1000);
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

    $audioPlayer.bind($.jPlayer.event.stalled, onAudioFail);
    $audioPlayer.bind($.jPlayer.event.waiting, onAudioFail);
}

var onAudioButtonsClick = function() {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'audio-toggle']);
}

var onAudioFail = function() {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'audio-fail']);
}

/*
 * COUNTDOWN
 */
function start_countdown() {
	var page_width = $(window).width();
	var countdown_width = Math.floor(page_width * .03); // 3vw
	var countdown_outer_radius = Math.floor(countdown_width / 2);
	var countdown_inner_radius = Math.floor(countdown_outer_radius * .6);
	var countdown_status = 0;
	var countdown_limit = 20;
	var τ = 2 * Math.PI; // http://bl.ocks.org/mbostock/5100636
	
	console.log(countdown_width, countdown_outer_radius, countdown_inner_radius);
	
	$countdown.empty();
	
	var arc = d3.svg.arc()
		.innerRadius(countdown_inner_radius)
		.outerRadius(countdown_outer_radius)
		.startAngle(0);
	
	var svg = d3.select('#countdown')
		.append('svg')
			.attr('width', countdown_width)
			.attr('height', countdown_width)
		.append('g')
			.attr('transform', 'translate(' + countdown_width / 2 + ',' + countdown_width / 2 + ')');
	
	var background_arc = svg.append('path')
		.datum({endAngle: τ})
		.attr('class', 'countdown-background')
		.attr('d', arc);
	
	var foreground_arc = svg.append('path')
		.datum( { endAngle: (countdown_status / countdown_limit) * τ } )
		.attr('class', 'countdown-active')
		.attr('d', arc);
		
	var countdown_interval = setInterval(function() {
		foreground_arc.transition()
			.duration(750)
			.call(arcTween);
	}, 1000);

	function arcTween(transition) {
		var v = countdown_status + 1;
		if (v > countdown_limit) {
			v = 0;
		}
		countdown_status = v;
		var newAngle = (countdown_status / countdown_limit) * τ;
		
		transition.attrTween('d', function(d) {
			var interpolate = d3.interpolate(d.endAngle, newAngle);
			return function(t) {
				d.endAngle = interpolate(t);
				return arc(d);
			};
		});
	}
}

$(onDocumentReady);
