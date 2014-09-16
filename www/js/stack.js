var slideHistory = [];

var rotateSlide = function(url) {
  $.ajax({
    url: APP_CONFIG.S3_BASE_URL + url,
    success: function(data) {
      var $oldSlide = $('#stack').find('.slide');
      var $newSlide = $(data);
      $oldSlide.fadeOut();
      $('#stack').append($newSlide);

      $oldSlide.fadeOut(function(){
        $(this).remove();
      });
      $newSlide.fadeIn(function(){
        setTimeout(getSlide, 5000);
      });
      console.log('slides seen so far', slideHistory);
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
