var lastSlidePath = null;
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

var rotateSlide = function(url) {
    // Fix for out of sync server and client refreshes
    if (lastSlidePath == url) {
        setTimeout(getSlide, APP_CONFIG.CLIENT_SLIDE_ROTATE_INTERVAL * 1000);
        return;
    }

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + url,
        success: function(data) {
            lastSlidePath = url;

            var $oldSlide = $('#stack').find('.slide');
            var $newSlide = $(data);

            $('#stack').append($newSlide);

            resizeSlide($newSlide)

            $oldSlide.fadeOut(function(){
                $(this).remove();
            });

            $newSlide.fadeIn(function(){
                setTimeout(getSlide, APP_CONFIG.CLIENT_SLIDE_ROTATE_INTERVAL * 1000);
            });
        }
    });
}

var getSlide = function() {
    $welcomeScreen.hide();
    $stack.show();

    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + APP_CONFIG.NEXT_SLIDE_FILENAME,
        dataType: 'json',
        success: function(data) {
            rotateSlide(data.next);
        }
    });
}

var launchSlides = function(e) {
    e.preventDefault();

    getSlide();
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

    $welcomeForm.submit(launchSlides);

    setUpAudio();
});