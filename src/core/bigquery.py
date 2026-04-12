from datetime import UTC, datetime

from google.cloud import bigquery

from src.core.config import settings
from src.core.schema import AnalysisResult


class BigQueryManager:
    def __init__(self) -> None:
        # Clientの初期化（この時点では認証情報の検証のみ）
        self.client = bigquery.Client(project=settings.google_cloud_project)
        self.table_id = f"{settings.google_cloud_project}.{settings.bq_dataset}.{settings.bq_table}"

    def log_analysis(self, result: AnalysisResult) -> None:
        """
        解析結果を BigQuery にログとして保存します。
        バックグラウンドで実行されることを想定し、例外は内部でキャッチします。
        """
        try:
            # Pydantic モデルを辞書形式に変換し、タイムスタンプを追加
            # Pydantic のシリアライザを経由せず属性を直接参照して純粋な dict を組み立てる
            # success は BQ テーブルに存在しないため除外
            objects_list = [{"name": obj.name, "count": obj.count} for obj in result.objects]
            row = {
                "description": result.description,
                "objects": objects_list,
                "confidence_score": result.confidence_score,
                "created_at": datetime.now(UTC).isoformat(),
            }

            errors = self.client.insert_rows_json(self.table_id, [row])

            if errors:
                # 運用上、ここでのエラーで API 全体を止めないよう、ログ出力に留めるのが一般的
                # TODO: 本番環境では logger を推奨）
                print(f"[BigQuery] Insert Errors: {errors}")
            else:
                print("[BigQuery] Successfully logged analysis result.")

        except Exception as e:
            # バックグラウンドタスクがメインスレッドを落とさないよう、例外をキャッチ
            print(f"[BigQuery] Unexpected error during logging: {e}")


# シングルトンとしてインスタンス化
bq_manager = BigQueryManager()
