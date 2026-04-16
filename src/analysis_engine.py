import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt  # ★★★ 追加：Figureオブジェクトを操作するために必要


class AnalysisEngine:
    """
    データセットに対して統計的な計算や分析を実行するエンジン。
    Q-Qプロット生成や記述統計量の算出を行う。
    """

    def __init__(self, logger_manager):
        # ログマネージャーを依存性注入 (DI) で受け取ることで、ロギングの一貫性を保つ
        self.logger = logger_manager

    def calculate_descriptive_stats(self, df: pd.DataFrame, column_name: str) -> dict:
        """
        指定されたカラムの基本的な記述統計量（平均、標準偏差など）を計算する。

        Args:
            df (pd.DataFrame): データフレーム。
            column_name (str): 分析対象のカラム名。

        Returns:
            dict: 統計量の辞書。
        """
        if column_name not in df.columns:
            raise ValueError(f"カラム '{column_name}' はデータセットに見つかりません。")

        data = df[column_name].dropna()  # NaNを除外して計算

        stats_result = {
            "count": len(data),
            "mean": data.mean(),
            "std": data.std(),
            "median": data.median(),
            "min": data.min(),
            "max": data.max(),
        }
        self.logger.log_event(
            "ANALYZE_SUCCESS",
            f"{column_name} の記述統計量を計算しました。",
            "基礎的な統計指標が算出されました。",
        )
        return stats_result

    def calculate_qqplot(self, data: np.ndarray) -> plt.Figure:
        """
        データのQ-Qプロットを生成し、matplotlib Figureオブジェクトとして返す。

        Args:
            data (np.ndarray): 分析対象の一次元データ配列。

        Returns:
            plt.Figure: 生成されたmatplotlib Figureオブジェクト。
        """
        if data is None or len(data) < 2:
            raise ValueError(
                "Q-Qプロットを生成するには、少なくとも2つのデータポイントが必要です。"
            )

        # 新しいFigureとAxesを作成し、そこに描画を行うため、plot=plt の指定は行わず、
        # プロット関数自体が返すオブジェクトを取得するロジックに変更します。
        fig, ax = plt.subplots()
        stats.probplot(data, dist="norm", plot=ax)  # 'plot=ax' を使用して描画先を指定
        plt.close(fig)  # メモリリークを防ぐため、figureを閉じる (重要)
        return fig
