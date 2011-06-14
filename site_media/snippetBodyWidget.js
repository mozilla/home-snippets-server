(function($) {
$(function() {
	var icon_url = $("#snippet-icon-url");
	var snippet_text = $("#snippet-text");
	var preview = $("#snippet-preview");
	var form_textarea = $("#id_body");

	var preview_icon_url = "";
	var preview_icon_data = "";

	function wiki2link(str) {
		return str.replace(/\[(.+)\|(.+)\]/, '<a href="$1">$2</a>');
	}

	function link2wiki(str) {
		return str.replace(/<a href="(.+)">(.+)<\/a>/, "[$1|$2]");
	}
	
	// Generate snippet code and fill form/preview with it
	function generateSnippet() {
		// Add comment to easily identify "basic" snippets
		var snippet = '<!--basic--><div class="snippet">';
		if (preview_icon_data != '') {
			snippet += '<img class="icon" src="' + preview_icon_data + '" />';
		}
		snippet += '<p>' + wiki2link(snippet_text.val()) + '</p></div>';

		form_textarea.val(snippet);
		preview.html(snippet);
	}

	function encodeIcon() {
		// Avoid encoding when we don't need to
		if (preview_icon_url != icon_url.val()) {
			// TODO: Support non-png images
			var image_to_encode = icon_url.val();
			$.ajax({
				url: '/base64encode/' + image_to_encode,
				dataType: 'json',
				error: function() {
					alert("Error encoding icon. Please check that the icon URL points to a valid PNG image.");
				},
				success: function(data) {
					preview_icon_url = image_to_encode;
					preview_icon_data = 'data:image/png;base64,' + data['img'];
					generateSnippet();
				}
			});
		}
	}

	// Parse snippet code and fill in basic form with pulled info
	(function() {
		var snippet_code = form_textarea.val();
		if (snippet_code.match(/<!--basic-->/) === null) return;
		
		// Be dumb and throw a regex at it
		var img_matches = snippet_code.match(/<img class="icon" src="([\s\S]+)" \/>/);
		if (img_matches === null) return;
		preview_icon_data = img_matches[1];

		var text_matches = snippet_code.match(/<p>(.+)<\/p>/);
		if (text_matches === null) return;

		snippet_text.val(link2wiki(text_matches[1]));
		generateSnippet();
	})();

	$('#snippet-text').bind('change keyup', generateSnippet);
	$('#snippet-embed-button').click(encodeIcon);
	$('#snippet-editor').easytabs();
});
})(jQuery);