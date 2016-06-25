// import Native.Csrf

var _comses$miracle$Native_Csrf = function(){

    // http://musings.tinbrain.net/blog/2015/aug/28/vanilla-js-meets-djangos-csrf/
    function parse_cookies() {
        var cookies = {};
        if (typeof document !== 'undefined') {
            if (document.cookie && document.cookie !== '') {
                document.cookie.split(';').forEach(function (c) {
                    var m = c.trim().match(/(\w+)=(.*)/);
                    if (m !== undefined) {
                        cookies[m[1]] = decodeURIComponent(m[2]);
                    }
                });
            }
        }
        return cookies;
    }
    function getCsrfToken() {
        var csrfToken = parse_cookies()['csrftoken'];
        return   (csrfToken === null || (typeof csrfToken !== "string"))
             ? _elm_lang$core$Maybe$Nothing
             : _elm_lang$core$Maybe$Just(csrfToken);
    }

    function addOne(a) {
      return a + 1;
    }

    return {
        getCsrfToken: getCsrfToken(),
        addOne: addOne
    }
}();