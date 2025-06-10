from interactions import OptionType, slash_option

from .locale import getdesc, getname


def roleOption(required: bool = True):
    def wrapper(func):
        return slash_option(
            name=getname("role"),
            description=getdesc("role"),
            opt_type=OptionType.ROLE,
            required=required,
        )(func)

    return wrapper


def channelOption(required: bool = True):
    def wrapper(func):
        return slash_option(
            name=getname("channel"),
            description=getdesc("channel"),
            opt_type=OptionType.CHANNEL,
            required=required,
        )(func)

    return wrapper


def plainTextOption(name: str = "text", required: bool = True):
    def wrapper(func):
        return slash_option(
            name=getname(name),
            description=getdesc(name),
            opt_type=OptionType.STRING,
            required=required,
        )(func)

    return wrapper


def UserOption(required: bool = True):
    """Decorator to create a slash command option for a user.
    Args:
        required (bool): Whether the user option is required. Defaults to True.
    Returns:
        function: Decorated function with the user option.
    """

    def wrapper(func):
        return slash_option(
            name=getname("user"),
            description=getdesc("user"),
            opt_type=OptionType.USER,
            required=required,
        )(func)

    return wrapper
