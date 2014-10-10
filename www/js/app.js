// Global jQuery references
var $welcomeScreen = null;
var $welcomeButton = null;
var $cast = null;

var $statePickerScreen = null;
var $statePickerSubmitButton = null;
var $statePickerForm = null;
var $stateface = null;
var $stateName = null;
var $typeahead = null;

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

var states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California',
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
    $cast = $('.cast');

    $statePickerForm  = $('form.state-picker-form');
    $statePickerScreen = $('.state-picker');
    $statePickerLink = $ ('.state-picker-link');
    $stateface = $('.stateface');
    $stateName = $('.state-name');

    $audioPlayer = $('#pop-audio');
    $fullScreenButton = $('.fullscreen p');
    $stack = $('.stack');
    $header = $('.results-header');
    $headerControls = $('.header-controls');
    $shareModal = $('#share-modal');
    $commentCount = $('.comment-count');

    $('body').css('opacity', 1);

    // Bind events
    $welcomeButton.on('click', onWelcomeButtonClick);
    $cast.click('click', onCastClick);

    $statePickerForm.submit(onStatePickerSubmit);

    $fullScreenButton.on('click', onFullScreenButtonClick);
    $statePickerLink.on('click', onStatePickerLink);
    $shareModal.on('shown.bs.modal', onShareModalShown);
    $shareModal.on('hidden.bs.modal', onShareModalHidden);
    $(window).on('resize', onWindowResize);

    if (IS_CAST_RECEIVER) {
        beginStack();
    } else {
        // Prepare welcome screen
        $welcomeScreen.show();
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

    $('.typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
    },
    {
        name: 'states',
        displayKey: 'value',
        source: substringMatcher(states)
    });

    $typeahead = $('.twitter-typeahead');

    $('.typeahead').on('typeahead:selected', switchState)
    $('.typeahead').on('typeahead:opened', hideStateFace)

}

var substringMatcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substrRegex;

    // an array that will be populated with substring matches
    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each(strs, function(i, str) {
      if (substrRegex.test(str)) {
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
    $('.typeahead').typeahead('val', '')
    $('.typeahead').typeahead('close');
    $('.typeahead').blur();
}

var hideStateFace = function() {
    $stateface.css('opacity', 0);
    $stateName.css('opacity', 0);

    $typeahead.css('top', '-23vw');
}

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    getState();

    if (!(state)) {
        alert("Please pick a state!");
        return false;
    }

    $.cookie('state', state);

    $statePickerLink.text(APP_CONFIG.STATES[state]);

    beginStack();
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
 * Setup the stack display.
 */
var beginStack = function() {
    $welcomeScreen.hide();
    $statePickerScreen.hide();
    $stack.show();

    getStack();

    $('body').on('mousemove', onMouseMove);
    $headerControls.hover(onControlsHover, offControlsHover);
    $audioPlayer.jPlayer('play');
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
        // If no state selected, skip to next
        if (!state) {
            rotateSlide();
            return;
        }
            
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
