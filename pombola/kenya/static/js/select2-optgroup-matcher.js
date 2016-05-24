/* When you type into a Select2-enhanced select, it will normally only
   match the names of the options, not the names of the optgroups that
   contain those options. This optgroupMatcher function can be used as
   a custom matcher for Select2 to match text in optgroup as well as
   option labels.  This code is taken from this helpful comment:

     https://github.com/select2/select2/issues/3034#issuecomment-126451444
*/

includeOptgroupsMatcher = function(term, text) {

  text.parentText = text.parentText || "";

  // Always return the object if there is nothing to compare
  if ($.trim(term.term) === '') {
    return text;
  }

  // Do a recursive check for options with children
  if (text.children && text.children.length > 0) {
    // Clone the text object if there are children
    // This is required as we modify the object to remove any non-matches
    var match = $.extend(true, {}, text);

    // Check each child of the option
    for (var c = text.children.length - 1; c >= 0; c--) {
      var child = text.children[c];
      child.parentText += text.parentText + " " + text.text;

      var matches = includeOptgroupsMatcher(term, child);

      // If there wasn't a match, remove the object in the array
      if (matches == null) {
        match.children.splice(c, 1);
      }
    }

    // If any children matched, return the new object
    if (match.children.length > 0) {
      return match;
    }

    // If there were no matching children, check just the plain object
    return includeOptgroupsMatcher(term, match);
  }

  // If the typed-in term matches the text of this term, or the text from any
  // parent term, then it's a match.
  var original = (text.parentText + ' ' + text.text).toUpperCase();
  var term = term.term.toUpperCase();


  // Check if the text contains the term
  if (original.indexOf(term) > -1) {
    return text;
  }

  // If it doesn't contain the term, don't return anything
  return null;
}
