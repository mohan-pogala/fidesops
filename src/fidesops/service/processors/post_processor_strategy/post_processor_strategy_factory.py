import logging
from enum import Enum
from typing import List, Dict, Any

from pydantic import ValidationError

from fidesops.common_exceptions import (
    NoSuchStrategyException,
    ValidationError as FidesopsValidationError,
)
from fidesops.schemas.saas.strategy_configuration import StrategyConfiguration
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_filter import (
    FilterPostProcessorStrategy,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy_unwrap import (
    UnwrapPostProcessorStrategy,
)
from fidesops.service.processors.post_processor_strategy.post_processor_strategy import (
    PostProcessorStrategy,
)


logger = logging.getLogger(__name__)


class SupportedPostProcessorStrategies(Enum):
    """
    The supported methods by which Fidesops can post-process Saas connector data.
    """

    unwrap = UnwrapPostProcessorStrategy
    filter = FilterPostProcessorStrategy


def get_strategy(
    strategy_name: str,
    configuration: Dict[str, Any],
) -> PostProcessorStrategy:
    """
    Returns the strategy given the name and configuration.
    Raises NoSuchStrategyException if the strategy does not exist
    """
    if strategy_name not in SupportedPostProcessorStrategies.__members__:
        valid_strategies = ", ".join([s.name for s in SupportedPostProcessorStrategies])
        raise NoSuchStrategyException(
            f"Strategy '{strategy_name}' does not exist. Valid strategies are [{valid_strategies}]"
        )
    strategy = SupportedPostProcessorStrategies[strategy_name].value
    try:
        strategy_config: StrategyConfiguration = strategy.get_configuration_model()(
            **configuration
        )
        return strategy(configuration=strategy_config)
    except ValidationError as e:
        raise FidesopsValidationError(message=str(e))


def get_strategies() -> List[PostProcessorStrategy]:
    """Returns all supported postprocessor strategies"""
    return [e.value for e in SupportedPostProcessorStrategies]
