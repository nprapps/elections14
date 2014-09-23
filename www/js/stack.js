var lastSlidePath = null;

var resizeSlide = function(slide) {
    var $w = $(window).width();
    var $h = $(window).height();
    slide.width($w);
    slide.height($h);
}

var rotateSlide = function(url) {
    // Fix for out of sync server and client refreshes
    if (lastSlidePath == url) {
        setTimeout(getSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
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
                setTimeout(getSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
            });
        }
    });
}

var getSlide = function() {
  $.ajax({
    url: APP_CONFIG.S3_BASE_URL + '/' + APP_CONFIG.NEXT_SLIDE_FILENAME,
    dataType: 'json',
    success: function(data) {
        rotateSlide(data.next);
    }
  });
}

$(document).ready(function() {
    getSlide();
    $(window).resize(function() {
        var thisSlide = $('#stack .slide');
        resizeSlide(thisSlide);
    })
});