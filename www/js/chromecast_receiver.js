var initializeReceiver = function() { 
    // Only init receiver if in receiver mode
    if (window.location.search.indexOf('chromecast') < 0) {
        return;
    }

    var castReceiverManager = cast.receiver.CastReceiverManager.getInstance();
    var customMessageBus = castReceiverManager.getCastMessageBus(APP_CONFIG.CHROMECAST_NAMESPACE);

    customMessageBus.onMessage = onReceiveMessage; 

    castReceiverManager.start();
}

var onReceiveMessage = function(e) {
    /*if (e.data == 'showQuestionOne') {
        showQuestionOne();
    }

    else if (e.data.startsWith('highlightAnswer')) {
        highlightAnswer(e.data)
    }*/
}

$(initializeReceiver);
