var STACK = (function () {
    var obj = {};

    var _stack = [];
    var _nextStack = null;
    var _currentSlide = 0;

    var _stackTimer = null;
    var _rotateTimer = null;
    var _mouseMoveTimer = null;

    var _stackRequest = null;
    var _rotateRequest = null;

    /*
     * Setup the stack display.
     */
    obj.start = function() {
        $stack.show();

        $('body').on('mousemove', onMoveMouse);
        $headerControls.hover(onControlsHover, offControlsHover);

        updateStack();
    }

    /*
     * Stop running the stack.
     */
    obj.stop = function() {
        if (_stackTimer) {
            clearTimeout(_stackTimer);
            _stackTimer = null;
        }

        if (_stackRequest) {
            _stackRequest.abort();
            _stackRequest = null;
        }

        if (_rotateTimer) {
            clearTimeout(_rotateTimer);
            _rotateTimer = null;
        }

        if (_rotateRequest) {
            _rotateRequest.abort();
            _rotateRequest = null;
        }

        if (_mouseMoveTimer) {
            clearTimeout(_mouseMoveTimer);
            _mouseMoveTimer = null;
        }

        $audioPlayer.jPlayer('pause');

        $stack.hide();
    }

    /*
     * Show the header.
     */
    var onMoveMouse = function() {
        if (!($('body').data('mouse-moving'))) {
            $header.fadeOut(200, function() {
                $('body').data('mouse-moving', true);
                $headerControls.fadeIn(200);
            });

        }

        if (_mouseMoveTimer) {
            clearTimeout(_mouseMoveTimer);
        }

        _mouseMoveTimer = setTimeout(onEndMouse, 400);
    }

    /*
     * Hide the header.
     */
    var onEndMouse = function() {

        if (!($headerControls.data('hover'))) {
            $headerControls.fadeOut(200, function() {
                $header.fadeIn(200, function() {
                    $('body').data('mouse-moving', false);
                });
            });
        }
    }


    /*
     * Rotate to the next slide in the stack.
     */
    var rotateSlide = function() {
        _currentSlide += 1;

        if (_currentSlide >= _stack.length) {
            if (_nextStack.length > 0) {
                _stack = _nextStack;
                _nextStack = [];
            }

            _currentSlide = 0;
        }

        var slug = _stack[_currentSlide]['slug'];
        var timeOnScreen = _stack[_currentSlide]['time_on_screen'];

        if (slug === 'state-senate') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide();
                return;
            }

            slide_path = 'slides/state-senate-' + state + '.html';
        }
        else if (slug === 'state-house-1') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide();
                return;
            }

            slide_path = 'slides/state-house-' + state + '-' + '1.html';
        }
        else if (slug === 'state-house-2') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide();
                return;
            }

            // Not a paginated state, skip page two
            if (APP_CONFIG.PAGINATED_STATES.indexOf(state) < 0) {
                rotateSlide();
                return;
            }

            slide_path = 'slides/state-house-' + state + '-' + '2.html';
        }
        else {
            slide_path = 'slides/' + slug + '.html';
        }

        console.log('Rotating to next slide:', slide_path);

        _rotateRequest = $.ajax({
            url: slide_path,
            success: function(data) {
                var $oldSlide = $stack.find('.slide');
                var $newSlide = $(data);

                if ($oldSlide.length > 0) {
                    $oldSlide.fadeOut(800, function() {
                        $(this).remove();
                        $stack.append($newSlide);
                        resizeSlide($newSlide)

                        if ($newSlide.find('.leaderboard').length > 0) {
                            $header.find('.leaderboard').fadeOut();
                        }
                        else {
                            $header.find('.leaderboard').fadeIn();
                        }

                        $newSlide.fadeIn(800, function(){
                            _rotateTimer = setTimeout(rotateSlide, timeOnScreen * 1000);
                        });
                    });
                } else {
                    $stack.append($newSlide);
                    resizeSlide($newSlide);

                    if ($newSlide.find('.results-header').length > 0) {
                        $header.find('.leaderboard').fadeOut();
                    }
                    else {
                        $header.find('.leaderboard').fadeIn();
                    }

                    $newSlide.fadeIn(800, function(){
                        _rotateTimer = setTimeout(rotateSlide, timeOnScreen * 1000);
                    });
                }
            }
        });
    }

    /*
     * Update the slide stack.
     */
    function updateStack() {
        _stackRequest = $.ajax({
            url: 'live-data/stack.json',
            dataType: 'json',
            success: function(data) {
                _nextStack = data;

                if (!_rotateTimer) {
                    rotateSlide();
                }

                _stackTimer = setTimeout(updateStack, APP_CONFIG.STACK_UPDATE_INTERVAL * 1000);
            }
        });
    }

    return obj;
}());
