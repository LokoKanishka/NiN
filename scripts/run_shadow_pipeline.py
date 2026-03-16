#!/usr/bin/env python3
import argparse
import sys
import logging
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
    
    args = parser.parse_args()
    
    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    
    if end_dt < start_dt:
        logger.error("End date must be >= start date")
        sys.exit(1)
        
    logger.info("=============================================")
    logger.info("Initializing Continuous Shadow Pipeline")
    logger.info("=============================================")
    
    ctx = CurrentContextBuilder()
    if not ctx.narrative_path.exists():
        logger.error(f"FATAL: Active Narrative Dataset not found at {ctx.narrative_path}")
        sys.exit(1)
    logger.info(f"Using Narrative Baseline: {ctx.narrative_path}")
        
    runner = BitNinRuntimeRunner()
    # Unique batch id
    window_str = f"{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}"
    batch_id = f"cont_shadow_{window_str}"
    results = []
    
    current_dt = start_dt
    while current_dt <= end_dt:
        # Construct exact 23:59:59.999Z for daily bars
        as_of = current_dt.replace(hour=23, minute=59, second=59, microsecond=999000).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        run_id = f"sh_{current_dt.strftime('%Y%m%d')}"
        logger.info(f"\n---> Running tick for day {current_dt.strftime('%Y-%m-%d')} (as_of: {as_of})")
        
        try:
            res = runner.run_once(
                symbol="BTCUSDT",
                interval="1d",
                top_k=5,
                auto_approve=False,  # Strict shadow/dry-run, no forced approval
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
        batch_report_path = runner.generate_batch_report(batch_id=batch_id, results=results)
        logger.info(f"Batch report stored at: {batch_report_path}")
        
        # Output Scorecard
        scorecard_dir = str(runner.runtime_base / "observability")
        gen = ScorecardGenerator(scorecard_dir)
        scorecard_path, alerts = gen.generate(batch_report_path)
        logger.info(f"Scorecard stored at: {scorecard_path}")
        
        if any("CRITICAL" in a or "DEGRADATION" in a for a in alerts):
            logger.warning("\nDEGRADATION ALERTS DETECTED:")
            for alert in alerts:
                if "DEGRADATION" in alert or "CRITICAL" in alert:
                    logger.warning(f"  {alert}")
        else:
            logger.info("Scorecard looks healthy.")
            for alert in alerts:
                logger.info(f"  {alert}")

if __name__ == "__main__":
    main()
