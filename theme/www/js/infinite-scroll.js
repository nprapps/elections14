var Tumblelog = {};

// AJAX
Tumblelog.Ajax = (function(url, callbackFunction) {
    this.bindFunction = function (caller, object) {
        return function() {
            return caller.apply(object, [object]);
        };
    };

    this.stateChange = function (object) {
        if (this.request.readyState==4) {
            this.callbackFunction(this.request.responseText);
        }
    };

    this.getRequest = function() {
        if (window.ActiveXObject)
            return new ActiveXObject('Microsoft.XMLHTTP');
        else if (window.XMLHttpRequest)
            return new XMLHttpRequest();
        return false;
    };

    this.postBody = (arguments[2] || "");
    this.callbackFunction=callbackFunction;
    this.url=url;
    this.request = this.getRequest();

    if(this.request) {
        var req = this.request;
        req.onreadystatechange = this.bindFunction(this.stateChange, this);

        if (this.postBody!=="") {
            req.open("POST", url, true);
            req.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            req.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
            req.setRequestHeader('Connection', 'close');
        } else {
            req.open("GET", url, true);
        }

        req.send(this.postBody);
    }
});

// Infinite Scroll
Tumblelog.Infinite = (function() {

    var _$window          = $(window);
    var _$posts           = $('#posts');
    var _trigger_post     = null;

    var _current_page     = CURRENT_PAGE;
    var _total_pages      = TOTAL_PAGES;
    var _url              = document.location.href;
    var _infinite_timeout = null;
    var _is_loading       = false;
    var _posts_loaded     = false;

    var _Ajax = Tumblelog.Ajax;

    function init() {
        set_trigger();
        enable_scroll();

        if (APP_CONFIG.TUMBLR_AUTO_REFRESH) {
            enableLiveBlog();
        }
    }

    function set_trigger () {
        var $all_posts = _$posts.find('article.post');

        if (!_posts_loaded) {
            _posts_loaded = $all_posts.length;
        }

        if (_posts_loaded >= 4) {
            _trigger_post = _$posts.find('article.post:eq(' + ($all_posts.length - 4) + ')').get(0);
        } else if (_posts_loaded >= 3) {
            _trigger_post = _$posts.find('article.post:eq(' + ($all_posts.length - 3) + ')').get(0);
        } else {
            _trigger_post = _$posts.find('article.post:last').get(0);
        }

    };

    function in_viewport (el) {
        if (el == null) return;
        var top = el.offsetTop;
        var height = el.offsetHeight;

        while (el.offsetParent) {
            el = el.offsetParent;
            top += el.offsetTop;
        }

        return (top < (window.pageYOffset + window.innerHeight));
    };

    function enable_scroll() {
        $('footer .pagination').hide();
        _$window.scroll(function(){
            clearTimeout(_infinite_timeout);
            infinite_timeout = setTimeout(infinite_scroll, 100);
        });
    }

    function disable_scroll() {
        clearTimeout(_infinite_timeout);
        $(window).unbind('scroll');
    }

    function infinite_scroll() {
        if (_is_loading) return;

        if (in_viewport(_trigger_post)) {
            load_more_posts(); // w00t
        }
    };

    function load_more_posts() {
        if (_is_loading) {
            return;
        }

        _is_loading = true;

        // Build URL
        if (_url.charAt(_url.length - 1) != '/') {
            _url += '/';
        }

        if (_current_page === 1){
            _url += 'page/1';
        }

        _current_page++;
        _url = _url.replace('page/' + (_current_page - 1), 'page/' + _current_page);

        console.log('load_more_posts', _url, _current_page);

        // Fetch
        _Ajax(_url, function(data) {
            var $data = $(data);

            var $new_posts = $('#posts article', data);
            var $current_posts = $('#posts');

            var posts_to_append = [];

            for (var i = 0; i < $new_posts.length; i++) {
                var found = $current_posts.find('#' + $new_posts.eq(i).attr('id'));

                if (found.length == 0) {
                    posts_to_append.push($new_posts[i]);
                }
            }

            // Insert new posts
            $current_posts.append(posts_to_append);


            $posts = $('#posts article');

            sizeVideoContainers($posts);
            $posts.fitVids({ customSelector: "video"});

            _posts_loaded = $('#posts article.post').length;

            if (_current_page < _total_pages) {
                set_trigger();
            } else {
                disable_scroll();
            }
                
            _is_loading = false;
        });

        // Stats
        if (typeof window._gaq != 'undefined') {
            _gaq.push(['_trackPageview', _url]);
        }
    }

    /* Live blog code */

    function enableLiveBlog() {
        setInterval(updateLiveBlog, APP_CONFIG.TUMBLR_REFRESH_INTERVAL * 1000);
    }

    function updateLiveBlog() {
        if (_is_loading) {
            return;
        }

        _is_loading = true;

        // reset the url
        var liveblog_url = document.location.href;
        
        if (liveblog_url.charAt(liveblog_url.length - 1) != '/') {
            liveblog_url += '/';
        }

        liveblog_url += 'page/1';

        _Ajax(liveblog_url, function(data) {
            var $data = $(data);

            // Update global state
            var new_total_pages = $(data).find('#total-pages').attr('data-total-pages');

            if (new_total_pages > _total_pages) {
                _current_page += new_total_pages - _total_pages;
                _total_pages = new_total_pages;
                console.log('New page', _current_page, _total_pages);
            }

            // Parse new posts
            var $new_posts = $data.find('#posts article');

            var $current_posts = $('#posts');
            var current_post_permalink = $current_posts.find('.permalink').attr('href');
            var posts_to_append = [];

            for (i = 0; i < $new_posts.length; i++) {
                var $loop_post = $new_posts.eq(i);
                var permalink = $loop_post.find('.permalink').attr('href');
                
                if (permalink == current_post_permalink) {
                    break;
                }

                posts_to_append.push($new_posts[i]);
            }

            console.log('updateLiveBlog', posts_to_append);

            // Insert new posts
            $current_posts.prepend(posts_to_append);

            $posts = $('#posts article');

            sizeVideoContainers($posts);
            $posts.fitVids({ customSelector: "video"});

            _posts_loaded = $('#posts article.post').length;

            if (_current_page < _total_pages) {
                set_trigger();
                _is_loading = false;
            } else {
                disable_scroll();
            }
        });
    }

    return {
        init: init
    };
});

$(function() {
    var scroller = new Tumblelog.Infinite;
    scroller.init();
});
