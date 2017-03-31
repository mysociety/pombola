Thank-you for your interest in contributing to Pombola!

The coding standards we keep to on this project are documented
here:

* [Coding Standards](https://mysociety.github.io/coding-standards.html)

You can see a waffle board representing all the issues that
we're currently working on here:

* [Pombola board at waffle.io](https://waffle.io/mysociety/pombola)

The names of the columns there may need some explanation:

* **Icebox**: all open issues that haven't been triaged, or
  are on the back burner.
* **Contender**: these are issues we'd like to work on at some
  point soon, approximately ordered so the most important are at
  the top of the column. (This is somewhat like the product
  backlog in other projects.)
* **Current Sprint**: these are issues we're working on in the
  current two week sprint.
* **Now**: these are the issues that someone's actively working
  on at the moment.
* **Reviewing**: these are tickets for which someone's done the
  work, and someone else is now reviewing it (or it's waiting
  for someone to review it).
* **Deploying**: these are tickets which have been reviewed and
  given a thumbs-up, but we haven't deployed yet.
* **Done**: this is for work which has been deployed and the
  issue should be closed.

### Issue state and assignment

Please don't just assign tickets to yourself or anyone else
without discussing it with someone on mySociety's parliaments
team — it's easy to miss changes in ticket assignments.  You can
contact us by commenting on the issue or emailing us at
<pombola@mysociety.org>. If it's agreed that you're going to
work on a ticket, then assign it to yourself.

If it's been agreed that you're going to be the main reviewer of
a pull request, please drag it into the reviewing column in
waffle and assign it to yourself.

After you've finished your review, let the author know and they
will either:

* Move the issue to the "Deploying" column (if there are no revisions
  to be made)
* Move the issue back to the "Now" column (if they're going to
  make those fixes immediately) or the "Current Sprint" column
  (if there's some really good reason for putting off making
  those changes)

... and assign it to themself.

One a change is deployed, drag the issue to the "Done" column
and it'll be closed.

Tips
----

If you create a new branch that starts with “NNN-” or “NNN_” or
has “#NNN” anywhere in it, then pushing that branch will
automatically move the issue with that number to "Now".

When you create a pull request, if it fixes a current issue put
either “Fixes #NNN”, “closes #NNN” or “resolves #NNN” in the
pull request's title or description, and then the pull request
will be linked with the issue. If it is only linked to an issue,
but doesn’t fix it, put one of “connect #NNN”, connects #NNN” or
“connected to #NNN” in the pull request message.

New pull requests from anyone will appear in Reviewing, so we
should notice them and leave comments pretty soon, but please
ask if there's no sign that your pull request has been looked
at.

---

*This document is based on
[TheyWorkForYou's CONTRIBUTING.md](https://github.com/mysociety/theyworkforyou/blob/master/CONTRIBUTING.md)
with some changes for the Pombola process.*
