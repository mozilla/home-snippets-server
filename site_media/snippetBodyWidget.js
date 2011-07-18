jQuery(function($) {
	var icon_url_input = $('#snippet-icon-url');
	var snippet_text_input = $('#snippet-text');
	var preview = $('#snippet-preview');
	var form_textarea = $('#id_body');

	var preview_icon_data = '';

	function wiki2link(str) {
		return str.replace(/\[(.+)\|(.+)\]/, '<a href="$1">$2</a>');
	}

	function link2wiki(str) {
		return str.replace(/<a href="(.+)">(.+)<\/a>/, '[$1|$2]');
	}

	function previewSnippet(snippet) {
		form_textarea.val(snippet);
		preview.html(snippet);
	}

	// Generate snippet code
	function generateSnippet(icon_uri, text) {
		// Add comment to easily identify "basic" snippets
		var snippet = '<!--basic--><div class="snippet">';
		if (icon_uri !== '') {
			snippet += '<img class="icon" src="' + icon_uri + '" />';
		}
		snippet += '<p>' + wiki2link(text) + '</p></div>';

		return snippet;
	}

	function generateAndPreviewSnippet(icon_uri, text) {
		var snippet_code = generateSnippet(icon_uri, text);
		previewSnippet(snippet_code);
	}

	// Sends icon URL to server to encode in base64
	function encodeIcon(icon_url, successCallback) {
		// TODO: Support non-png images
		$.ajax({
			url: '/base64encode?url=' + encodeURIComponent(icon_url),
			dataType: 'json',
			error: function() {
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
		generateAndPreviewSnippet(preview_icon_data, snippet_text_input.val());
	});
	$('#snippet-embed-button').click(function() {
		encodeIcon(icon_url_input.val(), function(icon_data) {
			preview_icon_data = icon_data;
			generateAndPreviewSnippet(icon_data, snippet_text_input.val());
		});
	});
	$('#snippet-editor').easytabs();


	// Parse snippet code and fill in basic form with pulled info
	(function() {
		var snippet_code = form_textarea.val();
		if (snippet_code.match(/<!--basic-->/) === null) {
			if (snippet_code != '') {
				$('#snippet-editor').easytabs('select', '#snippet-advanced');
			}
			return;
		}

		// Be dumb and throw a regex at it
		var img_matches = snippet_code.match(/<img class="icon" src="([\s\S]+)" \/>/);
		if (img_matches !== null) {
			preview_icon_data = img_matches[1];
		}

		var text_matches = snippet_code.match(/<p>(.+)<\/p>/);
		if (text_matches === null) return;

		var snippet_text = link2wiki(text_matches[1]);
		snippet_text_input.val(snippet_text);
		generateAndPreviewSnippet(preview_icon_data, snippet_text);
	})();
});