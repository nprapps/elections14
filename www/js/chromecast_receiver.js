var CHROMECAST_RECEIVER = (function() {
    var obj = {};

    obj.setup = function() { 
        var castReceiverManager = cast.receiver.CastReceiverManager.getInstance();
        var customMessageBus = castReceiverManager.getCastMessageBus(APP_CONFIG.CHROMECAST_NAMESPACE);

        customMessageBus.onMessage = onReceiveMessage; 

        castReceiverManager.start();
    }

    var onReceiveMessage = function(e) {
        // TODO
    }

    return obj;
}());
