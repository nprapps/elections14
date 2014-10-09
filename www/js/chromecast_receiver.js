var initializeReceiver = function() { 
    // Only init receiver if in receiver mode
    if (!IS_CAST_RECEIVER) {
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
