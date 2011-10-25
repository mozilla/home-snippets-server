SnippetBodyWidget = function($) {
    var elems = {
        icon_url: $('#snippet-icon-url'),
        text: $('#snippet-text'),
        preview: $('#snippet-preview'),
        code: $('#id_body')
    };

    var snippet = {
        text: '',
        icon: null
    };

    function wiki2link(str) {
        return str.replace(/\[(.+)\|(.+)\]/, '<a href="$1">$2</a>');
    }

    function link2wiki(str) {
        return str.replace(/<a href="(.+)">(.+)<\/a>/, '[$1|$2]');
    }

    function renderSnippet() {
        var code = ich.snippet_template(snippet, true);

        // Escape ampersands
        code = code.replace(/&(?!amp;)/, '&amp;');

        return code;
    }

    function updatePreview() {
        var code = renderSnippet();
        elems.code.val(code);
        elems.preview.html(code);
    }

    // Sends icon URL to server to encode in base64
    function encodeIcon(icon_url, successCallback) {
        // TODO: Support non-png images
        // TODO: Show animation while waiting for image encoding
        $.ajax({
            url: '/base64encode?url=' + encodeURIComponent(icon_url),
            dataType: 'json',
            error: function() {
                // TODO: Make pretty
                alert('Error encoding icon. Please check that the icon URL points to a valid PNG image.');
            },
            success: function(data) {
                if (typeof successCallback === 'function') {
                    successCallback('data:image/png;base64,' + data['img']);
                }
            }
        });
    }

    // Bind events and do UI
    $('#snippet-text').bind('change keyup', function() {
        snippet.text = wiki2link(elems.text.val());
        updatePreview();
    });

    $('#snippet-embed-button').click(function() {
        encodeIcon(elems.icon_url.val(), function(icon_data) {
            snippet.icon = {
                url: elems.icon_url.val(),
                data: icon_data
            };
            updatePreview();
        });
    });
    $('#snippet-editor').easytabs();


    // Parse snippet code and fill in basic form with pulled info
    (function() {
        var snippet_code = elems.code.val();
        if (snippet_code.match(/<!--basic-->/) === null) {
            if (snippet_code !== '') {
                $('#snippet-editor').easytabs('select', '#snippet-advanced');
            }
            return;
        }

        // Simple parsing using regex
        var img_matches = snippet_code.match(/<img class="icon" src="([\s\S]+)" \/>/),
            icon_matches = snippet_code.match(/<!--icon:([\s\S]+)-->/);
        if (img_matches || icon_matches) {
            snippet.icon = {
                url: (icon_matches ? icon_matches[1] : ''),
                data: (img_matches ? img_matches[1] : '')
            };
            elems.icon_url.val(snippet.icon.url);
        }

        var text_matches = snippet_code.match(/<p>(.+)<\/p>/);
        if (text_matches !== null) {
            snippet.text = text_matches[1];
            elems.text.val(link2wiki(text_matches[1]));
        }

        updatePreview();
    })();
};

jQuery(SnippetBodyWidget);
