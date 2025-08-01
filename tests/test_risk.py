from smartmoney_bot.risk.manager import AccountState, PositionParams, vet_and_size
from smartmoney_bot.strategy.core import Signal


def test_vet_and_size() -> None:
    sig = Signal(
        symbol="TEST",
        side="long",
        entry_price=100.0,
        sl_price=90.0,
        tp_price=130.0,
        p_hit_rate_est=0.4,
        r_multiple=3.0,
    )
    account = AccountState(equity=10000.0, start_equity=10000.0)
    params = PositionParams(risk_pct=1.0, max_dd_pct=50.0, daily_stop=1000.0)
    plan = vet_and_size(sig, account, params)
    assert plan is not None
    assert plan.qty == 10.0
