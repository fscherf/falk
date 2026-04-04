def add_dependency_provider(mutable_settings):
    def add_dependency(dependency, name=""):
        if not callable(dependency):
            raise ValueError("dependency needs to be a callback")

        if name and not isinstance(name, str):
            raise ValueError("name needs to be a string")

        name = name or dependency.__name__

        mutable_settings["dependencies"][name] = dependency

    return add_dependency
