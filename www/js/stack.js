var STACK = (function () {
    var obj = {};

    var _stack = [];
    var _nextStack = null;
    var _currentSlide = 0;
    var _timeOnScreen = null;
    var $newSlide = null;

    var _stackTimer = null;
    var _rotateTimer = null;
    var _mouseMoveTimer = null;

    var _stackRequest = null;
    var _rotateRequest = null;

    var _mouseMoving = false;
    var _hover = false;

    var _slideExitCallback = null;

    /*
     * Setup the stack display.
     */
    obj.start = function() {
        startPrerollAudio();

        $stack.show();

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

        $audioPlayer.jPlayer('pause');

        $stack.hide();
    }

    obj.setSlideExitCallback = function(cb) {
        _slideExitCallback = cb;
    }

    obj.next = function() {
        if (_rotateTimer) {
            clearTimeout(_rotateTimer);
            _rotateTimer = null;
        }
        rotateSlide();
    }

    obj.previous = function() {
        if (_rotateTimer) {
            clearTimeout(_rotateTimer);
            _rotateTimer = null;
        }
        rotateSlide('previous');
    }

    var startPrerollAudio = function() {
        $audioPlayer.jPlayer({
            ready: function () {
                $(this).jPlayer('setMedia', {
                    mp3: 'http://www.springfieldfiles.com/sounds/homer/goons.mp3'
                }).jPlayer('play');
            },
            ended: startLivestream,
            swfPath: 'js/lib',
            supplied: 'mp3',
            loop: false,
        });

        $audioPlayer.bind($.jPlayer.event.stalled, onAudioFail);
        $audioPlayer.bind($.jPlayer.event.waiting, onAudioFail);
    }

    var startLivestream = function() {
        $audioPlayer.jPlayer('setMedia', {
            mp3: 'http://nprdmp.ic.llnwd.net/stream/nprdmp_live01_mp3'
        }).jPlayer('play');
    }

    var onAudioFail = function() {
        _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'audio-fail']);
    }

    /*
     * Rotate to the next slide in the stack.
     */
    var rotateSlide = function(direction) {
        var increment = (direction == 'previous') ? -1 : 1;

        _currentSlide += increment;

        if (_currentSlide >= _stack.length) {
            if (_nextStack.length > 0) {
                _stack = _nextStack;
                _nextStack = [];
            }
            _currentSlide = 0;
        }
        else if (_currentSlide < 0) {
            _currentSlide = _stack.length - 1;
        }

        var slug = _stack[_currentSlide]['slug'];

        if (slug === 'state-senate-results') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide(direction);
                return;
            }

            // If we're tracking any races in this state
            if (APP_CONFIG.NO_GOVERNOR_OR_SENATE_RACES.indexOf(state) >= 0) {
                rotateSlide(direction);
                return;
            }

            slide_path = 'slides/state-senate-results-' + state + '.html';
        }
        else if (slug === 'state-house-results-1') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide(direction);
                return;
            }

            // If we're tracking any races in this state
            if (APP_CONFIG.NO_FEATURED_HOUSE_RACES.indexOf(state) >= 0) {
                rotateSlide(direction);
                return;
            }

            slide_path = 'slides/state-house-results-' + state + '-' + '1.html';
        }
        else if (slug === 'state-house-results-2') {
            // If no state selected, skip to next
            if (!state) {
                rotateSlide(direction);
                return;
            }

            // If we're tracking any races in this state
            if (APP_CONFIG.NO_FEATURED_HOUSE_RACES.indexOf(state) >= 0) {
                rotateSlide(direction);
                return;
            }

            // Not a paginated state, skip page two
            if (APP_CONFIG.PAGINATED_STATES.indexOf(state) < 0) {
                rotateSlide(direction);
                return;
            }

            slide_path = 'slides/state-house-results-' + state + '-' + '2.html';
        }
        else {
            slide_path = 'slides/' + slug + '.html';
        }

        console.log('Rotating to next slide:', slide_path);

        _rotateRequest = $.ajax({
            'url': slide_path,
            'cache': false,
            'success': _onSlideSuccess,
            'error': _onSlideError
        });
    }

    /*
     * Slide successfully downloaded.
     */
    var _onSlideSuccess = function(data) {
        var $oldSlide = $stack.find('.slide');
        $newSlide = $(data);

        _timeOnScreen = _stack[_currentSlide]['time_on_screen'];

        // update countdown spinner
        start_arc_countdown('slide_countdown', _timeOnScreen);

        if ($oldSlide.length > 0) {
            if (_slideExitCallback) {
                _slideExitCallback();

                _slideExitCallback = null;
            }
            if (IS_CAST_RECEIVER) {
                $oldSlide.hide();
                addNewSlide();
            }
            else {
                $oldSlide.fadeOut(800, addNewSlide);
            }

        } else {
            $stack.append($newSlide);
            resizeSlide($newSlide);

            if (($newSlide.find('.results-header').length > 0) || ($newSlide.find('.balance-of-power').length > 0)) {
                $header.find('.leaderboard').fadeOut();
            }
            else {
                $header.find('.leaderboard').fadeIn();
            }

            if (IS_CAST_RECEIVER) {
                $newSlide.show();
                setTimer();
            }
            else {
                $newSlide.fadeIn(800, setTimer);
            }
        }
    }

    var addNewSlide = function() {
        $(this).remove();
        $stack.append($newSlide);
        resizeSlide($newSlide)

        if (($newSlide.find('.leaderboard').length > 0)  || ($newSlide.find('.balance-of-power').length > 0)) {
            $header.find('.leaderboard').fadeOut();
        }
        else {
            $header.find('.leaderboard').fadeIn();
        }

        if (IS_CAST_RECEIVER) {
            $newSlide.show();
            setTimer();
        }
        else {
            $newSlide.fadeIn(800, setTimer);
        }
    }

    var setTimer = function() {
        _rotateTimer = setTimeout(rotateSlide, _timeOnScreen * 1000);
        $(this).find('a').on('click', onSlideAnchorClick);
    }

    /*
     * If a slide fails to load, rotate again.
     */
    var _onSlideError = function() {
        rotateSlide();
    }

    var onSlideAnchorClick = function() {
        _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'slide-link-click']);
    }

    /*
     * Update the slide stack.
     */
    var updateStack = function() {
        _stackRequest = $.ajax({
            'url': 'live-data/stack.json',
            'dataType': 'json',
            'cache': false,
            'success': function(data) {
                _nextStack = data;

                if (!_rotateTimer) {
                    rotateSlide();
                }

                _stackTimer = setTimeout(updateStack, APP_CONFIG.STACK_UPDATE_INTERVAL * 1000);
            },
            'error': function() {
                _stackTimer = setTimeout(updateStack, APP_CONFIG.STACK_UPDATE_INTERVAL * 1000);
            }
        });
    }

    return obj;
}());
