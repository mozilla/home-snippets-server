(function($) {
$(function() {
	var icon_url = $("#snippet-body-icon-url");
	var snippet_text = $("#snippet-body-text");
	var preview = $("#snippet-body-preview");
	var form_textarea = $("#id_body");
	
	function generateSnippet(iconURI) {
		var snippet = '<div class="snippet">';
		if (iconURI != '') {
			snippet += '<img class="icon" src="' + iconURI + '" />';
		}
		snippet += '<p>' + snippet_text.val() + '</p></div>';

		form_textarea.val(snippet);
		preview.html(snippet);
	}

	var preview_icon_url = "";
	var preview_icon_data = "";
	function processBasicForm() {
		// Avoid encoding when we don't need to
		if (preview_icon_url != icon_url.val()) {
			preview_icon_url = icon_url.val();

			// TODO: Support non-png images
			$.ajax({
				url: '/base64encode/' + preview_icon_url,
				dataType: 'json',
				error: function() {
					generateSnippet("");
				},
				success: function(data) {
					preview_icon_data = 'data:image/png;base64,' + data['img'];
					generateSnippet(preview_icon_data);
				}
			});
		} else {
			generateSnippet(preview_icon_data);
		}
	}

	$('#snippet-body-text, #snippet-body-icon-url').bind('change keyup', processBasicForm);
	$('#snippet-body-editor').easytabs();
});
})(jQuery);