// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;
var $rotate = null;

var $countdownScreen = null;
var $counter = null;

var $stateface = null;
var $stateName = null;
var $statePicker = null;

var $chromecastScreen = null;
var $chromecastIndexHeader = null;
var $castStart = null;
var $castStop = null;

var $header = null;
var $headerControls = null;
var $chromecastButton = null;
var $audioPlayer = null;
var $bop = null;
var $stack = null;
var $audioButtons = null;
var $slide_countdown = null;
var $desktopOnlyLeftRight = null;
var $slideControls = null;
var $controlsWrapper = null;
var $controlsToggle = null;
var $castControls = null;
var $closeControlsLink = null;
var $changeState = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);
var IS_FAKE_CASTER = (window.location.search.indexOf('fakecast') >= 0);
var SKIP_COUNTDOWN = (window.location.search.indexOf('skipcountdown') >= 0);
var NO_AUDIO = (window.location.search.indexOf('noaudio') >= 0);
var IS_TOUCH = Modernizr.touch;
var reloadTimestamp = null;

var state = null;
var is_casting = false;
var countdown = 5 + 1;
var welcome_greeting_counter = 0;
var welcome_greeting_timer = null;
var inTransition = null;

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
var hasTrackedMobileControls = null;

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

    $stateface = $('.stateface');
    $stateName = $('.state-name');
    $statePicker = $('.state-picker');

    $chromecastScreen = $('.cast-controls');
    $chromecastIndexHeader = $welcomeScreen.find('.cast-header');
    $castStart = $('.cast-start');
    $castStop = $('.cast-stop');

    $audioPlayer = $('#pop-audio');
    $fullscreenStart = $('.fullscreen .start');
    $fullscreenStop = $('.fullscreen .stop');
    $chromecastButton = $('.chromecast');
    $bop = $('.leaderboard');
    $stack = $('#stack');
    $header = $('.index');
    $headerControls = $('.header-controls');
    $desktopOnlyLeftRight = $('.nav .slide-nav');
    $slideControls = $('.slide-nav .nav-btn');
    $controlsWrapper = $('.controls-wrapper');
    $controlsToggle = $('.js-toggle-controls');
    $castControls = $('.cast-controls');
    $closeControlsLink = $('.close-link');
    $slide_countdown = $stack.find('.slide-countdown');
    $audioPlay = $('.controls .play');
    $audioPause = $('.controls .pause');
    $changeState = $('.controls .change-state');

    reloadTimestamp = moment();

    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);

    $castStart.on('click', onCastStartClick);
    $castStop.on('click', onCastStopClick);
    $fullscreenStart.on('click', onFullscreenButtonClick);
    $fullscreenStop.on('click', onFullscreenButtonClick);

    $audioPlay.on('click', onAudioPlayClick);
    $audioPause.on('click', onAudioPauseClick);
    $slideControls.on('click', onSlideControlClick);
    if (!IS_TOUCH) {    
        $controlsToggle.on('click', onControlsToggleClick);
    }
    else {
        $stack.on('click', onStackTap);
        $closeControlsLink.on('click', onCloseControlsLink);
    }
    $changeState.on('click', onChangeStateClick);
    $statePicker.on('change', onStatePickerChange);

    $body.on('keydown', onKeyboard);
    $(window).on('resize', onWindowResize);

    STACK.setupAudio();

    if (IS_CAST_RECEIVER) {
        $controlsToggle.hide();
        $slide_countdown.hide();
        $slideControls.hide();
        $welcomeScreen.hide();

        CHROMECAST_RECEIVER.setup();
        CHROMECAST_RECEIVER.onMessage('mute', onCastReceiverMute);
        CHROMECAST_RECEIVER.onMessage('state', onCastStateChange);
        CHROMECAST_RECEIVER.onMessage('slide-change', onCastReceiverSlideChange);

        STACK.start();
        $desktopOnlyLeftRight.hide();

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
        $welcomeScreen.velocity('fadeIn');
        $chromecastIndexHeader.css('opacity', 1);

        setupUI();
    }

    onWindowResize();
    checkBop();
    checkTimestamp();

    create_slide_countdown();
}

var setupUI = function() {
    checkTimestamp();

    if (IS_TOUCH) {
        $desktopOnlyLeftRight.hide();
        $fullscreenStart.hide();
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
        // TODO: handle geoip load failure (e.g. adblocker)
    }

    welcomeOurGuests();
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
        window.clearTimeout(welcome_greeting_timer);
    } else {
        $chromecastIndexHeader.find('.cast-try-chrome').hide();
        $chromecastIndexHeader.find('.cast-get-extension').show();
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
    $stack.hide();
    $fullscreenStart.hide();
    $fullscreenStop.hide();
    $castStart.hide();
    STACK.stop();

    $chromecastScreen.show();

    is_casting = true;

    CHROMECAST_SENDER.sendMessage('state', state);
}

/*
 * A cast session stopped.
 */
var onCastStopped = function() {
    $chromecastScreen.hide();

    STACK.start();
    
    if (!IS_TOUCH) {
        $fullscreenStart.show();
        $fullscreenStop.show();
    }

    is_casting = false;
}

/*
 * Mute or unmute the receiver.
 */
var onCastReceiverMute = function(message) {
    if (message == 'true') {
        $audioPlayer.jPlayer('mute', true);
    } else {
        $audioPlayer.jPlayer('mute', false);
    }
}

/*
 * Back/next slide on the receiver.
 */
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
 * Resize current slide.
 */
