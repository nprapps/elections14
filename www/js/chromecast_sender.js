// Global state
var session = null;

window['__onGCastApiAvailable'] = function(loaded, errorInfo) {
    // Don't init sender if in receiver mode
    if (window.location.search.indexOf('chromecast') >= 0) {
        return;
    }

    if (loaded) {
        initializeCastApi();
    } else {
        console.log(errorInfo);
    }
}

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

var onRequestSessionSuccess = function(e) {
    session = e;
}

var onLaunchError = function(e) {
    console.log('launch error:', e);
}

var beginCasting = function() {
    console.log(1);
    chrome.cast.requestSession(onRequestSessionSuccess, onLaunchError);
}
