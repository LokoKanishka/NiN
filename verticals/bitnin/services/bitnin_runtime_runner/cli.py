"""
CLI for bitnin-runtime-runner.
"""
import argparse
import logging
import sys
import time
import uuid
from verticals.bitnin.services.bitnin_runtime_runner.runner import BitNinRuntimeRunner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("bitnin-runtime")

def main():
    parser = argparse.ArgumentParser(description="BitNin Runtime Runner (Operational Mode)")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol to analyze")
    parser.add_argument("--interval", default="1d", help="Interval (1d, 4h, 1h)")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve for demonstration")
    parser.add_argument("--period", type=int, default=3600, help="Period in seconds for continuous mode")
    parser.add_argument("--batch", type=int, default=1, help="Number of runs in batch mode")
    parser.add_argument("--sleep-seconds", type=int, default=10, help="Sleep between batch runs")

    args = parser.parse_args()

    runner = BitNinRuntimeRunner()

    if args.once:
        logger.info("Executing single BitNin cycle...")
        result = runner.run_once(
            symbol=args.symbol,
            interval=args.interval,
            auto_approve=args.auto_approve
        )
        logger.info(f"Done. Replay ID: {result['replay_id']}")
        sys.exit(0)

    if args.batch > 1:
        logger.info(f"Executing batch of {args.batch} cycles...")
        batch_id = f"batch_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
        results = []
        for i in range(args.batch):
            run_id = f"run_{batch_id}_{i+1}"
            logger.info(f"--- Batch {batch_id} | Run {i+1}/{args.batch} | ID: {run_id} ---")
            result = runner.run_once(
                symbol=args.symbol,
                interval=args.interval,
                auto_approve=args.auto_approve,
                run_id=run_id
            )
            results.append(result)
            if i < args.batch - 1:
                logger.info(f"Run completed. Sleeping for {args.sleep_seconds}s...")
                time.sleep(args.sleep_seconds)
        
        # Generate batch report
        report_path = runner.generate_batch_report(batch_id, results)
        logger.info(f"Batch completed. Report saved to: {report_path}")
        sys.exit(0)

    logger.info(f"Entering continuous operational mode. Period: {args.period}s")
    try:
        while True:
            logger.info("Starting scheduled cycle...")
            runner.run_once(
                symbol=args.symbol,
                interval=args.interval,
                auto_approve=args.auto_approve
            )
            logger.info(f"Cycle completed. Sleeping for {args.period}s")
            time.sleep(args.period)
    except KeyboardInterrupt:
        logger.info("Operational runner stopped by user.")
    except Exception as e:
        logger.error(f"Operational runner crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
