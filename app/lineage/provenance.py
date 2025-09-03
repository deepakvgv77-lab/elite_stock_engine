from openlineage.client import OpenLineageClient

class LineageEmitter:
    def __init__(self):
        # Initialize client from environment variables or openlineage.yml configuration
        self.client = OpenLineageClient.from_environment()

    def emit_event(self, job_name: str, run_id: str, inputs: list, outputs: list):
        self.client.emit_run_event(job_name=job_name, run_id=run_id, inputs=inputs, outputs=outputs)
