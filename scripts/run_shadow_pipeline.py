#!/usr/bin/env python3
import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from verticals.bitnin.services.bitnin_runtime_runner.runner import BitNinRuntimeRunner
from verticals.bitnin.services.bitnin_observability.scorecard import ScorecardGenerator
from verticals.bitnin.services.bitnin_analyst.context import CurrentContextBuilder

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bitnin_pipeline")

def main():
    parser = argparse.ArgumentParser(description="Run continuous BitNin shadow pipeline over a date window.")
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--append", action="store_true", help="Append results to longitudinal history")
    
    args = parser.parse_args()
    
    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    if end_dt < start_dt:
        logger.error("End date must be >= start date")
        sys.exit(1)
        
    logger.info("=============================================")
    logger.info("Initializing Continuous Shadow Pipeline (Fase 12)")
    logger.info("=============================================")
    
    ctx = CurrentContextBuilder()
    if not ctx.narrative_path.exists():
        logger.error(f"FATAL: Active Narrative Dataset not found at {ctx.narrative_path}")
        sys.exit(1)
    logger.info(f"Using Narrative Baseline: {ctx.narrative_path}")
        
    runner = BitNinRuntimeRunner()
    obs_root = runner.runtime_base / "observability"
    batches_dir = obs_root / "batches"
    scorecards_dir = obs_root / "scorecards"
    history_dir = obs_root / "history"
    
    # Ensure dirs exist
    for d in [batches_dir, scorecards_dir, history_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    history_path = history_dir / "longitudinal_history.json"
    
    # Unique batch id
    window_str = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
    batch_id = f"batch_{window_str}"
    results = []
    
    current_dt = start_dt
    while current_dt <= end_dt:
        as_of = current_dt.replace(hour=23, minute=59, second=59, microsecond=999000).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        run_id = f"sh_{current_dt.strftime('%Y%m%d')}"
        logger.info(f"\n---> Running tick for day {current_dt.strftime('%Y-%m-%d')} (as_of: {as_of})")
        
        try:
            res = runner.run_once(
                symbol="BTCUSDT",
                interval="1d",
                top_k=5,
                auto_approve=False,
                run_id=run_id,
                as_of=as_of
            )
            results.append(res)
            logger.info(f"     Status: {res['analyst_status']} | Action: {res['analyst_action']} | CompState: {res['composite_signal'].get('state', 'UNKNOWN')}")
            logger.info(f"     Causal Typology: {res['composite_signal'].get('causal_typology', 'UNKNOWN')} | Narrative Cover: {res['narrative_coverage_score']}")
            logger.info(f"     Active Memories: {res['active_memory_count']}")
        except Exception as e:
            logger.error(f"Tick {as_of} crashed: {e}")
            
        current_dt += timedelta(days=1)
        
    logger.info("\n=============================================")
    logger.info(f"Pipeline finished. Total runs: {len(results)}")
    
    # Generate Batch Report
    if results:
        # Save to batches/
        batch_report_path = runner.generate_batch_report(batch_id=batch_id, results=results)
        # Move it to batches folder for better organization
        permanent_batch_path = batches_dir / f"batch_report__{batch_id}.json"
        
        # We need to read it back since generate_batch_report writes to a fixed location usually
        import shutil
        shutil.move(str(batch_report_path), str(permanent_batch_path))
        
        logger.info(f"Batch report archived at: {permanent_batch_path}")
        
        # Output Scorecard
        gen = ScorecardGenerator(str(scorecards_dir), history_path=str(history_path) if args.append else None)
        scorecard_path, alerts = gen.generate(str(permanent_batch_path))
        logger.info(f"Scorecard archived at: {scorecard_path}")
        
        if any("🔴" in a or "🟠" in a or "🟡" in a for a in alerts if "HEALTHY" not in a):
            logger.warning("\nOBSERVABILITY ALERTS DETECTED:")
            for alert in alerts:
                if any(icon in alert for icon in ["🔴", "🟠", "🟡"]):
                    logger.warning(f"  {alert}")
        else:
            logger.info("System looks HEALTHY based on current window.")

if __name__ == "__main__":
    main()
