# Pombola

This web app allows you to store and share information on public figures,
especially politicians.

Please see the [Operations Manual](http://goo.gl/uaXup) which covers all aspects of running a Pombola site.

For an overview of the system please see the files in docs/ - especially
[OVERVIEW.md](https://github.com/mysociety/pombola/blob/master/docs/OVERVIEW.md)


## Community

Please join the Mzalendo Users Google group for discussion about running Pombola-based websites. This is also where announcements etc will be made.

    https://groups.google.com/forum/?fromgroups=#!forum/mzalendo-users

There is also the Poplus mailing list for some of the code used to make the
site. This includes [MapIt](https://github.com/mysociety/mapit) (for the
boundaries), [PopIt](https://github.com/mysociety/popit) (a person data storage
engine that Pombola will be changed to use in the future), and
[SayIt](https://github.com/mysociety/sayit) (a speech data storage system,
similarly):

    https://groups.google.com/forum/#!forum/poplus


## Installing

Please see [docs/INSTALL.txt](https://github.com/mysociety/pombola/blob/master/docs/INSTALL.txt)

To change your site's look and feel please see the [styling notes](https://github.com/mysociety/pombola/blob/master/docs/STYLING_NOTES.md).


## Troubleshooting

Please see [docs/TROUBLESHOOTING.md](https://github.com/mysociety/pombola/blob/master/docs/TROUBLESHOOTING.md) file

## Future

The Pombola codebase was originally written for the Kenyan site
[mzalendo.com](http://info.mzalendo.com). It has since been modified to support
other sites around the world, notably several in Africa.

We want the code to be easy to use for other installations, but currently there are some rough edges.

We also intend to replace the `core` app's models with an external data store. This will be done using [PopIt](https://github.com/mysociety/popit) which is a project that we are currently working on.
