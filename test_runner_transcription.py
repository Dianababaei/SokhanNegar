"""
Test runner for comprehensive transcription accuracy testing.

Executes transcription tests across all scenarios, collects metrics,
and generates baseline/improvement reports.

Usage:
    python test_runner_transcription.py --mode baseline
    python test_runner_transcription.py --mode compare --baseline test_results/baseline_metrics.json
    python test_runner_transcription.py --scenario code-switching
    python test_runner_transcription.py --interactive
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import sys

from test_transcription_accuracy import (
    TranscriptionAccuracyFramework,
    create_test_data_directory,
    setup_ground_truth_samples
)

logger = logging.getLogger(__name__)


class TestRunnerManager:
    """Manages test execution and reporting."""
    
    def __init__(self, framework: TranscriptionAccuracyFramework):
        """
        Initialize test runner.
        
        Args:
            framework: TranscriptionAccuracyFramework instance
        """
        self.framework = framework
        self.ground_truth_data = {}
        self.test_results = {}
    
    def load_ground_truth_files(self) -> bool:
        """
        Load ground truth samples from test_data directory.
        
        Returns:
            bool: True if all ground truth files loaded successfully
        """
        test_data_dir = Path('test_data')
        if not test_data_dir.exists():
            logger.error(f"Test data directory not found: {test_data_dir}")
            return False
        
        scenarios = ['soft_spoken', 'emotional', 'code_switching', 'medical_terms', 'background_noise']
        
        for scenario in scenarios:
            ground_truth_file = test_data_dir / scenario / 'ground_truth.json'
            if not ground_truth_file.exists():
                logger.warning(f"Ground truth file not found for {scenario}: {ground_truth_file}")
                continue
            
            try:
                with open(ground_truth_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.ground_truth_data[scenario] = data
                logger.info(f"✓ Loaded {len(data.get('samples', []))} samples for {scenario}")
            except Exception as e:
                logger.error(f"Error loading ground truth for {scenario}: {e}")
                continue
        
        return len(self.ground_truth_data) > 0
    
    def register_test_samples(self) -> None:
        """Register all ground truth samples with the framework."""
        for scenario_key, scenario_data in self.ground_truth_data.items():
            for sample in scenario_data.get('samples', []):
                # Prepare sample for framework
                test_sample = {
                    'audio_file': sample.get('filename'),
                    'ground_truth': sample.get('ground_truth'),
                    'recognized_text': sample.get('recognized_text'),  # None by default
                    'confidence_responses': sample.get('confidence_responses', []),
                    'expected_medical_terms': sample.get('expected_medical_terms', []),
                    'expected_english_terms': sample.get('expected_english_terms', []),
                }
                
                self.framework.add_test_sample(scenario_key, test_sample)
                logger.debug(f"Registered sample {sample.get('id')} for {scenario_key}")
    
    def print_test_summary(self) -> None:
        """Print summary of loaded test scenarios."""
        logger.info("\n" + "="*80)
        logger.info("TRANSCRIPTION ACCURACY TEST FRAMEWORK - SCENARIO SUMMARY")
        logger.info("="*80)
        
        for scenario_key, scenario in self.framework.test_scenarios.items():
            sample_count = len(scenario['samples'])
            logger.info(f"\n{scenario['name']}")
            logger.info(f"  Description: {scenario['description']}")
            logger.info(f"  Samples loaded: {sample_count}")
            
            if sample_count > 0 and scenario['samples']:
                for sample in scenario['samples'][:2]:  # Show first 2
                    logger.info(f"    - {sample.get('audio_file', 'unknown')}")
                if sample_count > 2:
                    logger.info(f"    ... and {sample_count - 2} more")
        
        logger.info("\n" + "="*80)
    
    def run_baseline_test(self) -> Dict:
        """
        Run baseline test on all scenarios.
        
        Returns:
            Dictionary with baseline metrics
        """
        logger.info("Running BASELINE test...")
        logger.info("Note: Samples without recognized_text will be skipped")
        
        report = self.framework.generate_baseline_report('baseline_metrics.json')
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("BASELINE METRICS SUMMARY")
        logger.info("="*80)
        
        targets = report.get('improvement_targets', {})
        for metric_name, metric_data in targets.items():
            baseline = metric_data.get('current_baseline')
            target = metric_data.get('target')
            description = metric_data.get('description')
            
            if baseline is not None:
                status = "✓ PASS" if _check_target_met(metric_name, baseline, target) else "⚠ NEEDS WORK"
                logger.info(f"\n{metric_name.upper()}")
                logger.info(f"  {description}")
                logger.info(f"  Baseline: {baseline:.3f}")
                logger.info(f"  Target: {target:.3f}")
                logger.info(f"  Status: {status}")
            else:
                logger.info(f"\n{metric_name.upper()}")
                logger.info(f"  {description}")
                logger.info(f"  Status: ⚠ NO DATA (no samples with recognized_text)")
        
        logger.info("\n" + "="*80)
        return report
    
    def run_scenario_test(self, scenario_key: str) -> Dict:
        """
        Run test for a specific scenario.
        
        Args:
            scenario_key: Scenario identifier
            
        Returns:
            Dictionary with scenario metrics
        """
        if scenario_key not in self.framework.test_scenarios:
            logger.error(f"Unknown scenario: {scenario_key}")
            return {}
        
        logger.info(f"\nRunning test for scenario: {scenario_key}")
        
        metrics = self.framework.calculate_scenario_metrics(scenario_key)
        
        logger.info(f"Results for {scenario_key}:")
        logger.info(f"  Sample count: {metrics.get('sample_count', 0)}")
        logger.info(f"  Avg WER: {metrics.get('avg_wer', 'N/A')}")
        logger.info(f"  Avg Medical Accuracy: {metrics.get('avg_medical_accuracy', 'N/A')}")
        logger.info(f"  Avg Code-Switch Accuracy: {metrics.get('avg_code_switch_accuracy', 'N/A')}")
        logger.info(f"  Avg Confidence: {metrics.get('avg_confidence', 'N/A')}")
        
        return metrics
    
    def run_comparison_test(self, baseline_file: str) -> Dict:
        """
        Run comparison test against baseline.
        
        Args:
            baseline_file: Path to baseline metrics JSON file
            
        Returns:
            Dictionary with improvement metrics
        """
        logger.info(f"Running COMPARISON test against baseline: {baseline_file}")
        
        report = self.framework.generate_comparison_report(baseline_file)
        
        logger.info("\n" + "="*80)
        logger.info("IMPROVEMENT REPORT SUMMARY")
        logger.info("="*80)
        
        improvements = report.get('improvements', {})
        for scenario_key, scenario_improvements in improvements.items():
            logger.info(f"\n{scenario_key}:")
            
            wer_imp = scenario_improvements.get('wer_improvement', {})
            if wer_imp.get('baseline') is not None:
                improvement = wer_imp.get('improvement_percent', 0)
                direction = "↓ Improved" if improvement > 0 else ("↑ Regressed" if improvement < 0 else "= No change")
                logger.info(f"  WER: {wer_imp.get('baseline'):.3f} → {wer_imp.get('current'):.3f} ({direction}: {improvement:.1f}%)")
            
            med_imp = scenario_improvements.get('medical_accuracy_improvement', {})
            if med_imp.get('baseline') is not None:
                improvement = med_imp.get('improvement_percent', 0)
                direction = "↑ Improved" if improvement > 0 else ("↓ Regressed" if improvement < 0 else "= No change")
                logger.info(f"  Medical Accuracy: {med_imp.get('baseline'):.3f} → {med_imp.get('current'):.3f} ({direction}: {improvement:.1f}%)")
            
            code_imp = scenario_improvements.get('code_switch_improvement', {})
            if code_imp.get('baseline') is not None:
                improvement = code_imp.get('improvement_percent', 0)
                direction = "↑ Improved" if improvement > 0 else ("↓ Regressed" if improvement < 0 else "= No change")
                logger.info(f"  Code-Switch Accuracy: {code_imp.get('baseline'):.3f} → {code_imp.get('current'):.3f} ({direction}: {improvement:.1f}%)")
        
        logger.info("\n" + "="*80)
        return report


def _check_target_met(metric_name: str, baseline: float, target: float) -> bool:
    """
    Check if metric meets target based on metric type.
    
    Args:
        metric_name: Name of the metric
        baseline: Current baseline value
        target: Target value
        
    Returns:
        bool: True if target is met
    """
    if 'wer' in metric_name.lower():
        # For WER, lower is better
        return baseline <= target
    else:
        # For accuracy metrics, higher is better
        return baseline >= target


def print_usage_instructions() -> None:
    """Print usage instructions for the framework."""
    logger.info("\n" + "="*80)
    logger.info("TRANSCRIPTION ACCURACY TESTING FRAMEWORK")
    logger.info("="*80)
    logger.info("\nQuick Start Guide:")
    logger.info("\n1. SETUP TEST DATA")
    logger.info("   - Test data directory created: test_data/")
    logger.info("   - Ground truth samples in: test_data/{scenario}/ground_truth.json")
    logger.info("   - Audio samples should be placed in: test_data/{scenario}/*.wav")
    logger.info("\n2. RUN BASELINE TEST")
    logger.info("   python test_runner_transcription.py --mode baseline")
    logger.info("   Creates: test_results/baseline_metrics.json")
    logger.info("\n3. MEASURE IMPROVEMENTS")
    logger.info("   python test_runner_transcription.py --mode compare \\")
    logger.info("     --baseline test_results/baseline_metrics.json")
    logger.info("   Creates: test_results/improvement_report.json")
    logger.info("\n4. TEST SPECIFIC SCENARIO")
    logger.info("   python test_runner_transcription.py --scenario code-switching")
    logger.info("\nAvailable Scenarios:")
    logger.info("   - soft_spoken: Low-energy depressed/quiet speech")
    logger.info("   - emotional: Speech with emotional variations")
    logger.info("   - code_switching: Persian-English medical terminology")
    logger.info("   - medical_terms: DSM-5 psychiatric terminology")
    logger.info("   - background_noise: Speech with background noise")
    logger.info("\n5. INTEGRATION WITH SOKHANEGAR")
    logger.info("   - Run SokhanNegar.py to transcribe test audio files")
    logger.info("   - Add recognized_text to ground truth JSON files")
    logger.info("   - Re-run baseline test to measure accuracy")
    logger.info("\n" + "="*80 + "\n")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description='Comprehensive Transcription Accuracy Testing Framework'
    )
    parser.add_argument(
        '--mode',
        choices=['baseline', 'compare', 'setup'],
        default='setup',
        help='Test mode: baseline (establish metrics), compare (measure improvements), or setup (initialize)'
    )
    parser.add_argument(
        '--scenario',
        choices=['soft_spoken', 'emotional', 'code_switching', 'medical_terms', 'background_noise'],
        help='Run test for specific scenario'
    )
    parser.add_argument(
        '--baseline',
        type=str,
        help='Path to baseline metrics JSON file (for compare mode)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('test_runner.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("="*80)
    logger.info("TRANSCRIPTION ACCURACY TEST RUNNER")
    logger.info("="*80)
    
    # Setup test data if needed
    if args.mode == 'setup' or not Path('test_data').exists():
        logger.info("\nInitializing test data structure...")
        create_test_data_directory()
        setup_ground_truth_samples()
        logger.info("✓ Test data initialization complete")
        if args.mode == 'setup':
            print_usage_instructions()
            return 0
    
    # Initialize framework
    logger.info("\nInitializing transcription accuracy framework...")
    framework = TranscriptionAccuracyFramework()
    
    # Initialize runner
    runner = TestRunnerManager(framework)
    
    # Load ground truth
    logger.info("Loading ground truth samples...")
    if not runner.load_ground_truth_files():
        logger.error("Failed to load any ground truth files")
        print_usage_instructions()
        return 1
    
    # Register samples with framework
    runner.register_test_samples()
    
    # Print summary
    runner.print_test_summary()
    
    # Run tests based on mode
    try:
        if args.scenario:
            logger.info(f"\nRunning test for scenario: {args.scenario}")
            results = runner.run_scenario_test(args.scenario)
            return 0
        
        elif args.mode == 'baseline':
            logger.info("\nRunning BASELINE test mode...")
            results = runner.run_baseline_test()
            return 0
        
        elif args.mode == 'compare':
            if not args.baseline:
                logger.error("--baseline file required for compare mode")
                parser.print_help()
                return 1
            
            logger.info(f"\nRunning COMPARISON test mode...")
            results = runner.run_comparison_test(args.baseline)
            return 0
        
        elif args.interactive:
            # Interactive mode
            print_usage_instructions()
            return 0
        
        else:
            # Default: print usage
            print_usage_instructions()
            return 0
    
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
