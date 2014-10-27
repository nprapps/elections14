var onDocumentReady = function() {
    $('.create-invitation').on('click', onNviteLinkClicked);
}

var onNviteLinkClicked = function(e) {
    e.preventDefault();

    _gaq.push(['_trackEvent', APP_CONFIG.PROJECT_SLUG, '']);

    var $this = $(this);
    
    setTimeout(function() {
        window.location = $this.attr('href');
    }, 500);
}

$(onDocumentReady);
