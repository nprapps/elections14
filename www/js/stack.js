var slideHistory = [];

var rotateSlide = function(url) {
    $.ajax({
        url: url,
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
        url: '/stack.json',
        dataType: 'json',
        success: function(data) {
            rotateSlide(data.next);
        }
    });
}

var loadQuestion = function() {
    $.getJSON('../live-data/current-question.json', function(data) {
        $(".question").html(JST.question(data));

        // TODO: send data to remote
    });
}

$(function() {
    getSlide();
});