var onWindowResize = function() {
    var width = $(window).width();
    var height = $(window).height();

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
    if (thisSlide.length > 0) {
        resizeSlide(thisSlide);
        rotatePhone();
    }
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
    if (IS_TOUCH && Modernizr.mq('(orientation: portrait)')) {
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

    window.clearTimeout(welcome_greeting_timer);

    // Mobile devices require a click to start audio
    if (IS_TOUCH) {
        STACK.startPrerollAudio();
    }

   showCountdown();
   rotatePhone();
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
		$counter.text('');
		setTimeout(hideCountdown, 200);
    }
}

var hideCountdown = function() {

    STACK.start();

    //hell yeah fade out
    var big = $countdownScreen.find('.countdown-arc svg');
    var little = $slide_countdown.find('svg');
    big_width = big.width()
    little_width = little.width()
    big_top = big.offset().top
    little_top = little.offset().top
    big_left = big.offset().left
    little_left = little.offset().left
    little_height = little.height()
    big.velocity({
        height: little_height,
        translateX: little_left - big_left - big_width/2 + little_width/2,
        translateY: little_top - big_top
        },
        {
            duration: 1000,
            display:'none',
            complete: function(){
                $countdownScreen.hide();
            }
        });
    $countdownScreen.find('h2, h3').velocity({opacity:0},{display: 'none'});
}

/*
 * Fullscreen the app.
 */
var onFullscreenButtonClick = function() {
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

        $fullscreenStart.show();
        $fullscreenStop.hide();
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

        $fullscreenStart.hide();
        $fullscreenStop.show();
    }
}

var onChangeStateClick = function(e) {
    e.preventDefault();

    $statePicker.show();
}
    
/*
 * Update the current state everywhere it is displayed.
 */
var showState = function() {
    $stateface.removeClass().addClass('stateface stateface-' + state.toLowerCase());
    $stateName.text(APP_CONFIG.STATES[state]);
    
    // Explicitly set state pickers because there could be more than one on the page
    $statePicker.val(state);
}

/*
 * Respond to selections from a state picker dropdown.
 */
var onStatePickerChange = function() {
    state = $(this).find('option:selected').val();

    showState();
    $.cookie('state', state, { expires: 30 });

    $stateface.css('opacity', 1);
    $stateName.css('opacity', 1);

    $statePicker.hide();

    if (is_casting) {
        CHROMECAST_SENDER.sendMessage('state', state);
    }
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'state-selected', state]);

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

/*
 * Fetch and display the latest balance of power.
 */
var checkBop = function() {
    setInterval(function() {
        $bop.load('/bop.html');
    }, APP_CONFIG.CLIENT_BOP_INTERVAL * 1000);
}

/*
 * Fetch the latest timestamp file and reload the if necessary.
 */
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
 * Unmute the audio.
 */
var onAudioPlayClick = function(e) {
    e.preventDefault();

    if (is_casting) {
        CHROMECAST_SENDER.sendMessage('mute', 'false');
    } else {
        $audioPlayer.jPlayer('mute', false);
    }

    $audioPlay.hide();
    $audioPause.show();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'audio-toggle']);
}

/*
 * Mute the audio.
 */
var onAudioPauseClick = function(e) {
    e.preventDefault();

    if (is_casting) {
        CHROMECAST_SENDER.sendMessage('mute', 'true');
    } else {
        $audioPlayer.jPlayer('mute', true);
    }

    $audioPause.hide();
    $audioPlay.show();

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


/*
 * Click left or right paddle
 */
var onSlideControlClick = function(e) {
    var $this = $(this);

    e.preventDefault();

    var direction = $this.data('slide');

    if (!(inTransition)) {
        $this.addClass('in-transition');

        // If casting we don't know when transition is complete
        // So just show highlight briefly
        if (is_casting) {
            setTimeout(function() {
                $slideControls.removeClass('in-transition');
            }, 1000);
        }
    }

    if (direction == "next") {

        if (is_casting) {
            CHROMECAST_SENDER.sendMessage('slide-change', 'next');
        } else {
            STACK.next();
        }
    }
    else if (direction == "previous") {
        if (is_casting) {
            CHROMECAST_SENDER.sendMessage('slide-change', 'prev');
        } else {
            STACK.previous();
        }
    }
}

/*
 * Click control/legend toggle
 */
var onControlsToggleClick = function(e) {
    e.preventDefault();

    $controlsWrapper.fadeToggle();
}

var onStackTap = function() {
    $castControls.show();
    $closeControlsLink.show();
    $stack.hide();
    
    if (!hasTrackedMobileControls) {
        _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'mobile-controls']);
        hasTrackedMobileControls = true;
    }
}

var onCloseControlsLink = function() {
    $castControls.hide();
    $stack.show();
}
/**
 * Catch keyboard events
 */
var onKeyboard = function(e) {
    if (!(hasTrackedKeyboardNav)) {
        _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'keyboard-nav']);
        hasTrackedKeyboardNav = true;
    }

    // Right arrow
    if (e.which == 39) {
        $('.slide-nav .nav-btn-right').eq(0).click();
    }

    // Left arrow
    if (e.which == 37) {
        $('.slide-nav .nav-btn-left').eq(0).click();
    }
    
    // Escape
    if (e.which == 27 && !IS_TOUCH && !is_casting) {
        $controlsToggle.click();
    }
}

var welcomeOurGuests = function(){
    greetings = $welcomeButton.find('span')
    var count = greetings.length;
    greetings.velocity({ opacity: 0 }, { display: "none" });
    $welcomeButton.find('span[data-greeting-index="' + welcome_greeting_counter % count + '"]').velocity({opacity:1}, { display: "inline" })
    welcome_greeting_counter++;
    welcome_greeting_timer = window.setTimeout(welcomeOurGuests, 5000);
}

$(onDocumentReady);
