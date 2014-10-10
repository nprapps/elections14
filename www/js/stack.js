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
        $audioPlayer.jPlayer('play');

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
        $header.hide();
        $headerControls.show();

        if (_mouseMoveTimer) {
            clearTimeout(_mouseMoveTimer);
        }
        
        _mouseMoveTimer = setTimeout(onEndMouse, 500);
    }

    /*
     * Hide the header.
     */
    var onEndMouse = function() {
        if (!($headerControls.data('hover'))) {
            $header.show();
            $headerControls.hide();
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

        _rotateRequest = $.ajax({
            url: APP_CONFIG.S3_BASE_URL + '/' + slide_path,
            success: function(data) {
                var $oldSlide = $stack.find('.slide');
                var $newSlide = $(data);

                if ($oldSlide.length > 0) {
                    $oldSlide.fadeOut(800, function() {
                        $(this).remove();
                        $stack.append($newSlide);
                        resizeSlide($newSlide)
                        $newSlide.fadeIn(800, function(){
                            _rotateTimer = setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
                        });
                    });
                }

                else {
                    $stack.append($newSlide);
                    resizeSlide($newSlide)
                    $newSlide.fadeIn(800, function(){
                        _rotateTimer = setTimeout(rotateSlide, APP_CONFIG.SLIDE_ROTATE_INTERVAL * 1000);
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
            url: APP_CONFIG.S3_BASE_URL + '/live-data/stack.json',
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
