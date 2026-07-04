from strategy import RollingStraddleStrategy
from backtest_engine import BacktestEngine
from results_analyzer import ResultsAnalyzer

DATA_ROOT = "allData"
UNDERLIERS_TO_TRADE = ["NIFTY", "BANKNIFTY"]


def main():
    strategy = RollingStraddleStrategy()

    engine = BacktestEngine(
        data_root=DATA_ROOT,
        underliers=UNDERLIERS_TO_TRADE,
        strategy=strategy,
    )

    portfolio = engine.run()

    analyzer = ResultsAnalyzer(portfolio)

    analyzer.plot_all()

    import os
    worst_day_date = None
    if not analyzer.trades.empty:
        daily_pnl = analyzer.trades.copy()
        daily_pnl["date"] = daily_pnl["exit_time"].dt.date
        daily_sum = daily_pnl.groupby("date")["pnl"].sum()
        worst_day_date = daily_sum.idxmin()

    if worst_day_date:
        worst_date_str = worst_day_date.strftime("%Y-%m-%d")
        worst_date_folder_str = worst_day_date.strftime("%Y%m%d")
        worst_day_csv = f"allData/NSE_{worst_date_folder_str}/Futures (Continuous)/NIFTY-I.csv"

        if os.path.exists(worst_day_csv):
            analyzer.plot_futures_atm_rolls_for_day(
                futures_csv_path=worst_day_csv,
                selected_date=worst_date_str,
                underlier="NIFTY",
                output_path=f"plots/worst_day_{worst_date_str}_case_study.png"
            )
        else:
            print(f"Futures file not found for worst day {worst_date_str}: {worst_day_csv}")


if __name__ == "__main__":
    main()