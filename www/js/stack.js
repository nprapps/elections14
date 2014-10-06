var $welcomeScreen = null;
var $welcomeButton = null;

var $statePickerScreen = null;
var $statePickerSubmitButton = null;
var $statePickerForm = null;

var $header = null;
var $headerControls = null;
var $fullScreenButton = null;
var stack = [];
var nextStack = [];
var currentSlide = 0;
var isRotating = false;
var state = null;
var $audioPlayer = null;
var $stack = null;
var timer = null;


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
    resizeSlide($statePickerScreen);

    $('.state-selector').chosen({max_selected_options: 1});

}

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

var onMouseMove = function() {
    $header.hide();
    $headerControls.show();

    if (timer) {
        clearTimeout(timer);
    }
    timer = setTimeout(onMouseEnd, 200);
}

var onMouseEnd = function() {
    if (!($headerControls.data('hover'))) {
        console.log($headerControls.data('hover'));
        $header.show();
        $headerControls.hide();
    }
}

var onControlsHover = function() {
    $headerControls.data('hover', true);
    $header.hide();
    $headerControls.show();
}

var offControlsHover = function() {
    $headerControls.data('hover', false);
    $headerControls.hide();
    $header.show();
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

var onStatePickerSubmit = function(e) {
    e.preventDefault();

    state = $('.state-selector').val();
    $.cookie('state', state);

    $statePickerScreen.hide();
    $stack.show();

    getStack();

    $('body').on('mousemove', onMouseMove);
    $headerControls.hover(onControlsHover, offControlsHover);

}

$(document).ready(function() {
    $welcomeScreen = $('.welcome');
    resizeSlide($welcomeScreen);
    $welcomeButton = $('.welcome-button')

    $audioPlayer = $('#pop-audio');
    $statePickerScreen = $('.state-picker');
    $welcomeSubmitButton = $('.state-picker-submit');
    $statePickerForm  = $('form.state-picker-form');
    $stack = $('.stack');
    $header = $('.results-header');
    $headerControls = $('.header-controls');

    $fullScreenButton = $('.fullscreen p');

    $(window).resize(function() {
        var thisSlide = $('.slide');
        resizeSlide(thisSlide);
    });

    $welcomeButton.on('click', onWelcomeButtonClick);
    $statePickerForm.submit(onStatePickerSubmit);
    $fullScreenButton.on('click', onFullScreenButtonClick);

    setUpAudio();
});
