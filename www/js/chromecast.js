window.onload = function() {
    var castReceiverManager = cast.receiver.CastReceiverManager.getInstance();
    var customMessageBus = castReceiverManager.getCastMessageBus(APP_CONFIG.CHROMECAST_NAMESPACE);

    customMessageBus.onMessage = function(e) {
        if (e.data == 'showQuestionOne') {
            showQuestionOne();
        }

        else if (e.data.startsWith('highlightAnswer')) {
            highlightAnswer(e.data)
        }
    }

    if (typeof String.prototype.startsWith != 'function') {
      String.prototype.startsWith = function (str){
        return this.slice(0, str.length) == str;
      };
    }

    var showQuestionOne = function() {
        $('.register').fadeOut();
        $('.quiz').fadeIn();
    }

    var highlightAnswer = function(message) {
        var answer = message.substr(message.length - 1)

        $('.answered').text('You answered ' + answer + '.');
    }

    castReceiverManager.start();
}