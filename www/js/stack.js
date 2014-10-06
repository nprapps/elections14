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

var $welcomeScreen = null;
var $welcomeButton = null;

var $statePickerScreen = null;
var $statePickerSubmitButton = null;
var $statePickerForm = null;

var stack = [];
var nextStack = [];
var currentSlide = 0;
var isRotating = false;
var state = null;
var $audioPlayer = null;
var $stack = null;


var resizeSlide = function(slide) {
    var $w = $(window).width();
    var $h = $(window).height();
    slide.width($w);
    slide.height($h);
}

var rotateSlide = function() {
    console.log('Rotating to next slide');
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

    if (stack[currentSlide]['slug'] === 'state') {
        slide_path = 'slides/state-' + state + '.html';
    } else {
        slide_path = 'slides/' + stack[currentSlide]['slug'] + '.html';
    }

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + slide_path,
        success: function(data) {
            var $oldSlide = $('#stack').find('.slide');
            var $newSlide = $(data);

            $('#stack').append($newSlide);

            resizeSlide($newSlide)

            $oldSlide.fadeOut(function(){
                $(this).remove();
            });

            $newSlide.fadeIn(function(){
                console.log('Slide rotation complete');
                setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
            });
        }
    });
}

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

var onWelcomeButtonClick = function() {
    $welcomeScreen.hide();
    $statePickerScreen.show();
}

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    state = $('.state-selector').val();
    $.cookie('state', state);

	$statePickerScreen.hide();
    $stack.show();

    getStack();
}


var setUpAudio = function() {
    $audioPlayer.jPlayer({
        ready: function () {
            $(this).jPlayer('setMedia', {
                mp3: 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3'
            }).jPlayer('pause');
        },
        swfPath: 'js/lib',
        supplied: 'mp3',
        loop: false,
    });
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


$(document).ready(function() {
    $welcomeScreen = $('.welcome');
    $welcomeButton = $('.welcome-button')

    $audioPlayer = $('#pop-audio');
    $statePickerScreen = $('.state-picker');
    $welcomeSubmitButton = $('.state-picker-submit');
    $statePickerForm  = $('form.state-picker-form');
    $stack = $('.stack');

    $(window).resize(function() {
        var thisSlide = $('#stack .slide');
        resizeSlide(thisSlide);
    });

    $welcomeButton.on('click', onWelcomeButtonClick);
    $statePickerForm.submit(onStatePickerSubmit);

    setUpAudio();

    $('.state-search .typeahead').typeahead({
        hint: true,
        highlight: true,
        minLength: 1
    },
    {
        name: 'states',
        displayKey: 'value',
        source: substringMatcher(states)
    });
});
