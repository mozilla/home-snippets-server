/**
 * Tweaks for home page simulator
 */
var Mozilla_Home_Main = (function () {

    var $this = {

        snippets_update_url: '',

        init: function () {
            // HACK: browser/components/nsBrowserContentHandler.js:895
            // AboutHomeUtils.loadDefaultSearchEngine();
            localStorage["search-engine"] = '{"name":"Google","searchUrl":"http://www.google.com/search?q=_searchTerms_&ie=utf-8&oe=utf-8&aq=t&rls=org.mozilla:en-US:unofficial&client=firefox-a"}'
            return $this;
        },

        setSnippetUpdateUrl: function (url) {
            $this.snippets_update_url = url;
            localStorage["snippets-update-url"] = url;
            // HACK: Force aboutHome.js to always load the snippets.
            localStorage["snippets-last-update"] = Date.now() - 86400000 - 1;
        },

        EOF:null
    };

    return $this.init();
})();
