
(function($, settings) {

var datepicker = {

	css: {
		usesDatePicker: ".uses-date-picker",
		imageButton: ".ui-datepicker-trigger"
	},

	//  Enable datepickers on any properly classed inputs
	activateDatePickers: function() {

		//  Set date picker options
		var datePickerOptions = {
			buttonImage:     settings.shared_media_url + 'core/images/date_icon_tiny.png',
			buttonImageOnly: true,
			buttonText:      'Click this to choose a date',
			showAnim:        'blind',
			showOn:          'both'
		};

		//  Activate the date picker
		var $picker = $(datepicker.css.usesDatePicker);
		$picker.datepicker(datePickerOptions);
		$picker.siblings(datepicker.css.imageButton).css('cursor', 'pointer');
	}
};

$(document).ready(function() {

	//  Link date pickers to widgets
	datepicker.activateDatePickers();
});

cilc.widgets.datePicker = datepicker;

})(jQuery, cilc_settings);
