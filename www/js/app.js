// Global jQuery references
var $shareModal = null;
var $commentCount = null;

// Global state
var firstShareLoad = true;
var session = null;

/*
 * Run on page load.
 */
var onDocumentLoad = function(e) {
    // Cache jQuery references
    $shareModal = $('#share-modal');
    $commentCount = $('.comment-count');

    // Bind events
    $shareModal.on('shown.bs.modal', onShareModalShown);
    $shareModal.on('hidden.bs.modal', onShareModalHidden);
    $('.register').on('submit', registerDevice);
    $('.quiz').on('submit', submitAnswer);

    // configure ZeroClipboard on share panel
    ZeroClipboard.config({ swfPath: 'js/lib/ZeroClipboard.swf' });
    var clippy = new ZeroClipboard($(".clippy"));

    clippy.on('ready', function(readyEvent) {
        clippy.on('aftercopy', onClippyCopy);
    });

    getCommentCount(showCommentCount);
}

window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    if (loaded) {
        initializeCastApi();
    } else {
        console.log(errorInfo);
    }
}

/*
* CHROMECAST
*/

var initializeCastApi = function() {
    var sessionRequest = new chrome.cast.SessionRequest(APP_CONFIG.CHROMECAST_APP_ID);
    var apiConfig = new chrome.cast.ApiConfig(
        sessionRequest,
        sessionListener,
        receiverListener
    );

    chrome.cast.initialize(apiConfig, onInitSuccess, onError);
};

var sessionListener = function(e) {
    session = e;
    session.addMessageListener(APP_CONFIG.CHROMECAST_NAMESPACE, receiverMessage);
}

var receiverMessage = function(namespace, message) {
    console.log('Message from receiver:', message)
}

var receiverListener = function(e) {
    if (e === chrome.cast.ReceiverAvailability.AVAILABLE) {
        console.log('available');
    } else {
        console.log('not available');
    }
}

var onInitSuccess = function(e) {
    console.log('init success');
}

var onError = function(e) {
    console.log('init error:', e);
}

var onSendError = function(message) {
    console.log(message);
}

var onSendSuccess = function(message) {
    console.log(message);
}

var sendMessage = function(message) {
    console.log(session);
    session.sendMessage(APP_CONFIG.CHROMECAST_NAMESPACE, message, onSendSuccess, onSendError);
}

$('#cast').click(function(e) {
    e.preventDefault();

    chrome.cast.requestSession(onRequestSessionSuccess, onLaunchError);
});

var onRequestSessionSuccess = function(e) {
    session = e;
}

var onLaunchError = function(e) {
    console.log('launch error:', e);
}

/*
 * Display the comment count.
 */
var showCommentCount = function(count) {
    $commentCount.text(count);

    if (count > 0) {
        $commentCount.addClass('has-comments');
    }

    if (count > 1) {
        $commentCount.next('.comment-label').text('Comments');
    }
}

/*
 * Share modal opened.
 */
var onShareModalShown = function(e) {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'open-share-discuss']);

    if (firstShareLoad) {
        loadComments();

        firstShareLoad = false;
    }
}

/*
 * Share modal closed.
 */
var onShareModalHidden = function(e) {
    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'close-share-discuss']);
}

/*
 * Text copied to clipboard.
 */
var onClippyCopy = function(e) {
    alert('Copied to your clipboard!');

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, 'summary-copied']);
}

$(onDocumentLoad);
