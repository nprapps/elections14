// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;
var $rotate = null;

var $countdownScreen = null;
var $counter = null;

var $statePickerScreen = null;
var $statePickerForm = null;
var $stateWrapper = null;
var $stateface = null;
var $stateName = null;
var $typeahead = null;
var $statePickerHed = null;
var $statePickerLink = null;

var $chromecastScreen = null;
var $chromecastMute = null;
var $chromecastChangeState = null;
var $chromecastIndexHeader = null;
var $castStart = null;
var $castStop = null;
var $castPrev = null;
var $castNext = null;

var $header = null;
var $headerControls = null;
var $rightControls = null;
var $fullScreenButton = null;
var $statePickerLink = null;
var $chromecastButton = null;
var $audioPlayer = null;
var $bop = null;
var $stack = null;
var $audioButtons = null;
var $slide_countdown = null;
var $controlsWrapper = null;
var $controlsToggle = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);
var IS_FAKE_CASTER = (window.location.search.indexOf('fakecast') >= 0);
var SKIP_COUNTDOWN = (window.location.search.indexOf('skipcountdown') >= 0);
var reloadTimestamp = null;

var state = null;
var is_casting = false;
var countdown = 3 + 1;

var slide_countdown_arc = null;
var slide_countdown_svg = null;
var slide_countdown_background_arc = null;
var slide_countdown_foreground_arc = null;
var welcome_countdown_arc = null;
var welcome_countdown_svg = null;
var welcome_countdown_background_arc = null;
var welcome_countdown_foreground_arc = null;
var τ = 2 * Math.PI; // http://bl.ocks.org/mbostock/5100636

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

var hasTrackedNextSlide = null;
var hasTrackedPrevSlide = null;
var hasTrackedKeyboardNav = null;

/*
 * Run on page load.
 */
var onDocumentReady = function(e) {
    // Cache jQuery references
    $body = $('body');
    $welcomeScreen = $('.welcome');
    $welcomeButton = $('.js-go')
    $rotate = $('.rotate-phone-wrapper');

    $countdownScreen = $('.countdown');
    $counter = $('.counter');

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
    $castPrev = $('.cast-prev');
    $castNext = $('.cast-next');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen a');
    $chromecastButton = $('.chromecast');
    $bop = $('.leaderboard');
    $stack = $('#stack');
    $header = $('.index');
    $headerControls = $('.header-controls');
    $rightControls = $('.right-controls');
    $audioButtons = $('.jp-controls .nav-btn');
    $slideControls = $('.slide-nav .nav-btn');
    $controlsWrapper = $('.controls-wrapper');
    $controlsToggle = $('.js-toggle-controls');
    $slide_countdown = $stack.find('.slide-countdown');
    reloadTimestamp = moment();

    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);

    $statePickerForm.submit(onStatePickerSubmit);

    $chromecastMute.on('click', onCastMute);
    $chromecastChangeState.on('click', onStatePickerLink);
    $castStart.on('click', onCastStartClick);
    $castStop.on('click', onCastStopClick);
    $castPrev.on('click', onCastSlideControlClick);
    $castNext.on('click', onCastSlideControlClick);

    $fullScreenButton.on('click', onFullScreenButtonClick);
    $statePickerLink.on('click', onStatePickerLink);
    $audioButtons.on('click', onAudioButtonsClick);
    $slideControls.on('click', onSlideControlClick);
    $controlsToggle.on('click', onControlsToggleClick);
    $body.on('keydown', onKeyboard);
    $(window).on('resize', onWindowResize);

    if (IS_CAST_RECEIVER) {
        $welcomeScreen.hide();

        CHROMECAST_RECEIVER.setup();
        CHROMECAST_RECEIVER.onMessage('mute', onCastReceiverMute);
        CHROMECAST_RECEIVER.onMessage('state', onCastStateChange);
        CHROMECAST_RECEIVER.onMessage('slide-change', onCastReceiverSlideChange);

        STACK.start();
        $rightControls.hide();

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
    } else if (SKIP_COUNTDOWN) {
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

    create_slide_countdown();
}

