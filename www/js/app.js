// Global jQuery references
var $shareModal = null;
var $commentCount = null;

// Global state
var firstShareLoad = true;
var pollingInterval = 30000;

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

    // configure ZeroClipboard on share panel
    ZeroClipboard.config({ swfPath: 'js/lib/ZeroClipboard.swf' });
    var clippy = new ZeroClipboard($(".clippy"));

    clippy.on('ready', function(readyEvent) {
        clippy.on('aftercopy', onClippyCopy);
    });

    getCommentCount(showCommentCount);
    getUpdates();
    pollUpdates();
}

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
