
(function($, cilc, settings) {

var wc = {

	css: {
		'current':           ".current",
		'currentCount':      ".current.value",
		'maxWordsStub':      "max-words",
		'minWordsStub':      "min-words",
		'stubValueSpacer':   "_",
		'wordCounterIDBase': "word-counter-",
		'wordCounters':      ".word-counter",
		'wordCounterInputs': "textarea.uses-word-counter"
	},

	classes: {
		'current':       "current",
		'maximum':       "maximum",
		'minimum':       "minimum",
		'limitType':     "limit",
		'limitVal':      "value",
		'outsideBounds': "outside-bounds",
		'overBounds':    "over",
		'underBounds':   "under",
		'wordCounter':   "word-counter"
	},

	text: {
		'current': "Current",
		'minimum': "Minimum",
		'maximum': "Maximum"
	},

	validKeyCodes: {
		"backspace": 8,
		"delete":    46,
		"period":    190,
		"space":     32
	},

	counters: [],

	//  Create a new word counter for every countable field with at least one
	//  word count boundary set, taking an optional argument, which is a jQuery
	//  selector for the part of the DOM in which to search for word counters
	initializeWordCounters: function(filter) {
		var counter, classes, j, valid;
		$(filter || "body").find(wc.css.wordCounterInputs).each(function(i, textarea) {

			//  Only create a counter for a class with at least one boundary
			classes = $(textarea).attr('class').split(/\s+/);
			valid = false;
			for (j=0; j < classes.length; j++) {
				if (classes[j].indexOf(wc.css.minWordsStub) == 0 || classes[j].indexOf(wc.css.maxWordsStub) == 0) {
					valid = true;
					break;
				}
			}

			//  If the textarea is properly configured to receive a counter,
			//  create the WordCounter instance and register its event handlers
			if (valid) {
				counter = new WordCounter(textarea);
				counter.registerEvents();
				wc.counters.push(counter);
			}
		});
	},

	//  Gets a word count boundary from a textarea's class name
	getWordLimit: function(textarea, limit) {

		var classes = $(textarea).attr('class').split(/\s+/), i, limitSearch = limit + wc.css.stubValueSpacer;
		for (i=0; i < classes.length; i++) {
			if (classes[i].indexOf(limit) > -1) {
				return classes[i].split(wc.css.stubValueSpacer)[1];
			}
		}
		return 0;
	}
};

//  Creates a new word counter instance linked with the given textarea
var WordCounter = function(textarea) {

	//  Create a unique ID for each wordcounter that links it with the textarea
	var $textarea = $(textarea), minWords, maxWords, $counter, parts = [], i=0, part,
	    counterID = wc.css.wordCounterIDBase + $textarea.attr('id'), $current, $currentCount;

	//  Update the display of the current word count
	var updateWordCount = function(e) {

		var keyCode = e.keyCode || e.which,
		    validKey = keyCode === undefined,
			keyName,
			currentWords = 0,
			currentText,
			boundsError = false;

		//  See if the key pressed is on our list of valid keypresses after
		//  which the word count should be recalculated
		if (!validKey) {
			for (keyName in wc.validKeyCodes) {
				if (keyCode === wc.validKeyCodes[keyName]) {
					validKey = true;
					break;
				}
			}
		}

		if (validKey) {

			//  Get our current word count and display it
			currentText = $textarea.val() || "";
			currentWords = currentText ? currentText.split(/[^\s]\s+?[^\s]/).length : 0;
			$currentCount.text(currentWords);

			//  If the current word count goes outside of our bounds, update the
			//  classes on the current word count and the word counter as a
			//  whole to reflect the nature of the bounds violation.
			$current.removeClass([wc.classes.underBounds, wc.classes.overBounds].join(" "));
			$counter.removeClass(wc.classes.outsideBounds);

			if (currentWords < minWords) {
				$current.addClass(wc.classes.underBounds);
				boundsError = true;
			}
			if (maxWords && currentWords > maxWords) {
				$current.addClass(wc.classes.overBounds);
				boundsError = true;
			}
			if (boundsError) {
				$counter.addClass(wc.classes.outsideBounds);
			}
		}
	};

	//  Configure the editor to listen for keypress events
	this.registerEvents = function() {
		$textarea.bind('keyup', updateWordCount).trigger('keyup');
	};

	//  Get our max and min words from the textarea's classes
	minWords = wc.getWordLimit(textarea, wc.css.minWordsStub);
	maxWords = wc.getWordLimit(textarea, wc.css.maxWordsStub);

	//  If we have a meaningful max or min word count, add the counter markup
	if (maxWords || minWords) {

		//  Assemble the list of bounds that need to be displayed
		if (minWords) { parts.push([wc.text.minimum, minWords, wc.classes.minimum]); }
		parts.push([wc.text.current, 0, wc.classes.current]);
		if (maxWords) { parts.push([wc.text.maximum, maxWords, wc.classes.maximum]); }

		//  Create the markup for the word counter
		$counter = $("<dl>").addClass(wc.classes.wordCounter).attr('id', counterID);
		for (i=0; i < parts.length; i++) {
			part = parts[i];
			$counter.append($("<dt>").text(part[0]).addClass(part[2]).addClass(wc.classes.limitType));
			$counter.append($("<dd>").text(part[1]).addClass(part[2]).addClass(wc.classes.limitVal));
		}
		$textarea.before($counter);

		//  Store references to markup elements
		$current = $counter.find(wc.css.current);
		$currentCount = $counter.find(wc.css.currentCount);
	}
};

//  Initialize all word counters
$(document).ready(function() {
	wc.initializeWordCounters();
});

$.extend(cilc.widgets, {
	wordCounter: wc
});

})(jQuery, cilc, cilc_settings);
