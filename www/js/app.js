// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;

var $statePickerScreen = null;
var $statePickerSubmitButton = null;
var $statePickerForm = null;
var $stateface = null;

var $header = null;
var $headerControls = null;
var $fullScreenButton = null;
var $statePickerLink = null;
var $audioPlayer = null;
var $stack = null;

var $shareModal = null;
var $commentCount = null;

// Global state
var IS_CAST_RECEIVER = (window.location.search.indexOf('chromecast') >= 0);

var stack = [];
var nextStack = [];
var currentSlide = 0;
var isRotating = false;
var state = null;
var mouseMoveTimer = null;

var firstShareLoad = true;

/*
 * Run on page load.
 */
var onDocumentReady = function(e) {
    // Cache jQuery references
    $welcomeScreen = $('.welcome');
    $welcomeButton = $('.welcome-button')
    $welcomeSubmitButton = $('.state-picker-submit');
    $cast = $('#cast');

    $statePickerForm  = $('form.state-picker-form');
    $statePickerScreen = $('.state-picker');
    $statePickerLink = $ ('.state-picker-link');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen p');
    $stack = $('.stack');
    $header = $('.results-header');
    $headerControls = $('.header-controls');
    $shareModal = $('#share-modal');
    $commentCount = $('.comment-count');

    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);
    $cast.click('click', onCastClick);

    $statePickerForm.submit(onStatePickerSubmit);
    $stateface = $('.stateface');

    $fullScreenButton.on('click', onFullScreenButtonClick);
    $statePickerLink.on('click', onStatePickerLink);
    $shareModal.on('shown.bs.modal', onShareModalShown);
    $shareModal.on('hidden.bs.modal', onShareModalHidden);
    $(window).on('resize', onWindowResize);

    if (IS_CAST_RECEIVER) {
        $welcomeScreen.hide();
        $statePickerScreen.hide();
        state = 'TX';
        $stack.show();

        // TODO: eliminate duplication with onStatePickerLink
        getStack();

        $('body').on('mousemove', onMouseMove);
        $headerControls.hover(onControlsHover, offControlsHover);
        setUpAudio(false);
    } else {
        // Prepare welcome screen
        resizeSlide($welcomeScreen);

        // Configure share panel
        ZeroClipboard.config({ swfPath: 'js/lib/ZeroClipboard.swf' });
        var clippy = new ZeroClipboard($(".clippy"));

        clippy.on('ready', function(readyEvent) {
            clippy.on('aftercopy', onClippyCopy);
        });

        // Geolocate
        geoip2.city(onLocateIP);
        
        setUpAudio(true);
    }
}

/*
 * Resize current slide.
 */
var onWindowResize = function() {
    var thisSlide = $('.slide');
    resizeSlide(thisSlide);
}

/*
 * Begin chromecasting.
 */
var onCastClick = function(e) {
    e.preventDefault();

    beginCasting();
}

/*
 * Advance to state select screen.
 */
var onWelcomeButtonClick = function() {
    $welcomeScreen.hide();
    $statePickerScreen.show();
    resizeSlide($statePickerScreen);

    $('.state-selector').chosen({max_selected_options: 1});

    $('.state-selector').on('change', function(evt, params) {
        if (params['selected']) {
            var abbrev = params['selected'].toLowerCase();
            $stateface.removeClass();
            $stateface.addClass('stateface stateface-' + abbrev);
        }
    });
}

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
 * Show the header.
 */
var onMouseMove = function() {
    $header.hide();
    $headerControls.show();

    if (mouseMoveTimer) {
        clearTimeout(mouseMoveTimer);
    }
    mouseMoveTimer = setTimeout(onMouseEnd, 500);
}

/*
 * Hide the header.
 */
var onMouseEnd = function() {
    if (!($headerControls.data('hover'))) {
        $header.show();
        $headerControls.hide();
    }
}

/*
 * Enable header hover.
 */
var onControlsHover = function() {
    $headerControls.data('hover', true);
    $header.hide();
    $headerControls.show();
}

/*
 * Disable header hover.
 */
var offControlsHover = function() {
    $headerControls.data('hover', false);
    $headerControls.hide();
    $header.show();
}

/*
 * Select the state.
 */
var onStatePickerSubmit = function(e) {
    e.preventDefault();

    state = $('.state-selector').val();

    if (!(state)) {
        alert("Please pick a state!");
        return false;
    }

    $.cookie('state', state);

    $statePickerLink.text(APP_CONFIG.STATES[state]);

    $statePickerScreen.hide();
    $stack.show();

    getStack();

    $('body').on('mousemove', onMouseMove);
    $headerControls.hover(onControlsHover, offControlsHover);
    $audioPlayer.jPlayer("play");
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
    slide.width($w);
    slide.height($h);
}

/*
 * Rotate to the next slide in the stack.
 */
var rotateSlide = function() {
    isRotating = true;

    currentSlide += 1;

    if (currentSlide >= stack.length) {
        if (nextStack.length > 0) {
            console.log('Switching to new stack');
            stack = nextStack;
            nextStack = [];
        }

        currentSlide = 0;
    }

    var slug = stack[currentSlide]['slug'];

    if (slug === 'state') {
        slide_path = 'slides/state-' + state + '.html';
    } else {
        slide_path = 'slides/' + slug + '.html';
    }
    
    console.log('Rotating to next slide:', slide_path);

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + slide_path,
        success: function(data) {
            var $oldSlide = $('#stack').find('.slide');
            var $newSlide = $(data);

            if ($oldSlide.length > 0) {
                $oldSlide.fadeOut(800, function() {
                    $(this).remove();
                    $('#stack').append($newSlide);
                    resizeSlide($newSlide)
                    $newSlide.fadeIn(800, function(){
                        console.log('Slide rotation complete');
                        setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
                    });
                });
            }

            else {
                $('#stack').append($newSlide);
                resizeSlide($newSlide)
                $newSlide.fadeIn(800, function(){
                    console.log('Slide rotation complete');
                    setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
                });
            }
        }
    });
}

/*
 * Update the slide stack.
 */
function getStack() {
    console.log('Updating the stack');

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/live-data/stack.json',
        dataType: 'json',
        success: function(data) {
            nextStack = data;

            console.log('Stack update complete');

            if (!isRotating) {
                rotateSlide();
            }

            setTimeout(getStack, APP_CONFIG.STACK_UPDATE_INTERVAL * 1000);
        }
    });
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
