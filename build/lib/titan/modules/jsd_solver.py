import os
import json
import subprocess
import logging
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

class JSDSolver:
    """
    Wrapper for the external Go-based JSD Solver.
    """
    
    def __init__(self):
        self.binary_path = self._find_binary()
        if not self.binary_path:
            logger.debug("JSD Solver binary not found. Will rely on Browser Fallback.")
            
    def _find_binary(self) -> Optional[str]:
        # Look in titan/solver_go/jsd_solver.exe
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        potential_path = os.path.join(base_dir, "titan", "solver_go", "jsd_solver.exe")
        
        if os.path.exists(potential_path):
            return potential_path
            
        # Also check just "jsd_solver" for linux/mac
        potential_path_nix = os.path.join(base_dir, "titan", "solver_go", "jsd_solver")
        if os.path.exists(potential_path_nix):
            return potential_path_nix
            
        return None

    def is_available(self) -> bool:
        return self.binary_path is not None

    def solve(self, url: str, r: str = None, t: str = None, cookies: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Solve the JSD challenge.
        
        If r and t are provided, uses 'manual' mode (skips initial fetch).
        If not, uses 'auto' mode (fetches homepage first).
        """
        if not self.is_available():
            raise RuntimeError("JSD Solver binary is not available.")

        mode = "manual" if (r and t) else "auto"
        
        payload = {
            "mode": mode,
            "url": url,
            "r": r or "",
            "t": t or "",
            "cookies": cookies or {}
        }
        
        try:
            process = subprocess.Popen(
                [self.binary_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=json.dumps(payload))
            
            if stderr:
                logger.debug(f"JSD Solver Logs: {stderr}")
                
            if process.returncode != 0:
                logger.error(f"JSD Solver process failed with code {process.returncode}")
                return {"success": False, "error": f"Process exited with code {process.returncode}"}
                
            result = json.loads(stdout)
            return result
            
        except Exception as e:
            logger.exception("Error running JSD solver")
            return {"success": False, "error": str(e)}
