# TODO

* Merge switcher and server into the same project?

* Cache management
    * Flush cache
    * Explore cache?
        * Possible in memcache?

* Switch to (var)char as primary key in rules and snippets
    * As opposed to autoincrement int
    * PK will be human- or script-maintained
    * Makes content more explicitly portable between dev / stage / prod

* Enhance Smuggler to export a selected subset as action in admin changelist
    * Currently can export at app or model level, need more granularity

* LDAP auth for internal Mozilla use

* Enforce well-formed XML in snippet validation

* Validate regexes in client match rule management in admin

* Regex tester
    * Throw an URL at it, show whether or not matched
    * In JS? Inline in admin?

* Snippet types
    * Templated rendering of common snippet content patterns
        * Global styles
        * Basic snippet capsule
        * JS-randomized snippet content
        * JS-managed timed content
