from .ingest_pipeline import ProjectIngestPipeline
from .retrieval_pipeline import RetrievalPipeline
from .base_pipeline import BasePipeline
from .utils import setup_pipeline_logger

class FullProjectPipeline(BasePipeline):

    def __init__(self, pid: int, filename: str):
        self.pid = pid
        self.filename = filename
        self.logger = setup_pipeline_logger("FullProjectPipeline")

    def run(self):

        self.logger.info("Running full project pipeline")

        # 1. Ingest
        ingest_result = ProjectIngestPipeline(
            pid=self.pid,
            filename=self.filename
        ).run()

        # 2. Sanity retrieval test
        retrieval_result = RetrievalPipeline(
            query="community benefits and employment",
            pid=self.pid,
            top_k=3
        ).run()

        return {
            "ingest": ingest_result,
            "retrieval_preview": retrieval_result
        }