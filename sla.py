from decimal import Decimal


class SLAStop(RuntimeError):
    pass


class RunBudget:
    def __init__(self, limit_usd, max_steps=5, on_open=None):
        requested = Decimal(str(limit_usd))
        if not requested.is_finite() or requested <= 0:
            raise ValueError("Budget must be positive and finite.")
        self.limit = min(requested, Decimal("0.15"))
        self.spent = Decimal("0")
        self.reserved = Decimal("0")
        self.steps = 0
        self.max_steps = max_steps
        self.state = "CLOSED"
        self.on_open = on_open

    def stop(self, reason):
        if self.state != "OPEN":
            self.state = "OPEN"
            if self.on_open:
                self.on_open(reason)
        raise SLAStop(reason)

    def reserve(self, maximum_cost_usd):
        if self.state == "OPEN":
            raise SLAStop("Circuit breaker is OPEN.")
        amount = Decimal(str(maximum_cost_usd))
        if not amount.is_finite() or amount < 0:
            self.stop("Invalid cost estimate.")
        if self.reserved:
            self.stop("Previous call has not been settled.")
        if self.steps >= self.max_steps:
            self.stop("Step limit reached.")
        if self.spent + amount > self.limit:
            self.stop("Next call would exceed run budget.")
        self.reserved = amount
        self.steps += 1

    def settle(self, actual_cost_usd):
        amount = Decimal(str(actual_cost_usd))
        if not amount.is_finite() or amount < 0:
            self.stop("Invalid actual cost.")
        reserved = self.reserved
        self.reserved = Decimal("0")
        self.spent += amount
        if amount > reserved or self.spent > self.limit:
            self.stop("Actual cost exceeded reservation or budget.")

    def charge_uncertain_call(self):
        # A timeout may still incur provider charges.
        self.spent += self.reserved
        self.reserved = Decimal("0")
        self.stop("Call failed; reserved cost charged conservatively.")


if __name__ == "__main__":
    events = []
    budget = RunBudget("0.05", on_open=events.append)
    budget.reserve("0.03")
    budget.settle("0.02")
    print("PASS: call within budget")

    try:
        budget.reserve("0.04")
    except SLAStop:
        assert budget.state == "OPEN"
        assert budget.spent == Decimal("0.02")
        assert len(events) == 1
        print("PASS: over-budget call blocked before execution")
    else:
        raise AssertionError("Budget stop failed.")

    try:
        budget.reserve("0.001")
    except SLAStop:
        assert len(events) == 1
        print("PASS: OPEN blocks further calls; one alert event")
    else:
        raise AssertionError("OPEN circuit allowed a call.")

    limited = RunBudget("0.15", max_steps=1)
    limited.reserve("0.01")
    limited.settle("0.005")
    try:
        limited.reserve("0.01")
    except SLAStop:
        print("PASS: step limit enforced")
    else:
        raise AssertionError("Step limit failed.")

    assert RunBudget("0.50").limit == Decimal("0.15")
    print("PASS: global hard ceiling is $0.15")
    print("SLA CHECK PASSED")
