var stack = [];
var nextStack = [];
var currentSlide = 0;
var isRotating = false;

var $audioPlayer = null;
var $welcomeScreen = null;
var $welcomeSubmitButton = null;
var $welcomeForm = null;
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
        slide_path = 'slides/state-' + $.cookie('state') + '.html';
    }
    else {
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

var onWelcomeFormSubmit = function(e) {
    e.preventDefault();

    var state = $('.state-selector').val();

    $.cookie('state', state);

	$welcomeScreen.hide();
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

$(document).ready(function() {
    $audioPlayer = $('#pop-audio');
    $welcomeScreen = $('.welcome');
    $welcomeSubmitButton = $('.welcome-submit');
    $welcomeForm = $('form.welcome-form');
    $stack = $('.stack');

    $(window).resize(function() {
        var thisSlide = $('#stack .slide');
        resizeSlide(thisSlide);
    });

    $welcomeForm.submit(onWelcomeFormSubmit);

    setUpAudio();
});
