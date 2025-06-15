# Registry for mapping robot types to their factory functions
ROBOT_FACTORIES = {}


def register_robot_factory(robot_type: str, factory_func):
    """Register a factory function for a robot type.

    Args:
        robot_type: The robot type identifier (e.g., "my_custom_robot")
        factory_func: Function that takes a config and returns a Robot instance
    """
    ROBOT_FACTORIES[robot_type] = factory_func
