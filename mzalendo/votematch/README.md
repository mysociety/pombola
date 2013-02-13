# VoteMatch

This is an app that lets you present quizzes to users and use their responses to
suggest the most compatible party.


## Summary

The premise is that you create a **quiz** which is then linked to a number of
**statements**. You can also create **parties** (political parties, candidates,
philosophical positions) and for each of them create a **stance** that
represents their view for a particular statement.

The user is presented a form where they are asked how they feel about each
statement. Their **submission** is saved and linked to each **answer** that they
give for each statement.

When the results are presented a very naïve calculation is done to tell the user
their overall agreement with each party.

The results each have a unique URL that can be shared in the normal ways.

All the various parts can be maintained using the admin.


## Acknowledgements

Originally written by [mySociety](http://www.mysociety.org) for the
[Mzalendo](http://www.mzalendo.com) website to present quizzes to users for the
2013 Kenyan elections.

Thank you to the people behind
[WhoShouldYouVoteFor](http://www.whoshouldyouvotefor.com/) for their assistance
in deciding how to approach this code.


## Known issues

Currently it is not possible to reuse `parties` or `sattements` across several
quizzes. This would be an obvious addition but was omitted in the interests of
simplicity at the start and making progress.

The submission token is a random string. Collisions should be handled gracefully
if they occur.

The admin is currently very simple - should add filters etc.
