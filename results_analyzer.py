import os
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class ResultsAnalyzer:
    """
    Creates summary statistics and plots from the completed portfolio.
    """

    def __init__(self, portfolio):
        self.pnl_history = portfolio.get_pnl_history_dataframe()
        self.trades = portfolio.get_closed_trades_dataframe()

        if not self.pnl_history.empty:
            self.pnl_history["timestamp"] = pd.to_datetime(
                self.pnl_history["timestamp"]
            )

        if not self.trades.empty:
            self.trades["entry_time"] = pd.to_datetime(self.trades["entry_time"])
            self.trades["exit_time"] = pd.to_datetime(self.trades["exit_time"])

          
            if "underlier" not in self.trades.columns:
                self.trades["underlier"] = self.trades["instrument"].apply(
                    self.get_underlier_from_instrument
                )
            self.trades["strike"] = self.trades["instrument"].apply(
                self.get_strike_from_instrument
            )
            self.trades["option_type"] = self.trades["instrument"].apply(
                self.get_option_type_from_instrument
            )


    @staticmethod
    def get_underlier_from_instrument(instrument):
       
        instrument = str(instrument)

        if instrument.startswith("BANKNIFTY"):
            return "BANKNIFTY"
        if instrument.startswith("FINNIFTY"):
            return "FINNIFTY"
        if instrument.startswith("NIFTY"):
            return "NIFTY"

        return "UNKNOWN"

    @staticmethod
    def get_strike_from_instrument(instrument):
        
        match = re.search(r"\d{6}(\d+)(CE|PE)$", str(instrument))

        if match:
            return int(match.group(1))

        return None

    @staticmethod
    def get_option_type_from_instrument(instrument):
        
        instrument = str(instrument)

        if instrument.endswith("CE"):
            return "CE"
        if instrument.endswith("PE"):
            return "PE"

        return "UNKNOWN"

    @staticmethod
    def ensure_output_folder(output_dir="plots"):
        os.makedirs(output_dir, exist_ok=True)

    def print_summary(self):
        if self.pnl_history.empty:
            print("No PnL history was recorded.")
            return

        final_row = self.pnl_history.iloc[-1]

        print("----- Backtest Summary -----")
        print(f"Final total PnL:    {final_row['total_pnl']:.2f}")
        print(f"Final realized PnL: {final_row['realized_pnl']:.2f}")
        print(f"Total trades closed: {len(self.trades)}")

        if not self.trades.empty:
            win_rate = (self.trades["pnl"] > 0).mean() * 100
            avg_pnl = self.trades["pnl"].mean()

            print(f"Win rate:            {win_rate:.1f}%")
            print(f"Average PnL / trade: {avg_pnl:.2f}")

    def plot_cumulative_pnl(self, output_path="plots/cumulative_pnl.png"):
        if self.pnl_history.empty:
            return

        self.ensure_output_folder()

        plt.figure(figsize=(12, 5))
        plt.plot(
            self.pnl_history["timestamp"],
            self.pnl_history["total_pnl"],
            label="Total PnL"
        )
        plt.plot(
            self.pnl_history["timestamp"],
            self.pnl_history["realized_pnl"],
            label="Realized PnL",
            linestyle="--"
        )
        plt.plot(
            self.pnl_history["timestamp"],
            self.pnl_history["total_pnl"] - self.pnl_history["realized_pnl"],
            label="Unrealized PnL",
            linestyle=":",
            alpha=0.7
        )

        plt.xlabel("Time")
        plt.ylabel("PnL")
        plt.title("Cumulative PnL Over Time")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def plot_daily_pnl(self, output_path="plots/daily_pnl.png"):
        if self.trades.empty:
            return

        self.ensure_output_folder()

        trades = self.trades.copy()
        trades["date"] = trades["exit_time"].dt.date
        daily_pnl = trades.groupby("date")["pnl"].sum()

        plt.figure(figsize=(12, 5))
        daily_pnl.plot(kind="bar")

        plt.xlabel("Date")
        plt.ylabel("PnL")
        plt.title("Daily PnL")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def plot_drawdown(self, output_path="plots/drawdown.png"):
        if self.pnl_history.empty:
            return

        self.ensure_output_folder()

        running_max = self.pnl_history["total_pnl"].cummax()
        drawdown = self.pnl_history["total_pnl"] - running_max

        plt.figure(figsize=(12, 5))
        plt.plot(self.pnl_history["timestamp"], drawdown)

        plt.xlabel("Time")
        plt.ylabel("Drawdown")
        plt.title("Drawdown Over Time")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def plot_trade_count_per_day(self, output_path="plots/trades_per_day.png"):
        if self.trades.empty:
            return

        self.ensure_output_folder()

        trades = self.trades.copy()
        trades["date"] = trades["exit_time"].dt.date

        closed_option_legs = trades.groupby("date").size()
        strike_rolls = closed_option_legs / 2

        plt.figure(figsize=(12, 5))
        strike_rolls.plot(kind="bar")

        plt.xlabel("Date")
        plt.ylabel("Number of strike rolls")
        plt.title("Strike Rolls Per Day")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


    def plot_underlier_cumulative_pnl(
        self,
        output_path="plots/underlier_cumulative_pnl.png"
    ):
        if self.trades.empty:
            return

        self.ensure_output_folder()

        df = self.trades.copy()
        df = df[df["underlier"].isin(["NIFTY", "BANKNIFTY"])]

        if df.empty:
            print("No NIFTY/BANKNIFTY trades found.")
            return

        grouped = (
            df.groupby(["exit_time", "underlier"])["pnl"]
            .sum()
            .unstack(fill_value=0)
            .sort_index()
        )

        for underlier in ["NIFTY", "BANKNIFTY"]:
            if underlier not in grouped.columns:
                grouped[underlier] = 0

        cumulative = grouped[["NIFTY", "BANKNIFTY"]].cumsum()

        plt.figure(figsize=(14, 6))
        plt.plot(cumulative.index, cumulative["NIFTY"], label="NIFTY")
        plt.plot(cumulative.index, cumulative["BANKNIFTY"], label="BANKNIFTY")
        plt.plot(
            cumulative.index,
            cumulative["NIFTY"] + cumulative["BANKNIFTY"],
            label="Combined",
            linestyle="--"
        )

        plt.xlabel("Time")
        plt.ylabel("Cumulative Realized PnL")
        plt.title("NIFTY vs BANKNIFTY Cumulative PnL")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()

    def plot_intraday_pnl_heatmap(
        self,
        output_path="plots/intraday_pnl_heatmap.png",
        bucket_minutes=15
    ):
        """
        Rows    = trading days
        Columns = 15-minute time buckets
        Values  = PnL change during that bucket

        Uses total_pnl, so it includes both realized PnL and MTM movement.
        """
        if self.pnl_history.empty:
            return

        self.ensure_output_folder()

        df = self.pnl_history.copy().sort_values("timestamp")

        df["date"] = df["timestamp"].dt.date
        df["time_bucket"] = df["timestamp"].dt.floor(
            f"{bucket_minutes}min"
        )

        df["pnl_change"] = (
            df.groupby("date")["total_pnl"]
            .diff()
            .fillna(0)
        )

        heatmap_data = (
            df.groupby(["date", "time_bucket"])["pnl_change"]
            .sum()
            .reset_index()
        )

        heatmap_data["time_label"] = heatmap_data["time_bucket"].dt.strftime(
            "%H:%M"
        )

        pivot = heatmap_data.pivot(
            index="date",
            columns="time_label",
            values="pnl_change"
        ).fillna(0)

        plt.figure(figsize=(18, 8))
        image = plt.imshow(
            pivot.values,
            aspect="auto",
            interpolation="nearest"
        )

        plt.colorbar(image, label="PnL change in bucket")

        plt.xticks(
            range(len(pivot.columns)),
            pivot.columns,
            rotation=90
        )
        plt.yticks(
            range(len(pivot.index)),
            [str(x) for x in pivot.index]
        )

        plt.xlabel(f"Time of day ({bucket_minutes}-minute buckets)")
        plt.ylabel("Trading date")
        plt.title("Intraday PnL Heatmap")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


    def plot_strike_roll_heatmap(
        self,
        output_path="plots/strike_roll_heatmap.png",
        bucket_minutes=15
    ):
        if self.trades.empty:
            return

        self.ensure_output_folder()

        df = self.trades.copy()
        df["date"] = df["exit_time"].dt.date
        df["time_bucket"] = df["exit_time"].dt.floor(
            f"{bucket_minutes}min"
        )

        roll_counts = (
            df.groupby(["date", "time_bucket"])
            .size()
            .div(2)
            .reset_index(name="roll_count")
        )

        roll_counts["time_label"] = roll_counts["time_bucket"].dt.strftime(
            "%H:%M"
        )

        pivot = roll_counts.pivot(
            index="date",
            columns="time_label",
            values="roll_count"
        ).fillna(0)

        plt.figure(figsize=(18, 8))
        image = plt.imshow(
            pivot.values,
            aspect="auto",
            interpolation="nearest"
        )

        plt.colorbar(image, label="Strike rolls")

        plt.xticks(
            range(len(pivot.columns)),
            pivot.columns,
            rotation=90
        )
        plt.yticks(
            range(len(pivot.index)),
            [str(x) for x in pivot.index]
        )

        plt.xlabel(f"Time of day ({bucket_minutes}-minute buckets)")
        plt.ylabel("Trading date")
        plt.title("Strike-Roll Intensity Heatmap")
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


    def plot_daily_pnl_vs_rolls(
        self,
        output_path="plots/daily_pnl_vs_rolls.png"
    ):
        """
        Each dot represents one day.

        X-axis: number of completed straddle rolls
        Y-axis: daily realized PnL
        """
        if self.trades.empty:
            return

        self.ensure_output_folder()

        df = self.trades.copy()
        df["date"] = df["exit_time"].dt.date

        daily_pnl = df.groupby("date")["pnl"].sum()

        daily_rolls = df.groupby("date").size() / 2

        daily = pd.DataFrame({
            "daily_pnl": daily_pnl,
            "strike_rolls": daily_rolls
        }).dropna()

        plt.figure(figsize=(11, 7))
        plt.scatter(
            daily["strike_rolls"],
            daily["daily_pnl"],
            s=90,
            alpha=0.8,
            label="Daily PnL"
        )

        for date, row in daily.iterrows():
            plt.annotate(
                str(date)[5:],
                (row["strike_rolls"], row["daily_pnl"]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8
            )

        if len(daily) >= 2 and daily["strike_rolls"].nunique() > 1:
            slope, intercept = np.polyfit(
                daily["strike_rolls"],
                daily["daily_pnl"],
                1
            )

            x_values = daily["strike_rolls"].sort_values()

            plt.plot(
                x_values,
                slope * x_values + intercept,
                linestyle="--",
                label="Trend line"
            )

        plt.axhline(0, linewidth=1)
        plt.xlabel("Strike rolls per day")
        plt.ylabel("Daily PnL")
        plt.title("Daily PnL vs Strike Rolls")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


    def plot_futures_atm_rolls_for_day(
        self,
        futures_csv_path,
        selected_date,
        underlier="NIFTY",
        output_path=None
    ):
        """
        This uses one raw futures file, for example:

        allData/NSE_20221103/futures/NIFTY-I.csv

        It shows:
        1. Futures price
        2. ATM strike selected by your strategy
        3. Each strike-roll event

        selected_date format: "2022-11-03"
        """

        if self.trades.empty:
            return

        self.ensure_output_folder()

        if output_path is None:
            output_path = (
                f"plots/{underlier.lower()}_futures_atm_rolls_"
                f"{selected_date}.png"
            )

        futures = pd.read_csv(
            futures_csv_path,
            header=None,
            names=["Date", "Time", "Price", "Volume", "OpenInterest"]
        )

       
        futures["timestamp"] = pd.to_datetime(
            futures["Date"].astype(str) + " " +
            futures["Time"].astype(str)
        )

        selected_day = pd.to_datetime(selected_date).date()

        futures = futures[
            futures["timestamp"].dt.date == selected_day
        ].copy()

        trades = self.trades.copy()

       
        trades = trades[
            (trades["underlier"] == underlier) &
            (trades["exit_time"].dt.date == selected_day)
        ].copy()

        if futures.empty or trades.empty:
            print(
                f"No futures/trades found for {underlier} on {selected_date}"
            )
            return

      
        roll_points = (
            trades.groupby(["exit_time", "strike"])
            .size()
            .reset_index(name="closed_legs")
        )

     
        roll_points = roll_points[roll_points["closed_legs"] >= 2]

        fig, ax1 = plt.subplots(figsize=(16, 7))

        ax1.plot(
            futures["timestamp"],
            futures["Price"],
            label=f"{underlier} Futures Price"
        )

        ax1.set_xlabel("Time")
        ax1.set_ylabel("Futures price")
        ax1.set_title(
            f"{underlier}: Futures Price, ATM Strike and Strike Rolls "
            f"({selected_date})"
        )

        ax2 = ax1.twinx()

        ax2.step(
            roll_points["exit_time"],
            roll_points["strike"],
            where="post",
            label="Selected ATM Strike"
        )

        ax2.scatter(
            roll_points["exit_time"],
            roll_points["strike"],
            s=25,
            marker="o",
            label="Strike Roll"
        )

        ax2.set_ylabel("ATM strike")

        ax1.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()

        ax1.legend(
            lines1 + lines2,
            labels1 + labels2,
            loc="upper left"
        )

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()


    def plot_all(self):
        self.print_summary()

        
        self.plot_cumulative_pnl()
        self.plot_daily_pnl()
        self.plot_drawdown()
        self.plot_trade_count_per_day()

     
        self.plot_underlier_cumulative_pnl()
        self.plot_intraday_pnl_heatmap()
        self.plot_strike_roll_heatmap()
        self.plot_daily_pnl_vs_rolls()