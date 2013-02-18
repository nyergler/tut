def version():
    """Return the installed package version."""

    import pkg_resources

    return pkg_resources.get_distribution('tut').version
