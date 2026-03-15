"""
Snapshot tool for bitnin-exec-guard.
Packages requests and results into reproducible bundles.
"""
import os
import tarfile
from datetime import datetime, timezone

RUNTIME_DIR = "/home/lucy-ubuntu/Escritorio/NIN/verticals/bitnin/runtime/execution"

class SnapshotManager:
    """Handles creating reproducible snapshots."""
    
    @staticmethod
    def create_snapshot(exec_id: str, req_path: str, res_path: str) -> str:
        """Creates a tarball of the request and result for auditability."""
        now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        snap_name = f"snapshot_{exec_id}_{now_str}.tar.gz"
        snap_path = os.path.join(RUNTIME_DIR, "snapshots", snap_name)
        
        with tarfile.open(snap_path, "w:gz") as tar:
            if os.path.exists(req_path):
                tar.add(req_path, arcname=os.path.basename(req_path))
            if os.path.exists(res_path):
                tar.add(res_path, arcname=os.path.basename(res_path))
                
        return snap_path
