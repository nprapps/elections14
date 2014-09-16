// Global jQuery references
var $shareModal = null;
var $commentCount = null;

// Global state
var firstShareLoad = true;
var pollingInterval = 30000;
var session = null;

var user = null;
var station = null;
var table = null;


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

    AWS.config.update({accessKeyId: DYNAMODB_ACCESS_KEY_ID, secretAccessKey: DYNAMODB_SECRET_ACCESS_KEY});

    AWS.config.region = 'us-west-2';

    getCommentCount(showCommentCount);
    getUpdates();
    pollUpdates();
    initDynamoDB();
}

window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    if (loaded) {
        initializeCastApi();
    } else {
        console.log(errorInfo);
    }
}

/*
* AP DATA
*/

var pollUpdates = function() {
    setInterval(getUpdates, pollingInterval);
}

var getUpdates = function() {
    $.getJSON('../live-data/update.json', function(data) {
        _.each(data, function(race) {
            _.each(race, function(value, key) {
                $('[data-field="' + race.slug + '-' + key + '"]').text(value);
            });

            _.each(race.candidates, function(candidate) {
                _.each(candidate, function(value, key) {
                    $('[data-field="' + candidate.slug + '-' + key + '"]').text(value);
                });
            });
        });
    });
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
* DYNAMODB
*/

var initDynamoDB = function() {
    AWS.config.update({accessKeyId: DYNAMODB_ACCESS_KEY_ID, secretAccessKey: DYNAMODB_SECRET_ACCESS_KEY});

    AWS.config.region = 'us-west-2';

    table = new AWS.DynamoDB({params: {TableName: 'elections14-game'}});
}

var guid = function() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });
}

var registerDevice = function(e) {
    e.preventDefault();

    user = $('#username').val();
    station = $('#station').val();

    $('.register').fadeOut();
    $('.quiz').fadeIn();

    if (session) {
        sendMessage('showQuestionOne');
    }
    else {
        $('.question-text').show();
    }
}

var submitAnswer = function(e) {
    e.preventDefault();

    var timestamp = new Date().getTime();
    timestamp = timestamp.toString();
    var answer = $('input[name="answer"]:checked').val();

    var itemParams = {
        Item: {
            user_id: {
                S: guid()
            },
            timestamp: {
                S: timestamp
            },
            question: {
                N: '1'
            },
            answer: {
                S: answer
            },
            station: {
                S: station
            },
            user: {
                S: user
            }
        }
    };
    table.putItem(itemParams, function(err) {
        if (!err){
            if (session) {
                sendMessage('highlightAnswer:' + answer)
            }
        }
        else {
            console.log(err);
        }
    });
};

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