var setupUI = function() {
    rotatePhone();
    checkTimestamp();

    if (Modernizr.touch) {
        $rightControls.hide();
    }

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
}

/*
 * Setup Chromecast if library is available.
 */
window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    $chromecastIndexHeader = $('.welcome').find('.cast-header');

    // Don't init sender if in receiver mode
    if (IS_CAST_RECEIVER || IS_FAKE_CASTER) {
        return;
    }

    if (loaded) {
        CHROMECAST_SENDER.setup(onCastReady, onCastStarted, onCastStopped);
    	$chromecastIndexHeader.find('.cast-enabled').show();
    	$chromecastIndexHeader.find('.cast-disabled').hide();
        $castStart.show();
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

var onCastReceiverSlideChange = function(message) {
    if (message == 'prev') {
        STACK.previous();
    }

    if (message == 'next') {
        STACK.next();
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

var onCastSlideControlClick = function(e) {
    e.preventDefault();

    if ($(this).hasClass('cast-prev')) {
        CHROMECAST_SENDER.sendMessage('slide-change', 'prev');
    }
    else if ($(this).hasClass('cast-next')) {
        CHROMECAST_SENDER.sendMessage('slide-change', 'next');
    }
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
        'width': width + 'px',
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

    $castStart.hide();
    $castStop.show();
}

/*
 * Stop chromecasting.
 */
var onCastStopClick = function(e) {
    e.preventDefault();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'chromecast-stopped']);

    CHROMECAST_SENDER.stopCasting();

    $castStop.hide();
    $castStart.show();
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

   showCountdown();
}

var showCountdown = function() {
    $countdownScreen.show();
    create_welcome_countdown();
    nextCountdown();
}

var nextCountdown = function() {
    countdown -= 1;

    if (countdown > 0) {
		$counter.text(countdown);
		setTimeout(nextCountdown, 1000);
    } else {
		$counter.text('Go!');
		setTimeout(hideCountdown, 1000);
    }
}

var hideCountdown = function() {
    $countdownScreen.hide();

    STACK.start();
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
        $fullScreenButton.find('span').text('Fullscreen');
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
        $fullScreenButton.find('span').text('Exit Fullscreen');
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
    $stateface.removeClass().addClass('stateface stateface-' + state.toLowerCase());
    $stateName.text(APP_CONFIG.STATES[state]);
    $statePickerLink.find('.state-name').text(state);
}

var switchState = function() {
    var $this = $(this);

    getState($this);
    showState();

    $stateface.css('opacity', 1);
    $stateName.css('opacity', 1);
    $typeahead.css('top', '0');
    $statePickerHed.text('You have selected').css('opacity', 1);;

    $this.typeahead('val', '')
    $this.typeahead('close');
    $this.blur();
}

var hideStateFace = function() {
    $stateface.css('opacity', 0);
    $stateName.css('opacity', 0);
    $statePickerHed.css('opacity', 0);

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
        $stack.show();
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

var onAudioButtonsClick = function() {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'audio-toggle']);
}

/*
 * COUNTDOWN
 */
function create_welcome_countdown() {
	var page_width = $(window).width();
//	var countdown_width = Math.floor(page_width * .22); // 22vw
	var countdown_width = 100;
	var countdown_outer_radius = Math.floor(countdown_width / 2);
	var countdown_inner_radius = Math.floor(countdown_outer_radius * .7);

	welcome_countdown_arc = d3.svg.arc()
		.innerRadius(countdown_inner_radius)
		.outerRadius(countdown_outer_radius)
		.startAngle(0);

	welcome_countdown_svg = d3.select('.countdown-arc')
		.append('svg')
			.attr('width', '100%')
			.attr('viewBox', '0 0 ' + countdown_width + ' ' + countdown_width)
//			.attr('width', countdown_width)
//			.attr('height', countdown_width)
		.append('g')
			.attr('transform', 'translate(' + countdown_width / 2 + ',' + countdown_width / 2 + ')');

	welcome_countdown_background_arc = welcome_countdown_svg.append('path')
		.datum({endAngle: τ})
		.attr('class', 'countdown-background')
		.attr('d', welcome_countdown_arc);

	welcome_countdown_foreground_arc = welcome_countdown_svg.append('path')
		.datum( { endAngle: 0 } )
		.attr('class', 'countdown-active')
		.attr('d', welcome_countdown_arc);

	start_arc_countdown('welcome_countdown', (countdown - 1));
}

