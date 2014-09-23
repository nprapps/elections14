var $w = $(window).width();
var $h = $(window).height();

var rotateSlide = function(url) {
    $.ajax({
        url: APP_CONFIG.S3_BASE_URL + '/' + url,
        success: function(data) {
            var $oldSlide = $('#stack').find('.slide');
            var $newSlide = $(data);

            $oldSlide.fadeOut();

            $('#stack').append($newSlide);

            $newSlide.width($w);
            $newSlide.height($h);

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

getSlide();
