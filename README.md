# about:home Snippets Server v0.0

Firefox 4 has space for snippets of content on about:home - this is a content
management app to serve and manage those snippets.

See also: <https://bugzilla.mozilla.org/show_bug.cgi?id=592431>

## Development

* Getting started
    * Make sure you have at least Python 2.5
        * I'm using Python 2.6.5 from MacPorts, for what it's worth.
    * Get the source code:
        * `git clone git://github.com/lmorchard/home-snippets-server.git`
        * `cd home-snippets-server`
    * Acquire python library dependencies, using either of these methods:
        * Use the vendor library (closest to production):
            * `git clone git://github.com/lmorchard/home-snippets-server-lib.git vendor`
        * Use [pip][] and [virtualenv][] (more bleeding edge):
            * `virtualenv --no-site-packages env`
            * `./env/activate`
            * `pip install -r requirements/dev.txt`
    * Prepare a `settings_local.py` file:
        * `cp settings_local.py-dist-dev settings_local.py`
        * Local config tweaks go here, though existing defaults may be sufficient to start hacking.
    * Set up and run the project
        * `python manage.py syncdb`
        * `python manage.py runserver`
        
[virtualenv]: http://pypi.python.org/pypi/virtualenv
[pip]: http://pip.openplans.org/
        
* Running tests
    * `python manage.py test homesnippets -lnose.homesnippets -a\!TODO`

## Deployment

* Vendor library here:
    * http://github.com/lmorchard/home-snippets-server-lib
    * Clone that into a `vendor` subdirectory of this project
* More details coming soon
