
//  Set the default configuration for the RTE if none is specified
if (typeof rte_settings === 'undefined') {

	var rte_settings = {
		editors: {
			'default': {
				customConfig: '',
				toolbar: [
					['Bold', 'Italic', 'Underline'],
					['JustifyLeft', 'JustifyCenter', 'JustifyRight'],
					['TextColor', 'BGColor'],
					['Source']
				],
				skin: 'kama'
			}
		}
	};
}

(function($, CKEDITOR, cilc, settings, rte_settings) {

var rte = {

	css: {
		autoFocus:      ".auto-focus",
		replaceInputs:  ".uses-rte",
		replacedInputs: ".rte-configured"
	},

	autoFocusSet: false,
	editors: {},
	replacedCount: {},

	//  Called after the editor instance has been loaded
	configureEditor: function(e) {
		$(".cke_contents legend").hide();
	},

	//  Focuses on the given editor
	focusEditor: function(e) {
		e.editor.focus();
	},

	//  Returns all instantiated rich text editors
	allEditors: function() {
		var editors = [], editor;
		for (editor in rte.editors) {
			if (rte.editors.hasOwnProperty(editor)) {
				editors.push(rte.editors[editor]);
			}
		}
		return editors;
	},

	//  Returns the editor for the given ID
	getEditorByID: function(id) {
		if (rte.editors[id]) {
			return rte.editors[id];
		}
		return null;
	},

	//  Replaces each textarea tagged with the proper classes with a CKEditor.
	enableEditors: function() {

		var $editor, editorID, typeFoundPos, rteClass, editClasses, j,
			editorTypeSearch = 'editor-', autoFocus = false, oldID;

		//  Configure each RTE based upon its type
		$(rte.css.replaceInputs).not(rte.css.replacedInputs).each(function(i, editor) {

				typeFoundPos = -1;
				rteClass     = "default",
				$editor      = $(editor);
				editorID     = $editor.attr('id');
				autoFocus    = false;

				//  Update the replacement count for the editor
				if (!rte.replacedCount[editorID]) { rte.replacedCount[editorID] = 0; }
				rte.replacedCount[editorID]++;

				//  If we're overwriting an existing editor that has not yet been
				//  configured, such as if we refresh the markup of a form that
				//  contained a rich text editor via AJAX, alter the textarea's ID.
				if (rte.editors[editorID] && !$editor.filter(rte.css.replacedInputs).length) {
					oldID = editorID;
					$editor.attr('id', editorID + "-" + rte.replacedCount[editorID]);
					editorID = $editor.attr('id');
					rte.replacedCount[editorID] = rte.replacedCount[oldID];
				}

				//  Get the editor type from one of the classes (i.e., 'editor-default')
				editClasses = $editor.attr('class').split(' ');
				for (j in editClasses) {
					typeFoundPos = editClasses[j].indexOf(editorTypeSearch);
					if (typeFoundPos > -1) {
						rteClass = editClasses[j].substr(typeFoundPos + editorTypeSearch.length);
					}
				}

				//  Set the editor to auto-focus on startup if need and if no other
				//  editors have been set to auto-focus.
				if (!rte.autoFocusSet && $editor.filter(rte.css.autoFocus).length) {
					rte.autoFocusSet = true;
					autoFocus = true;
				}

				//  Insert the editor
				rte.editors[editorID] = CKEDITOR.replace(editorID, rte_settings.editors[rteClass]);
				rte.editors[editorID].on('instanceReady', rte.configureEditor);

				//  Set the on-load auto-focus event if needed
				if (autoFocus) {
					rte.editors[editorID].on('instanceReady', rte.focusEditor);
				}

				//  Flag the editor as being configured
				$editor.addClass(urth.noCSS(rte.css.replacedInputs));
		});
	}
};

$(document).ready(function() {

	//  Enable the rich text editors
	rte.enableEditors();
});

//  Make the rich text editor registering available through jQuery
$.enableRichTextEditors = function() { rte.enableEditors(); }

cilc.widgets.rte = {
	allEditors: rte.allEditors,
	getEditorByID: rte.getEditorByID
};

})(jQuery, CKEDITOR, cilc, cilc_settings, rte_settings);
