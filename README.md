# about:home Snippets Server v0.1

Firefox 4 has space for snippets of content on about:home - this is a content
management app to serve and manage those snippets.

See also: <https://bugzilla.mozilla.org/show_bug.cgi?id=592431>

## Development

* Make sure you have at least Python 2.5
    * I'm using Python 2.6.5 from MacPorts, for what it's worth.
* Get the source code:
    * `git clone git://github.com/lmorchard/home-snippets-server.git`
    * `cd home-snippets-server`
* Acquire python library dependencies, using either of these methods
    * Use the vendor library (closer to Mozilla production):
        * `git clone git://github.com/lmorchard/home-snippets-server-lib.git vendor`
    * Use [pip][] and [virtualenv][] (more bleeding edge):
        * `virtualenv --no-site-packages env`
        * `./env/activate`
        * `pip install -r requirements/dev.txt`
* Prepare a `settings_local.py` file:
    * `cp settings_local.py-dist-dev settings_local.py`
    * Local config tweaks go here, though existing defaults may be sufficient to start hacking.
* Set up and run the project
    * Quick and dirty development
        * Use a sqlite DB in your `settings_local.py` file
        * `python manage.py syncdb`
    * Using MySQL and Schematic migrations (closer to Mozilla production)
        * Use the vendor library as described earlier.
        * Set up a MySQL database using `migrations/000-base.sql`
        * Configure your `settings_local.py` to use the MySQL database
        * `./vendor/src/schematic/schematic migrations`
        * Repeat the previous step whenever code is updated
        * Be sure to create numbered SQL migration files under `migration/` whenever you need to change the database.
    * `python manage.py runserver`
        
[virtualenv]: http://pypi.python.org/pypi/virtualenv
[pip]: http://pip.openplans.org/
        
* Running tests
    * `python manage.py test homesnippets`
        * This runs everything, with minimal verbosity
    * `python manage.py test homesnippets -lnose.homesnippets -a\!TODO`
        * This skips tests that may intentionally fail because they represent in-progress features.

## Deployment

* Follow the steps for development, but use the vendor library and use Schematic migrations.
* Also, check out `settings_local.py-dist-prod` rather than the `-dev` version.
* Configure your web server to serve up static assets, which are only served by Django in development.

### Static assets

For Apache, something like this should do (adjust paths to suit your installation):
   
    Alias /site_media/ /www/snippets.decafbad.com/app/home-snippets-server/site_media/
    <Directory /www/snippets.decafbad.com/app/home-snippets-server/site_media>
        Options -ExecCGI
    </Directory>
    Alias /media/ /www/snippets.decafbad.com/app/home-snippets-server/vendor/packages/Django/django/contrib/admin/media/
    <Directory /www/snippets.decafbad.com/app/home-snippets-server/vendor/packages/Django/django/contrib/admin/media>
        Options -ExecCGI
    </Directory>

Useful settings, if you need to change the locations from which these assets are served (eg. to a CDN or other host)

* `MEDIA_URL = '/site_media/'`
    * May be an absolute URL
* `MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'site_media')`
    * Absolute file path to location of `site_media`
* `ADMIN_MEDIA_PREFIX = '/media/'`
    * May be an absolute URL
* `ADMIN_MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'vendor/packages/Django/django/contrib/admin/media')`
    * Absolute file path to location of `vendor/packages/Django/django/contrib/admin/media`