function create_slide_countdown() {
	var page_width = $(window).width();
//	var countdown_width = Math.floor(page_width * .025); // 2.5vw
	var countdown_width = 100;
	var countdown_outer_radius = Math.floor(countdown_width / 2);
	var countdown_inner_radius = Math.floor(countdown_outer_radius * .6);

	slide_countdown_arc = d3.svg.arc()
		.innerRadius(countdown_inner_radius)
		.outerRadius(countdown_outer_radius)
		.startAngle(0);

	slide_countdown_svg = d3.select('#stack .slide-countdown')
		.append('svg')
			.attr('viewBox', '0 0 ' + countdown_width + ' ' + countdown_width)
//			.attr('width', countdown_width)
//			.attr('height', countdown_width)
		.append('g')
			.attr('transform', 'translate(' + countdown_width / 2 + ',' + countdown_width / 2 + ')');

	slide_countdown_background_arc = slide_countdown_svg.append('path')
		.datum({endAngle: τ})
		.attr('class', 'countdown-background')
		.attr('d', slide_countdown_arc);

	slide_countdown_foreground_arc = slide_countdown_svg.append('path')
		.datum( { endAngle: 0 } )
		.attr('class', 'countdown-active')
		.attr('d', slide_countdown_arc);
}

function start_arc_countdown(arc, duration) {
	var arc_start = 0;
	var arc_end = τ;
	var arc_foreground = eval(arc + '_foreground_arc');
	var arc_main = eval(arc + '_arc');

	arc_foreground.transition()
			.duration(1000)
				.ease('linear')
				.call(tween_slide_arc, arc_main, arc_start);
	arc_foreground.transition()
			.duration(duration * 1000)
				.ease('linear')
				.call(tween_slide_arc, arc_main, arc_end);
}

function cancel_arc_countdown(arc) {
    var arc_start = 0;
    var arc_end = τ;
    var arc_foreground = eval(arc + '_foreground_arc');
    var arc_main = eval(arc + '_arc');

    arc_foreground.transition()
            .duration(0)
                .call(tween_slide_arc, arc_main, arc_end);
    arc_foreground.transition()
            .duration(0)
                .call(tween_slide_arc, arc_main, arc_start);
}

function tween_slide_arc(transition, arc_main, end) {
	transition.attrTween('d', function(d) {
		var interpolate = d3.interpolate(d['endAngle'], end);
		return function(t) {
			d['endAngle'] = interpolate(t);
			return arc_main(d);
		};
	});
}


/**
 * Click left or right paddle
 */
var onSlideControlClick = function() {
    var direction = $(this).data('slide');
    if (direction == "next") {
        STACK.next($(this));
    }
    else if (direction == "previous") {
        STACK.previous($(this));
    }
}

/**
 * Click control/legend toggle
 */
var onControlsToggleClick = function() {
    $controlsWrapper.fadeToggle();
}

/**
 * Catch keyboard events
 */
var onKeyboard = function(e) {
    if (!(hasTrackedKeyboardNav)) {
        _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'keyboard-nav']);
        hasTrackedKeyboardNav = true;
    }
    if (e.which == 39) {
        if (is_casting) {
            CHROMECAST_SENDER.sendMessage('slide-change', 'next');
        }
        else {
            STACK.next($('.slide-nav .nav-btn-right'))
        }
    }
    if (e.which == 37) {
        if (is_casting) {
            CHROMECAST_SENDER.sendMessage('slide-change', 'prev');
        }
        else {
            STACK.previous($('.slide-nav .nav-btn-left'))
        }
    }
}

$(onDocumentReady);
