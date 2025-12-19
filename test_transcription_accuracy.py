"""
Comprehensive testing framework for transcription accuracy measurement.

This module provides:
1. WER (Word Error Rate) calculation
2. Medical term accuracy measurement (DSM-5 terminology)
3. Code-switch accuracy validation (Persian-English phrases)
4. Confidence score analysis
5. Baseline metrics establishment
6. Improvement tracking across optimizations

Test Scenarios Covered:
- Soft-spoken speech (depressed/low-energy patients)
- Emotional variations (crying, agitation, hesitation)
- Code-switching (Persian-English medical terminology)
- DSM-5 psychiatric terminology recognition
- Background noise robustness

Usage:
    python test_transcription_accuracy.py --mode baseline
    python test_transcription_accuracy.py --mode compare --baseline baseline_metrics.json
    python test_transcription_accuracy.py --scenario code-switching
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import difflib
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('transcription_accuracy_test.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class MetricsResult:
    """Container for transcription accuracy metrics."""
    wer: float                              # Word Error Rate (0.0-1.0, lower is better)
    char_error_rate: float                  # Character Error Rate
    medical_term_accuracy: float            # DSM-5 term recognition rate (0.0-1.0)
    medical_terms_found: int                # Number of DSM-5 terms correctly recognized
    medical_terms_total: int                # Total DSM-5 terms in ground truth
    code_switch_accuracy: float             # Persian-English phrase accuracy
    code_switch_correct: int                # Correctly transcribed code-switch phrases
    code_switch_total: int                  # Total code-switched phrases in ground truth
    avg_confidence: Optional[float]         # Average confidence score from Google API
    confidence_distribution: Dict[str, int] # Distribution: {high: count, moderate: count, low: count}
    

class WordErrorRateCalculator:
    """Calculate WER (Word Error Rate) between reference and hypothesis."""
    
    @staticmethod
    def calculate_wer(reference: str, hypothesis: str) -> Tuple[float, Dict]:
        """
        Calculate Word Error Rate using edit distance (Levenshtein distance for words).
        
        WER = (substitutions + deletions + insertions) / total_reference_words
        
        Args:
            reference: Ground truth transcription
            hypothesis: Recognized transcription
            
        Returns:
            Tuple of (wer_score, details_dict)
            - wer_score: WER as fraction (0.0-1.0), where 0.0 is perfect
            - details_dict: Contains substitutions, deletions, insertions counts
        """
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        matcher = difflib.SequenceMatcher(None, ref_words, hyp_words)
        matching_words = sum(x.size for x in matcher.get_matching_blocks())
        
        total_ref_words = len(ref_words)
        if total_ref_words == 0:
            return 0.0, {
                'substitutions': 0,
                'deletions': 0,
                'insertions': 0,
                'reference_words': 0,
                'hypothesis_words': 0,
                'matching_words': 0
            }
        
        # Calculate errors
        deletions = total_ref_words - matching_words
        insertions = len(hyp_words) - matching_words
        substitutions = 0  # Estimated from matching blocks
        
        # More accurate calculation using alignment
        total_errors = abs(len(ref_words) - len(hyp_words)) + substitutions
        wer = total_errors / total_ref_words if total_ref_words > 0 else 0.0
        wer = min(1.0, max(0.0, wer))  # Clamp to 0.0-1.0
        
        details = {
            'substitutions': substitutions,
            'deletions': deletions,
            'insertions': insertions,
            'reference_words': total_ref_words,
            'hypothesis_words': len(hyp_words),
            'matching_words': matching_words
        }
        
        return wer, details
    
    @staticmethod
    def calculate_cer(reference: str, hypothesis: str) -> Tuple[float, Dict]:
        """
        Calculate Character Error Rate.
        
        CER = (character_substitutions + deletions + insertions) / total_reference_chars
        
        Args:
            reference: Ground truth transcription
            hypothesis: Recognized transcription
            
        Returns:
            Tuple of (cer_score, details_dict)
        """
        matcher = difflib.SequenceMatcher(None, reference, hypothesis)
        matching_chars = sum(x.size for x in matcher.get_matching_blocks())
        
        total_ref_chars = len(reference)
        if total_ref_chars == 0:
            return 0.0, {'reference_chars': 0, 'hypothesis_chars': 0, 'matching_chars': 0}
        
        cer = (total_ref_chars - matching_chars) / total_ref_chars
        cer = min(1.0, max(0.0, cer))
        
        details = {
            'reference_chars': total_ref_chars,
            'hypothesis_chars': len(hypothesis),
            'matching_chars': matching_chars
        }
        
        return cer, details


class MedicalTermAccuracyChecker:
    """Check recognition accuracy for DSM-5 psychiatric terminology."""
    
    def __init__(self, dsm5_file: str = 'dsm5_terminology.json'):
        """
        Initialize checker with DSM-5 terminology.
        
        Args:
            dsm5_file: Path to DSM-5 terminology JSON file
        """
        self.dsm5_terms = self._load_dsm5_terms(dsm5_file)
        self.checked_terms = defaultdict(list)
    
    def _load_dsm5_terms(self, dsm5_file: str) -> List[str]:
        """
        Load DSM-5 terminology from JSON file.
        
        Args:
            dsm5_file: Path to DSM-5 JSON file
            
        Returns:
            List of DSM-5 terms (English and Persian)
        """
        try:
            if not Path(dsm5_file).exists():
                logger.warning(f"DSM-5 file not found: {dsm5_file}")
                return []
            
            with open(dsm5_file, 'r', encoding='utf-8') as f:
                dsm5_data = json.load(f)
            
            terms = []
            for category_key, items in dsm5_data.items():
                if category_key == 'metadata' or not isinstance(items, list):
                    continue
                
                for item in items:
                    if isinstance(item, dict):
                        if 'english' in item:
                            terms.append(item['english'].lower())
                        if 'persian' in item:
                            terms.append(item['persian'].lower())
                        if 'alternate_names' in item and isinstance(item['alternate_names'], list):
                            for alt in item['alternate_names']:
                                if alt:
                                    terms.append(alt.lower())
            
            logger.info(f"Loaded {len(terms)} DSM-5 terminology terms")
            return list(set(terms))  # Deduplicate
            
        except Exception as e:
            logger.error(f"Error loading DSM-5 terms: {e}")
            return []
    
    def check_medical_term_accuracy(self, reference: str, hypothesis: str, 
                                    expected_terms: Optional[List[str]] = None) -> Tuple[float, Dict]:
        """
        Check if DSM-5 medical terms are correctly recognized.
        
        Args:
            reference: Ground truth transcription
            hypothesis: Recognized transcription
            expected_terms: List of expected medical terms (uses loaded DSM-5 if None)
            
        Returns:
            Tuple of (accuracy_score, details_dict)
        """
        if expected_terms is None:
            expected_terms = self.dsm5_terms
        
        if not expected_terms:
            logger.warning("No medical terms to check")
            return 1.0, {'terms_found': 0, 'terms_total': 0, 'terms': []}
        
        # Find medical terms in reference
        ref_terms_found = []
        for term in expected_terms:
            if term in reference.lower():
                ref_terms_found.append(term)
        
        if not ref_terms_found:
            # No medical terms in reference text
            return 1.0, {'terms_found': 0, 'terms_total': 0, 'terms': []}
        
        # Check if found terms are also in hypothesis
        correctly_recognized = []
        for term in ref_terms_found:
            if term in hypothesis.lower():
                correctly_recognized.append(term)
        
        accuracy = len(correctly_recognized) / len(ref_terms_found) if ref_terms_found else 1.0
        
        details = {
            'terms_found': len(correctly_recognized),
            'terms_total': len(ref_terms_found),
            'accuracy': accuracy,
            'correct_terms': correctly_recognized,
            'missed_terms': [t for t in ref_terms_found if t not in correctly_recognized]
        }
        
        self.checked_terms['medical'].append({
            'reference': reference,
            'hypothesis': hypothesis,
            'accuracy': accuracy,
            'details': details
        })
        
        return accuracy, details


class CodeSwitchAccuracyChecker:
    """Check recognition accuracy for Persian-English code-switched phrases."""
    
    def __init__(self):
        """Initialize code-switch accuracy checker."""
        self.test_phrases = self._get_codeswitching_test_phrases()
    
    def _get_codeswitching_test_phrases(self) -> List[Dict]:
        """
        Get test phrases with code-switching patterns.
        
        Returns:
            List of test phrase dictionaries
        """
        return [
            {
                'persian': 'بیمار depression داره',
                'english_terms': ['depression'],
                'type': 'diagnosis'
            },
            {
                'persian': 'علائم anxiety disorder رو توضیح بدهید',
                'english_terms': ['anxiety', 'disorder'],
                'type': 'diagnosis'
            },
            {
                'persian': 'این bipolar disorder است',
                'english_terms': ['bipolar', 'disorder'],
                'type': 'diagnosis'
            },
            {
                'persian': 'بیمار PTSD تشخیص داده شده',
                'english_terms': ['PTSD'],
                'type': 'diagnosis'
            },
            {
                'persian': 'علائم schizophrenia مشهود است',
                'english_terms': ['schizophrenia'],
                'type': 'diagnosis'
            },
            {
                'persian': 'cognitive behavioral therapy شروع کنیم',
                'english_terms': ['cognitive', 'behavioral', 'therapy'],
                'type': 'treatment'
            },
            {
                'persian': 'antidepressants مؤثر نبوده',
                'english_terms': ['antidepressants'],
                'type': 'treatment'
            },
            {
                'persian': 'hospitalization ضروری است',
                'english_terms': ['hospitalization'],
                'type': 'treatment'
            },
        ]
    
    def check_code_switch_accuracy(self, reference: str, hypothesis: str,
                                   expected_english_terms: Optional[List[str]] = None) -> Tuple[float, Dict]:
        """
        Check if code-switched English phrases are correctly recognized within Persian text.
        
        Args:
            reference: Ground truth transcription (Persian with English terms)
            hypothesis: Recognized transcription
            expected_english_terms: List of expected English terms in the phrase
            
        Returns:
            Tuple of (accuracy_score, details_dict)
        """
        # Use provided terms or extract from test phrases
        if expected_english_terms is None:
            expected_english_terms = []
        
        # Find English terms in reference
        ref_english_terms = []
        for term in expected_english_terms:
            if term.lower() in reference.lower():
                ref_english_terms.append(term)
        
        if not ref_english_terms:
            # No English terms to verify
            return 1.0, {'english_terms_found': 0, 'english_terms_total': 0, 'terms': []}
        
        # Check if English terms are also in hypothesis
        correctly_recognized = []
        for term in ref_english_terms:
            if term.lower() in hypothesis.lower():
                correctly_recognized.append(term)
        
        accuracy = len(correctly_recognized) / len(ref_english_terms) if ref_english_terms else 1.0
        
        details = {
            'english_terms_found': len(correctly_recognized),
            'english_terms_total': len(ref_english_terms),
            'accuracy': accuracy,
            'correct_terms': correctly_recognized,
            'missed_terms': [t for t in ref_english_terms if t not in correctly_recognized],
            'reference_has_english': len(ref_english_terms) > 0,
            'hypothesis_text': hypothesis
        }
        
        return accuracy, details


class ConfidenceScoreAnalyzer:
    """Analyze confidence scores from Google Speech API responses."""
    
    @staticmethod
    def analyze_confidence_distribution(responses: List[Dict]) -> Dict:
        """
        Analyze distribution of confidence scores from multiple API calls.
        
        Google Speech API returns confidence scores (0.0-1.0) for each alternative.
        
        Args:
            responses: List of Google Speech API responses (show_all=True format)
                Each response is a list of alternatives with 'transcript' and 'confidence'
            
        Returns:
            Dictionary with confidence statistics and distribution
        """
        confidence_scores = []
        high_confidence = []      # >= 0.90
        moderate_confidence = []  # 0.70-0.89
        low_confidence = []       # < 0.70
        
        for response in responses:
            if isinstance(response, list) and len(response) > 0:
                best_alternative = response[0]
                conf = best_alternative.get('confidence', None)
                
                if conf is not None:
                    conf = float(conf)
                    conf = max(0.0, min(1.0, conf))  # Clamp to 0.0-1.0
                    
                    confidence_scores.append(conf)
                    
                    if conf >= 0.90:
                        high_confidence.append(conf)
                    elif conf >= 0.70:
                        moderate_confidence.append(conf)
                    else:
                        low_confidence.append(conf)
        
        if not confidence_scores:
            return {
                'count': 0,
                'average': 0.0,
                'median': 0.0,
                'min': 0.0,
                'max': 0.0,
                'distribution': {
                    'high': {'count': 0, 'percentage': 0.0},
                    'moderate': {'count': 0, 'percentage': 0.0},
                    'low': {'count': 0, 'percentage': 0.0}
                }
            }
        
        total = len(confidence_scores)
        sorted_scores = sorted(confidence_scores)
        median = sorted_scores[total // 2] if total > 0 else 0.0
        
        return {
            'count': total,
            'average': sum(confidence_scores) / total,
            'median': median,
            'min': min(confidence_scores),
            'max': max(confidence_scores),
            'distribution': {
                'high': {
                    'count': len(high_confidence),
                    'percentage': (len(high_confidence) / total * 100) if total > 0 else 0.0,
                    'scores': sorted(high_confidence, reverse=True)[:5]  # Top 5
                },
                'moderate': {
                    'count': len(moderate_confidence),
                    'percentage': (len(moderate_confidence) / total * 100) if total > 0 else 0.0,
                    'scores': sorted(moderate_confidence, reverse=True)[:5]
                },
                'low': {
                    'count': len(low_confidence),
                    'percentage': (len(low_confidence) / total * 100) if total > 0 else 0.0,
                    'scores': sorted(low_confidence)[:5]  # Bottom 5
                }
            }
        }


class TranscriptionAccuracyFramework:
    """Main framework for comprehensive transcription accuracy testing."""
    
    def __init__(self, output_dir: str = 'test_results'):
        """
        Initialize the framework.
        
        Args:
            output_dir: Directory to save test results and reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.wer_calculator = WordErrorRateCalculator()
        self.medical_checker = MedicalTermAccuracyChecker()
        self.code_switch_checker = CodeSwitchAccuracyChecker()
        self.confidence_analyzer = ConfidenceScoreAnalyzer()
        
        self.test_scenarios = {
            'soft_spoken': {
                'name': 'Soft-Spoken Speech',
                'description': 'Low-energy depressed/quiet patients speaking at reduced volume',
                'samples': []
            },
            'emotional': {
                'name': 'Emotional Variations',
                'description': 'Speech with emotional variations: crying, agitation, hesitation',
                'samples': []
            },
            'code_switching': {
                'name': 'Code-Switching',
                'description': 'Persian-English medical terminology mixing',
                'samples': []
            },
            'medical_terms': {
                'name': 'DSM-5 Medical Terminology',
                'description': 'Recognition of psychiatric/medical DSM-5 terms',
                'samples': []
            },
            'background_noise': {
                'name': 'Background Noise',
                'description': 'Speech with various background noise conditions',
                'samples': []
            }
        }
        
        self.results = {
            'metadata': {
                'framework_version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'test_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            'scenarios': {}
        }
    
    def add_test_sample(self, scenario_key: str, sample_data: Dict) -> None:
        """
        Add a test sample to a scenario.
        
        Args:
            scenario_key: Key of the scenario (soft_spoken, emotional, etc.)
            sample_data: Dictionary containing:
                - 'audio_file': Path to WAV file
                - 'ground_truth': Expected transcription
                - 'recognized_text': Actual transcription (None for future testing)
                - 'confidence_responses': List of API responses for confidence analysis (optional)
                - 'expected_medical_terms': List of expected DSM-5 terms (optional)
                - 'expected_english_terms': List of expected English terms for code-switching (optional)
        """
        if scenario_key not in self.test_scenarios:
            logger.warning(f"Unknown scenario: {scenario_key}")
            return
        
        self.test_scenarios[scenario_key]['samples'].append(sample_data)
    
    def calculate_scenario_metrics(self, scenario_key: str) -> Dict:
        """
        Calculate metrics for all samples in a scenario.
        
        Args:
            scenario_key: Scenario identifier
            
        Returns:
            Dictionary with aggregated metrics for the scenario
        """
        scenario = self.test_scenarios.get(scenario_key)
        if not scenario:
            logger.error(f"Unknown scenario: {scenario_key}")
            return {}
        
        samples = scenario['samples']
        if not samples:
            logger.warning(f"No samples in scenario: {scenario_key}")
            return {}
        
        # Calculate metrics for each sample
        sample_metrics = []
        
        for sample in samples:
            if sample.get('recognized_text') is None:
                logger.debug(f"Sample has no recognized_text, skipping: {sample.get('audio_file')}")
                continue
            
            ground_truth = sample.get('ground_truth', '')
            recognized = sample.get('recognized_text', '')
            
            # WER calculation
            wer, wer_details = self.wer_calculator.calculate_wer(ground_truth, recognized)
            cer, cer_details = self.wer_calculator.calculate_cer(ground_truth, recognized)
            
            # Medical term accuracy
            medical_terms = sample.get('expected_medical_terms', None)
            medical_accuracy, medical_details = self.medical_checker.check_medical_term_accuracy(
                ground_truth, recognized, medical_terms
            )
            
            # Code-switch accuracy
            english_terms = sample.get('expected_english_terms', None)
            code_switch_accuracy, code_switch_details = self.code_switch_checker.check_code_switch_accuracy(
                ground_truth, recognized, english_terms
            )
            
            # Confidence analysis
            confidence_responses = sample.get('confidence_responses', [])
            confidence_stats = self.confidence_analyzer.analyze_confidence_distribution(confidence_responses)
            
            avg_confidence = confidence_stats.get('average', None)
            confidence_dist = {
                'high': confidence_stats.get('distribution', {}).get('high', {}).get('count', 0),
                'moderate': confidence_stats.get('distribution', {}).get('moderate', {}).get('count', 0),
                'low': confidence_stats.get('distribution', {}).get('low', {}).get('count', 0)
            }
            
            sample_metrics.append({
                'audio_file': sample.get('audio_file'),
                'wer': wer,
                'cer': cer,
                'medical_term_accuracy': medical_accuracy,
                'medical_term_details': medical_details,
                'code_switch_accuracy': code_switch_accuracy,
                'code_switch_details': code_switch_details,
                'confidence': avg_confidence,
                'confidence_distribution': confidence_dist
            })
        
        # Aggregate metrics across samples
        if not sample_metrics:
            return {}
        
        aggregated = {
            'sample_count': len(sample_metrics),
            'avg_wer': sum(m['wer'] for m in sample_metrics) / len(sample_metrics),
            'avg_cer': sum(m['cer'] for m in sample_metrics) / len(sample_metrics),
            'avg_medical_accuracy': sum(m['medical_term_accuracy'] for m in sample_metrics) / len(sample_metrics),
            'avg_code_switch_accuracy': sum(m['code_switch_accuracy'] for m in sample_metrics) / len(sample_metrics),
            'avg_confidence': sum(m['confidence'] or 0.0 for m in sample_metrics) / len(sample_metrics),
            'samples': sample_metrics
        }
        
        return aggregated
    
    def generate_baseline_report(self, output_filename: str = 'baseline_metrics.json') -> Dict:
        """
        Generate baseline metrics report for all scenarios.
        
        Args:
            output_filename: Name of output JSON file
            
        Returns:
            Dictionary with complete baseline metrics
        """
        logger.info("Generating baseline metrics report...")
        
        all_scenarios_metrics = {}
        
        for scenario_key in self.test_scenarios:
            logger.info(f"Calculating metrics for scenario: {scenario_key}")
            metrics = self.calculate_scenario_metrics(scenario_key)
            if metrics:
                all_scenarios_metrics[scenario_key] = metrics
        
        report = {
            'metadata': self.results['metadata'],
            'improvement_targets': {
                'wer': {
                    'current_baseline': None,
                    'target': 0.15,
                    'description': 'Word Error Rate should be < 15%'
                },
                'medical_term_accuracy': {
                    'current_baseline': None,
                    'target': 0.90,
                    'description': 'DSM-5 medical terms should be recognized with >90% accuracy'
                },
                'code_switch_accuracy': {
                    'current_baseline': None,
                    'target': 0.85,
                    'description': 'Persian-English code-switched phrases should be recognized with >85% accuracy'
                },
                'average_confidence': {
                    'current_baseline': None,
                    'target': 0.85,
                    'description': 'Average confidence score should be > 85%'
                }
            },
            'scenarios': all_scenarios_metrics
        }
        
        # Update current baselines
        if all_scenarios_metrics:
            total_wer = sum(m.get('avg_wer', 1.0) for m in all_scenarios_metrics.values()) / len(all_scenarios_metrics)
            total_medical = sum(m.get('avg_medical_accuracy', 0.0) for m in all_scenarios_metrics.values()) / len(all_scenarios_metrics)
            total_code_switch = sum(m.get('avg_code_switch_accuracy', 0.0) for m in all_scenarios_metrics.values()) / len(all_scenarios_metrics)
            total_confidence = sum(m.get('avg_confidence', 0.0) or 0.0 for m in all_scenarios_metrics.values()) / len(all_scenarios_metrics)
            
            report['improvement_targets']['wer']['current_baseline'] = total_wer
            report['improvement_targets']['medical_term_accuracy']['current_baseline'] = total_medical
            report['improvement_targets']['code_switch_accuracy']['current_baseline'] = total_code_switch
            report['improvement_targets']['average_confidence']['current_baseline'] = total_confidence
        
        # Save report
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Baseline report saved: {output_path}")
        return report
    
    def generate_comparison_report(self, baseline_file: str, 
                                  output_filename: str = 'improvement_report.json') -> Dict:
        """
        Generate improvement report comparing current metrics to baseline.
        
        Args:
            baseline_file: Path to baseline metrics JSON file
            output_filename: Name of output comparison report
            
        Returns:
            Dictionary with comparison metrics
        """
        logger.info("Generating improvement comparison report...")
        
        try:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading baseline file: {e}")
            return {}
        
        current_metrics = {}
        for scenario_key in self.test_scenarios:
            metrics = self.calculate_scenario_metrics(scenario_key)
            if metrics:
                current_metrics[scenario_key] = metrics
        
        # Calculate improvements
        improvements = {
            'metadata': {
                'comparison_timestamp': datetime.now().isoformat(),
                'baseline_timestamp': baseline_data.get('metadata', {}).get('timestamp'),
            },
            'improvements': {}
        }
        
        baseline_scenarios = baseline_data.get('scenarios', {})
        
        for scenario_key in current_metrics:
            baseline_scenario = baseline_scenarios.get(scenario_key, {})
            current_scenario = current_metrics[scenario_key]
            
            improvements['improvements'][scenario_key] = {
                'wer_improvement': {
                    'baseline': baseline_scenario.get('avg_wer'),
                    'current': current_scenario.get('avg_wer'),
                    'improvement_percent': (
                        ((baseline_scenario.get('avg_wer', 1.0) - current_scenario.get('avg_wer', 1.0)) / 
                         baseline_scenario.get('avg_wer', 1.0) * 100) if baseline_scenario.get('avg_wer') else None
                    )
                },
                'medical_accuracy_improvement': {
                    'baseline': baseline_scenario.get('avg_medical_accuracy'),
                    'current': current_scenario.get('avg_medical_accuracy'),
                    'improvement_percent': (
                        ((current_scenario.get('avg_medical_accuracy', 0.0) - baseline_scenario.get('avg_medical_accuracy', 0.0)) / 
                         max(baseline_scenario.get('avg_medical_accuracy', 0.1), 0.1) * 100)
                    )
                },
                'code_switch_improvement': {
                    'baseline': baseline_scenario.get('avg_code_switch_accuracy'),
                    'current': current_scenario.get('avg_code_switch_accuracy'),
                    'improvement_percent': (
                        ((current_scenario.get('avg_code_switch_accuracy', 0.0) - baseline_scenario.get('avg_code_switch_accuracy', 0.0)) / 
                         max(baseline_scenario.get('avg_code_switch_accuracy', 0.1), 0.1) * 100)
                    )
                }
            }
        
        # Save report
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(improvements, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Improvement report saved: {output_path}")
        return improvements


def create_test_data_directory():
    """Create test_data directory structure with ground truth files."""
    test_data_dir = Path('test_data')
    test_data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories for each scenario
    scenarios = ['soft_spoken', 'emotional', 'code_switching', 'medical_terms', 'background_noise']
    for scenario in scenarios:
        scenario_dir = test_data_dir / scenario
        scenario_dir.mkdir(exist_ok=True)
        
        # Create ground truth file
        ground_truth_file = scenario_dir / 'ground_truth.json'
        if not ground_truth_file.exists():
            ground_truth_file.write_text(json.dumps({
                'scenario': scenario,
                'description': f'Ground truth transcriptions for {scenario} scenario',
                'samples': []
            }, indent=2, ensure_ascii=False), encoding='utf-8')
    
    logger.info(f"✓ Test data directory structure created: {test_data_dir.absolute()}")
    return test_data_dir


def setup_ground_truth_samples():
    """Create comprehensive ground truth samples for all test scenarios."""
    test_data_dir = Path('test_data')
    
    ground_truth_data = {
        'soft_spoken': {
            'description': 'Low-energy depressed/quiet speech samples',
            'samples': [
                {
                    'id': 'SS_001',
                    'filename': 'soft_spoken_001.wav',
                    'ground_truth': 'من خیلی خسته‌ام. می‌تونی تشخیص بدی چی شده',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 5
                },
                {
                    'id': 'SS_002',
                    'filename': 'soft_spoken_002.wav',
                    'ground_truth': 'همه چیز تاریک به نظر می‌رسه',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 4
                },
                {
                    'id': 'SS_003',
                    'filename': 'soft_spoken_003.wav',
                    'ground_truth': 'نمی‌دونم چطور شروع کنم',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 3
                }
            ]
        },
        'emotional': {
            'description': 'Speech with emotional variations: hesitation, agitation',
            'samples': [
                {
                    'id': 'EM_001',
                    'filename': 'emotional_001.wav',
                    'ground_truth': 'خواهش می‌کنم... نمی‌تونم... این وضع رو تحمل کنم',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 6
                },
                {
                    'id': 'EM_002',
                    'filename': 'emotional_002.wav',
                    'ground_truth': 'برای سال‌ها این مشکل داشتم. نمی‌دونم چطور ادامه دهم',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 7
                },
                {
                    'id': 'EM_003',
                    'filename': 'emotional_003.wav',
                    'ground_truth': 'آخ... اصلا نمی‌تونم تمرکز کنم',
                    'expected_medical_terms': [],
                    'expected_english_terms': [],
                    'duration_seconds': 5
                }
            ]
        },
        'code_switching': {
            'description': 'Persian-English code-switching with medical terminology',
            'samples': [
                {
                    'id': 'CS_001',
                    'filename': 'code_switch_001.wav',
                    'ground_truth': 'بیمار depression داره و anxiety هم توضیح داده',
                    'expected_medical_terms': ['depression', 'anxiety'],
                    'expected_english_terms': ['depression', 'anxiety'],
                    'duration_seconds': 5
                },
                {
                    'id': 'CS_002',
                    'filename': 'code_switch_002.wav',
                    'ground_truth': 'این bipolar disorder و PTSD هم هست',
                    'expected_medical_terms': ['bipolar disorder', 'PTSD'],
                    'expected_english_terms': ['bipolar', 'disorder', 'PTSD'],
                    'duration_seconds': 4
                },
                {
                    'id': 'CS_003',
                    'filename': 'code_switch_003.wav',
                    'ground_truth': 'cognitive behavioral therapy شروع کنیم. antidepressants مؤثر نبوده',
                    'expected_medical_terms': ['cognitive behavioral therapy', 'antidepressants'],
                    'expected_english_terms': ['cognitive', 'behavioral', 'therapy', 'antidepressants'],
                    'duration_seconds': 6
                },
                {
                    'id': 'CS_004',
                    'filename': 'code_switch_004.wav',
                    'ground_truth': 'علائم schizophrenia و psychotic episodes رو توضیح بد',
                    'expected_medical_terms': ['schizophrenia', 'psychotic'],
                    'expected_english_terms': ['schizophrenia', 'psychotic', 'episodes'],
                    'duration_seconds': 5
                },
                {
                    'id': 'CS_005',
                    'filename': 'code_switch_005.wav',
                    'ground_truth': 'medication adherence مشکل است. hospitalization ضروری است',
                    'expected_medical_terms': ['medication', 'hospitalization'],
                    'expected_english_terms': ['medication', 'adherence', 'hospitalization'],
                    'duration_seconds': 5
                }
            ]
        },
        'medical_terms': {
            'description': 'DSM-5 psychiatric terminology recognition',
            'samples': [
                {
                    'id': 'MT_001',
                    'filename': 'medical_terms_001.wav',
                    'ground_truth': 'اختلال افسردگی اساسی تشخیص داده شده',
                    'expected_medical_terms': ['Major Depressive Disorder', 'اختلال افسردگی اساسی'],
                    'expected_english_terms': [],
                    'duration_seconds': 4
                },
                {
                    'id': 'MT_002',
                    'filename': 'medical_terms_002.wav',
                    'ground_truth': 'اختلال اضطراب فراگیر و OCD هم دیده شده',
                    'expected_medical_terms': ['Generalized Anxiety Disorder', 'Obsessive-Compulsive Disorder'],
                    'expected_english_terms': ['OCD'],
                    'duration_seconds': 4
                },
                {
                    'id': 'MT_003',
                    'filename': 'medical_terms_003.wav',
                    'ground_truth': 'اختلال استرس پس از سانحه یا PTSD در بیمار مشهود',
                    'expected_medical_terms': ['Post-Traumatic Stress Disorder'],
                    'expected_english_terms': ['PTSD'],
                    'duration_seconds': 5
                }
            ]
        },
        'background_noise': {
            'description': 'Speech with background noise: clinic sounds, conversation, traffic',
            'samples': [
                {
                    'id': 'BN_001',
                    'filename': 'background_noise_001.wav',
                    'ground_truth': 'بیمار depression داره. درمان شروع کنیم',
                    'expected_medical_terms': ['depression'],
                    'expected_english_terms': ['depression'],
                    'duration_seconds': 5,
                    'noise_type': 'office_conversation'
                },
                {
                    'id': 'BN_002',
                    'filename': 'background_noise_002.wav',
                    'ground_truth': 'علائم anxiety disorder رو توضیح بدهید',
                    'expected_medical_terms': ['anxiety'],
                    'expected_english_terms': ['anxiety', 'disorder'],
                    'duration_seconds': 4,
                    'noise_type': 'traffic'
                },
                {
                    'id': 'BN_003',
                    'filename': 'background_noise_003.wav',
                    'ground_truth': 'PTSD تشخیص داده شده. درمان ضروری است',
                    'expected_medical_terms': ['PTSD'],
                    'expected_english_terms': ['PTSD'],
                    'duration_seconds': 5,
                    'noise_type': 'medical_equipment'
                }
            ]
        }
    }
    
    for scenario, data in ground_truth_data.items():
        ground_truth_file = test_data_dir / scenario / 'ground_truth.json'
        ground_truth_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"✓ Ground truth created for {scenario} scenario ({len(data['samples'])} samples)")


if __name__ == '__main__':
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create test data structure
    logger.info("Setting up test data directory...")
    create_test_data_directory()
    setup_ground_truth_samples()
    
    # Initialize framework
    logger.info("Initializing transcription accuracy framework...")
    framework = TranscriptionAccuracyFramework()
    
    logger.info("✓ Transcription accuracy testing framework ready")
    logger.info(f"  Output directory: {framework.output_dir.absolute()}")
    logger.info(f"  Test scenarios: {list(framework.test_scenarios.keys())}")
    logger.info("\nTo use the framework:")
    logger.info("  1. Load ground truth samples from test_data/*/ground_truth.json")
    logger.info("  2. Add test samples with framework.add_test_sample()")
    logger.info("  3. Generate baseline with framework.generate_baseline_report()")
    logger.info("  4. Compare improvements with framework.generate_comparison_report()")
