(function($, cilc, settings) {

var library = {

	libraries: {},

	css: {
		'errorClass':       "error",
		'initializedClass': "initialized",
		'initialized':      ".initialized",
		'libraries':        ".media-library",
		'successClass':     "success"
	},

	//  Activates all media libraries on the page
	initialize: function() {
		$(library.css.libraries).not(library.css.initialized).each(library.initializeLibrary);
	},

	//  Initializes an individual media library
	initializeLibrary: function(i, el) {
		var newLibrary = new MediaLibrary(el), $el = $(el);
		$el.addClass(library.css.initializedClass);
		library.libraries[$el.attr('id')] = newLibrary;
	},

	//  Returns an jQuery object of all initialized media libraries
	getAllInitializedLibraries: function() {
		return library.libraries;
	},

	//  Returns the MediaLibrary instance created for a library's ID
	getLibraryByID: function(id) {
		if (library.libraries[id]) {
			return library.libraries[id];
		}
		return null;
	},

	//  Serializes any fields in a section of a form to an object
	serializeFormSection: function($section) {
		var postData = {}, $el;
		$section.find(":input").each(function(i, el) {
			$el = $(el);
			if ($el.attr('name')) {
				postData[$el.attr('name')] = $el.val();
			}
		});
		return postData;
	},

	//  Show success and failure alerts
	showAlert: function(alert, message, removeClass, addClass) {
		$(alert).show().removeClass(removeClass).addClass(addClass).text(message);
	},
	alertSuccess: function(alert, message) {
		var $alert = $(alert);
		library.showAlert(alert, message, library.css.errorClass, library.css.successClass);
		$alert.fadeOut(2000);
	},
	alertFailure: function(alert, error) {
		library.showAlert(alert, error, library.css.successClass, library.css.errorClass);
	}
};

var MediaLibrary = function(libraryEl) {

	var $library = $(libraryEl), $modal, $filters, fileFieldCopy,
	libraryDOMID = $library.attr('id'),
	libraryID = $library.attr('id').substr($library.attr('id').indexOf('_') + 1),
	mediaID = 0,

	css = {
		'addForm':        "#media-library-add-form",
		'addFormAlert':   "#add-form-alert",
		'addLinks':       ".media-library-add-link",
		'addGroupButton': "#submit-new-group-button",
		'addGroupLink':   "#add-media-group-link",
		'fileField':      "#form-field-media-file",
		'filterForm':     ".media-library-filters",
		'filters':        ".media-library-filters :input",
		'groupList':      "#form-field-media-groups",
		'mediaFields':    "#media-fields",
		'mediaList':      "#id_file_list",
		'newGroupAlert':  "#new-group-alert",
		'newGroupFields': "#new-media-group-fields",
		'newGroupName':   "#id_group_name",
		'subtypeFilter':  "#id_subtype_filter",
		'typeSelector':   "#form-field-media-is-file :radio",
		'urlField':       "#form-field-media-url"
	},

	//  Binds event handlers for the library filters
	bindFilterEventHandlers = function() {
		$library.find(css.filters).unbind().not(css.mediaList).change(filterMediaLibrary);
		$library.find(css.mediaList).change(setCurrentMediaItem);
		setCurrentMediaItem();
	},

	//  Set the ID of the current media item
	setCurrentMediaItem = function() {
		mediaID = $library.find(css.mediaList).val();
		if (!mediaID) {
			mediaID = 0;
		}
	},

	//  Gets the ID of the selected media item
	getCurrentMediaID = function() {
		return mediaID;
	},

	//  Requests the media files that match the selected filters
	filterMediaLibrary = function(e) {
		$.ajax({
			data:     library.serializeFormSection($library.find(css.filterForm)),
			dataType: "json",
			success:  updateMediaLibrary,
			type:     "POST",
			url:      _global_filterURL
		});
	},

	//  Updates the library filters with the newly filtered results
	updateMediaLibrary = function(data) {
		if (data.success) {
			$library.find(css.subtypeFilter).replaceWith(data.markup.subtypes);
			$library.find(css.mediaList).replaceWith(data.markup.media);
			bindFilterEventHandlers();
		}
	},

	//  Loads the media addition form
	loadAddMediaForm = function(e) {
		e.preventDefault();
		$.ajax({
			data:     {library_id: libraryID},
			dataType: "json",
			success:  renderAddMediaForm,
			type:     "POST",
			url:      $(this).attr('href')
		});
	},

	//  Inserts the markup for the media addition form into the document
	renderAddMediaForm = function(data) {

		//  Render the addition form in a modal window
		if (data.success && data.markup.form) {
			$.modal(data.markup.form, {
				containerId: "media-modal-container",
				onShow: configureAdditionForm
			});

			//  Store a copy of the file upload field, used in form clearning
			fileFieldCopy = $(css.fileField).html();
		}
	},

	//  Configures the media addition form
	configureAdditionForm = function(dialog) {

		//  Make the file / URL selector hide the opposite field
		$modal = dialog;
		$(css.typeSelector).click(hideMediaFields);
		hideMediaFields();

		//  Enable interactivity for the new group addition fields
		$(css.newGroupFields).hide();
		$(css.addGroupLink).click(toggleNewGroupFields);
		$(css.addGroupButton).click(submitNewGroup);

		//  Set the form to submit via ajax
		dialog.data.find(css.addForm).ajaxForm({
			dataType: "json",
			success:  handleMediaAddition
		});
	},

	//  Submits a new group
	submitNewGroup = function(e) {

		var postData = library.serializeFormSection($(css.newGroupFields));
		postData['library_id'] = libraryID;
		$.ajax({
			data:     postData,
			dataType: "json",
			success:  updateGroupList,
			type:    "POST",
			url:     _global_newGroupURL
		})
	},

	//  Updates the list of available groups
	updateGroupList = function(data) {
		var $alert = $modal.data.find(css.newGroupAlert);
		if (data.success) {
			library.alertSuccess($alert, data.message);
			$(css.groupList).replaceWith(data.markup.group_selector);
			$(css.newGroupName).val('');
			refreshFilters();
		} else {
			library.alertFailure($alert, data.error);
		}
	},

	//  Toggles visibility of the new group fields
	toggleNewGroupFields = function(e) {

		e.preventDefault();

		$fields = $(css.newGroupFields);
		if ($fields.is(":visible")) {
			$fields.fadeOut();
		} else {
			$fields.fadeIn();
		}
	},

	//  Handles the submission of the add media form
	handleMediaAddition = function(data) {

		var $alert = $modal.data.find(css.addFormAlert);

		//  If the media was added, show a success message and update the media
		//  library list after clearing the addition form
		if (data.success) {
			library.alertSuccess($alert, data.message);
			$(css.addForm).clearForm();
			$(css.fileField).html(fileFieldCopy);
			refreshFilters();

			//  Restore focus to the medium type selector
			$(css.typeSelector).filter("[value=" + (data.local ? "True" : "False") + "]").attr('checked', true);
		}

		//  If the saving failed, display the error
		else {
			library.alertFailure($alert, data.error);
		}
	},

	//  Refreshes all library filters for the current library
	refreshFilters = function() {
		$.ajax({
			data:     {library_id: libraryID},
			dataType: "json",
			success:  updateFilterMarkup,
			type:     "POST",
			url:      _global_updateFilterURL
		});
	},

	//  Updates the markup for the library filters
	updateFilterMarkup = function(data) {
		if (data.success) {
			$(library.css.libraries).filter(library.css.initialized).find(css.filterForm).html(data.markup.filters);
			bindFilterEventHandlers();
		}
	},

	//  Hides fields not needed for the current media type
	hideMediaFields = function(e) {

		//  Hide URL fields if selecting a file, or file fields if using a URL
		var $file = $(css.fileField), $url = $(css.urlField);
		if ($(css.typeSelector).filter(":checked").attr('value') === "True") {
			$file.show();
			$url.hide().find(":input").val('');
		} else {
			$file.hide().html(fileFieldCopy);
			$url.show();
		};
	};

	//  Enable media library filtering for the select boxes
	bindFilterEventHandlers();
	filterMediaLibrary();

	//  Make the media addition links load the addition form
	$library.find(css.addLinks).click(loadAddMediaForm);

	//  Expose public properties and methods
	this.$library = $library;
	this.getCurrentMediaID = getCurrentMediaID;
};

cilc.widgets.mediaLibrary = {
	all:          library.getAllInitializedLibraries,
	MediaLibrary: MediaLibrary,
	initialize:   library.initialize,
	libraryForID: library.getLibraryByID
};

})(jQuery, cilc, cilc_settings);
