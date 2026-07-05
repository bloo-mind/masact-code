"""The treasury: a stock constraint the accounting can see."""

from dataclasses import dataclass


@dataclass
class Budget:
    allowance: int
    spent: int = 0

    def debit(self, amount: int) -> None:
        self.spent += amount

    def exhausted(self) -> bool:
        return self.spent >= self.allowance
