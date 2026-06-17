```requirements.txt
numpy>=1.16
asyncio
```

```python
# Auto-generated flattened file from FaaS entrypoint
# Source: main.py
# Target: apply_tax


class TaxCalculator:
    # This comes from other modules as we scan the whole project
    # to get all local dependencies and add them at the start
    # of the file before the decorated function.
    def __init__(self, tax_rate: float = 0.14) -> None:
        self.tax_rate = tax_rate

    def apply_tax(self, amount: float) -> float:
        return round(amount * (1 + self.tax_rate), 2)


def apply_tax(discounted_total: float) -> float:
    """Apply tax using an instance from utils.TaxCalculator."""
    calculator = TaxCalculator(tax_rate=0.14)
    return calculator.apply_tax(discounted_total)
```
