# qef_core/reasoning/BaseStrategy.py

from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract Base Class for all reasoning strategies in the Quantum Æon Fluxor.

    This class defines the common interface that all concrete strategies,
    such as LogicalFlowStrategy or TreeOfThoughtsStrategy, must implement.
    This ensures that the StrategyManager can use any strategy interchangeably.
   
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The unique, human-readable name of the strategy."""
        pass

    @abstractmethod
    def execute(self, user_prompt: str, context: dict) -> dict:
        """
        Executes the reasoning strategy.

        Args:
            user_prompt (str): The initial prompt or query from the user.
            context (dict): A dictionary containing all relevant contextual
                            information, such as the C³, active code, etc.

        Returns:
            dict: A dictionary containing the result of the strategy,
                  including the final output, the reasoning path,
                  and any performance metrics.
        """
        pass