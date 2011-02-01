(function($, CKEDITOR, cilc, settings) {

var editor = {

	initialize: function() {
		var libraries = cilc.widgets.mediaLibrary.all(), libraryID, library;
		for (libraryID in libraries) {
			var newEditor = RTEMediaLibrary(libraries[libraryID]);
		}
	}
};

var RTEMediaLibrary = function(library) {

	var $library = library.$library, editor, $editor, idPos, classes, i,
	$iframe,

	editorIDStub = "editor_",

	css = {
		'insertLink': '.insert-media'
	},

	//  Finalizes insertion of a media item by reverting back to WYSIWYG mode
	finalizeMediaInsertion = function(e) {

		//  If the editor has been switched to source mode, immediately revert
		//  it back to WYSIWYG mode, and remove this mode-change listener. This
		//  works because this function is set as a listener only when adding a
		//  media library item, during which the editor is set to source mode.
		if (editor.mode == "source") {
			editor.removeListener('mode', finalizeMediaInsertion);
			editor.setMode('wysiwyg');
		}
	},

	//  Inserts media into the editor, requesting the markup via ajax
	insertMediaIntoEditor = function(e) {
		e.preventDefault();
		$.ajax({
			data: {media_id: library.getCurrentMediaID() },
			dataType: "json",
			success: insertMediaMarkup,
			type: "POST",
			url: _global_mediaMarkupURL
		});
	},

	//  Inserts the markup for a media item
	insertMediaMarkup = function(data) {
		if (data.success) {

			//  Switch the editor to source mode, after setting a listener to
			//  watch for changes in the editing mode. The registered listener
			//  reverts the editor back to WYSIWYG as soon as it goes to source
			//  mode, which causes the various CKEditor plugins to either render
			//  the added elements or show placeholders for them.
			editor.on('mode', finalizeMediaInsertion);
			editor.setMode('source');

			//  Append our media markup to the source-editing textarea. Due to
			//  the timing of CKEditor, the updating of the textarea occurs well
			//  in advance of the mode change firing an event, so the data has
			//  been updated by the time that the finalizing function is called.
			var $textarea = $(editor.textarea.$);
			editor.textarea.setValue(editor.textarea.getValue() + data.markup.media);
		}
	};

	//  Get a reference to the editor linked to the library
	classes = $library.attr('class').split(" ");
	for (i=0; i < classes.length; i++) {
		idPos = classes[i].indexOf(editorIDStub);
		if (idPos === 0) {
			$editor = $("#" + classes[i].substr(editorIDStub.length));
			break;
		}
	}
	if (!$editor || !$editor.length) {
		return;
	}
	editor = cilc.widgets.rte.getEditorByID($editor.attr('id'));

	//  Set up the event handlers
	$library.find(css.insertLink).click(insertMediaIntoEditor);
};

cilc.widgets.rteWithMedia = {
	initialize: editor.initialize
};

})(jQuery, CKEDITOR, cilc, cilc_settings);
