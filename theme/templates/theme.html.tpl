<!DOCTYPE html>
<html class="no-js">
    <head>
        <title>{Title}{block:SearchPage} ({lang:Search results for SearchQuery}){/block:SearchPage}{block:PermalinkPage}{block:PostSummary}  {PostSummary}{/block:PostSummary}{/block:PermalinkPage} : NPR</title>

        <meta charset="utf-8">
        <meta name="description" content="{block:IndexPage}{block:Description}{MetaDescription}{/block:Description}{/block:IndexPage}{block:PermalinkPage}{block:PostSummary}{PostSummary}{/block:PostSummary}{/block:PermalinkPage}" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0" />

        <meta name="font:Body" content="'Helvetica Neue', Helvetica, Arial, sans-serif"/>

        <!-- Appearance option -->
        <meta name="if:Two column posts" content="1"/>
        <meta name="if:Show blog title" content="1"/>
        <meta name="if:Show blog description" content="1"/>
        <meta name="if:Show profile photo" content="0"/>
        <meta name="if:Use endless scrolling" content="1"/>
        <meta name="if:Use larger font for quotes" content="0"/>
        <meta name="if:Show image shadows" content="1"/>
        <meta name="if:Show post notes" content="1"/>
        <meta name="if:Show copyright in footer" content="0"/>
        <meta name="text:Disqus Shortname" content="" />

        <link rel="shortcut icon" href="http://www.npr.org/favicon.ico" />
        <link rel="alternate" type="application/rss+xml" title="RSS" href="{RSS}"/>

        <!-- Font loader -->
        <script src="//ajax.googleapis.com/ajax/libs/webfont/1.4.10/webfont.js"></script>
        <script>
            WebFont.load({
                 custom: {
                     families: [
                         'Gotham SSm:n4,n7'
                     ],
                     urls: [
                         'http://s.npr.org/templates/css/fonts/GothamSSm.css'
                     ]
                 },
                 timeout: 10000
             });
        </script>

         <!-- CSS -->
        {{ CSS.push('less/app.less') }}
        {% block extra_css %}{% endblock extra_css %}
        {{ CSS.render('css/app.min.css') }}

        <!-- GOOGLE ANALYTICS -->
         <script>
             (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
             (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
             m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
             })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

             ga('create', 'UA-5828686-63', 'tumblr.com');
             ga('send', 'pageview');
         </script>

        <meta name="twitter:card" content="summary">
        <meta property="og:title" content="{Title}" />
        <meta property="og:url" content="{{ copy.og_url }}" />
        <meta property="og:type" content="article" />
        <meta property="og:description" content="{{ copy.og_description }}" />
        <meta property="og:image" content="{{ copy.og_image }}" />
        <meta property="og:site_name" content="NPR.org" />
        <meta property="fb:app_id" content="138837436154588" />

    </head>
    <body class="{block:IndexPage}index-page{/block:IndexPage}{block:PermalinkPage}permalink-page{/block:PermalinkPage}">

        <div id="container" class="group container">
            <div class="row">
                <header>
                    <div id="blog_info">
                        <div class="fix-wrap">
                            <h2 class="npr"><a href="http://npr.org"><img src="http://media.npr.org/chrome/news/nprlogo_138x46.gif" alt="NPR" /></a></h2>
                            {block:IfShowBlogTitle}
                            <h1><a href="/">
                                {{ static(file_path='social_media_desk_lg.svg', classes='img-responsive hidden-xs hidden-sm', alt="header") }}
                                {{ static(file_path='social_media_desk.svg', classes='img-responsive visible-xs visible-sm', alt="header") }}
                            </a></h1>
                            {/block:IfShowBlogTitle}
                            <p>{Description}</p>
                        </div>
                    </div>
                </header>

                <section id="post-wrap">

                    {block:TagPage}<h2 class="tag-header">{Tag}</h2>{/block:TagPage}

                    <div id="posts">
                        <!-- START POSTS -->
                        {block:Posts}
                        <article class="post {TagsAsClasses} {block:Text}text{/block:Text}{block:Quote}quote{/block:Quote}{block:Link}link{/block:Link}{block:Video}video{/block:Video}{block:Audio}audio{/block:Audio}{block:Photo}photo{/block:Photo}{block:Photoset}photoset{/block:Photoset}{block:Panorama}panorama{/block:Panorama}{block:Chat}chat{/block:Chat}{block:Answer}answer{/block:Answer}">

                            <div class="row">
                            {block:Text}
                                {block:Title}
                                    {block:IndexPage}
                                    <a href="{Permalink}" class="permalink">
                                    {/block:IndexPage}
                                    <h3>{Title}</h3>
                                    {block:IndexPage}
                                    </a>
                                    {/block:IndexPage}

                                {/block:Title}
                                <div class="text-wrapper">
                                    {Body}
                                </div>
                            {/block:Text}
                            {block:Quote}
                                <div class="quote-wrapper">
                                    <blockquote class="words {Length}">&#8220;{Quote}&#8221;</blockquote>
                                    {block:Source}<p class="source">&mdash; {Source}</p>{/block:Source}
                                </div>
                            {/block:Quote}
                            {block:Link}
                                <h3><a href="{URL}" {Target}>{Name} <i class="icon icon-external-link"></i></a></h3>
                                <div class="caption">{block:Description}{Description}{/block:Description}</div>
                            {/block:Link}
                            {block:Video}
                                <div class="video-wrapper">
                                    <div class="video-container">
                                        {VideoEmbed-700}
                                    </div>
                                </div>
                                {block:Caption}<div class="caption">{Caption}</div>{/block:Caption}
                            {/block:Video}
                            {block:Audio}
                                {block:AlbumArt}<img src="{AlbumArtURL}" alt="">{/block:AlbumArt}
                                {AudioPlayerGrey}
                                {block:Caption}<div class="caption">{Caption}</div>{/block:Caption}
                            {/block:Audio}
                            {block:Photo}
                                    {LinkOpenTag}<img src="{PhotoURL-HighRes}" class="img-responsive" alt="{PhotoAlt}"/>{LinkCloseTag}
                                    {block:Caption}<div class="caption">{Caption}</div>{/block:Caption}
                            {/block:Photo}

                            {block:Photoset}
                                <div class="photoset-500">{Photoset-700}</div>
                                <div class="photoset-250">{Photoset-250}</div>
                                {block:Caption}<div class="caption">{Caption}</div>{/block:Caption}
                            {/block:Photoset}

                            {block:Panorama}
                                {LinkOpenTag}<img src="{PhotoURL-Panorama}" class="img-responsive" alt="{PhotoAlt}" />{LinkCloseTag}
                                {block:Caption}<div class="caption">{Caption}</div>{/block:Caption}
                            {/block:Panorama}

                            {block:Chat}
                                {block:Title}<h3>{Title}</h3>{/block:Title}
                                <ul class="conversation">
                                    {block:Lines}
                                    <li class="line {Alt}">
                                        {block:Label}<span class="person">{Label}</span>{/block:Label}
                                        <span class="person-said">{Line}</span>
                                    </li>
                                    {/block:Lines}
                                </ul>
                            {/block:Chat}
                            {block:Answer}
                                <div class="qa-asker">
                                    <img src="{AskerPortraitURL-40}">
                                    {Asker} asks:
                                </div>
                                <div class="qa-question">{Question}</div>
                                <div class="qa-response">{Answer}</div>
                            {/block:Answer}

                            <div class="post-meta">

                            {block:IndexPage}
                                <p class="pubdate"><a href="{Permalink}" class="permalink">{block:Date}{Month} {DayOfMonth}, {Year}{/block:Date}</a></p>
                                <p class="note-count"><a href="{Permalink}" class="permalink"><i class="icon icon-comment"></i> {NoteCountWithLabel}</a></p>
                            {/block:IndexPage}
                            {block:PermalinkPage}
                                <p class="pubdate">{block:Date}{Month} {DayOfMonth}, {Year}{/block:Date}</p>
                            {/block:PermalinkPage}

                            {block:HasTags}
                                <div class="tags">
                                    {block:Tags}<a href="{TagURL}" class="tag">{Tag}<span class="triangle"></span></a>{/block:Tags}
                                </div>
                            {/block:HasTags}

                            </div>

                            <!--
                            <ul class="unstyled sharing-tools">
                                <li><a rel="external" href="http://twitter.com/share?text=Read this post from &ldquo;{Title}&rdquo;%3a&amp;url={Permalink}" alt="Share on Twitter" target="_blank" onclick="_gaq.push(['_trackEvent', 'Social', 'Click Twitter In Post', '{Title}']);" title="Share This Page On Twitter"><i class="icon icon-twitter"></i></a></li>
                                <li><a rel="external" href="https://www.facebook.com/dialog/feed?app_id=138837436154588&amp;link={Permalink}&picture={PhotoURL-HighRes}&name={Title}&redirect_uri={Permalink}" alt="Share on Facebook" target="_blank" onclick="_gaq.push(['_trackEvent', 'Social', 'Click Facebook In Post', 'Read this post from &ldquo;{Title}&rdquo;']);" title="Like This Page On Facebook"><i class="icon icon-facebook-sign"></i></a></li>
                            </ul>
                            -->
                            </div> <!-- end .row -->

                            {block:PermalinkPage}
                            {block:PostNotes}
                                <div class="post-notes">
                                    <h3>Notes</h3>
                                    {PostNotes}
                                </div>
                            {/block:PostNotes}
                            {/block:PermalinkPage}
                        </article>
                        {/block:Posts}
                        <!-- END POSTS -->
                    </div>


                    <footer id="footer">
                        {block:PermalinkPage}
                            <nav class="pagination-index">
                                <a href="/">See More Posts <i class="icon icon-chevron-sign-right"></i></a>
                            </nav>
                        {/block:PermalinkPage}

                        {block:Pagination}
                            <nav class="pagination">
                                <section class="buttons">
                                    {block:PreviousPage}<a href="{PreviousPage}" class="left">{lang:Previous page}<span class="arrow"></span></a>{/block:PreviousPage}
                                    {block:NextPage}<a href="{NextPage}" class="right">{lang:Next page}<span class="arrow"></span></a>{block:NextPage}
                                </section>
                                <section class="disabled buttons">
                                    <li class="left"><span class="arrow"></span></li>
                                    <li class="right"><span class="arrow"></span></li>
                                </section>
                                <section class="count">Page  {CurrentPage} / {TotalPages}</section>
                            </nav>
                        {/block:Pagination}
                    </footer>
                </section> <!-- #post-wrap -->
            </div>
        </div> <!-- #container -->


        {{ JS.push('js/lib/jquery.js') }}
        {{ JS.push('js/lib/jquery.fitvids.js') }}
        {{ JS.push('js/infinite-scroll.js') }}
        {{ JS.push('js/app.js') }}
        {{ JS.render('js/app-footer-index.min.js') }}

        <!-- CHARTBEAT -->
        <script type="text/javascript">
            var _sf_async_config={};
            /** CONFIGURATION START **/
            _sf_async_config.uid = 18888;
            _sf_async_config.domain = "npr.org";
            /** CONFIGURATION END **/
            (function(){
                function loadChartbeat() {
                    window._sf_endpt=(new Date()).getTime();
                    var e = document.createElement("script");
                    e.setAttribute("language", "javascript");
                    e.setAttribute("type", "text/javascript");
                    e.setAttribute("src",
                        (("https:" == document.location.protocol) ?
                         "https://a248.e.akamai.net/chartbeat.download.akamai.com/102508/" :
                         "http://static.chartbeat.com/") +
                        "js/chartbeat.js");
                    document.body.appendChild(e);
                }
                var oldonload = window.onload;
                window.onload = (typeof window.onload != "function") ?
                    loadChartbeat : function() { oldonload(); loadChartbeat(); };
            })();
        </script>

        <script>
            (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
            (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
            m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
            })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

ga('create', '{{ TUMBLR_GOOGLE_ANALYTICS.ACCOUNT_ID }}', 'tumblr.com');
            ga('send', 'pageview');
        </script>
    </body>
</html>