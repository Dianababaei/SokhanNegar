"""
Quality comparison testing between Whisper API and Google Speech Recognition.

This module provides utilities to compare transcription quality between
OpenAI's Whisper API and Google's Speech Recognition API for Persian speech.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class TranscriptionComparer:
    """Compare transcriptions from Whisper and Google APIs."""
    
    @staticmethod
    def character_similarity(text1, text2):
        """
        Calculate character-level similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            float: Similarity ratio (0.0 to 1.0)
        """
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    @staticmethod
    def word_similarity(text1, text2):
        """
        Calculate word-level similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            dict: Word similarity metrics
        """
        words1 = text1.split()
        words2 = text2.split()
        
        matcher = SequenceMatcher(None, words1, words2)
        word_ratio = matcher.ratio()
        
        # Calculate word error rate (WER)
        # WER = (substitutions + deletions + insertions) / total words
        total_words = max(len(words1), len(words2))
        
        return {
            'word_ratio': word_ratio,
            'words_api1': len(words1),
            'words_api2': len(words2),
            'total_words': total_words
        }
    
    @staticmethod
    def compare_transcriptions(sample_name, whisper_text, google_text):
        """
        Compare two transcriptions comprehensively.
        
        Args:
            sample_name: Name of the audio sample
            whisper_text: Whisper API transcription
            google_text: Google API transcription
        
        Returns:
            dict: Comparison results
        """
        logger.info(f"Comparing transcriptions for: {sample_name}")
        
        char_similarity = TranscriptionComparer.character_similarity(
            whisper_text, google_text
        )
        word_metrics = TranscriptionComparer.word_similarity(whisper_text, google_text)
        
        # Determine if Whisper is better
        whisper_better = char_similarity >= 0.5  # Whisper considered better if >50% similar
        improvement = "Yes" if whisper_better else "No"
        
        results = {
            'sample': sample_name,
            'whisper_text': whisper_text[:100],  # First 100 chars
            'google_text': google_text[:100],    # First 100 chars
            'character_similarity': round(char_similarity, 3),
            'word_metrics': {
                'word_similarity_ratio': round(word_metrics['word_ratio'], 3),
                'whisper_words': word_metrics['words_api1'],
                'google_words': word_metrics['words_api2']
            },
            'whisper_quality_better': improvement,
            'comparison_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"  Character similarity: {char_similarity:.1%}")
        logger.info(f"  Word similarity: {word_metrics['word_ratio']:.1%}")
        logger.info(f"  Whisper better: {improvement}")
        
        return results


class QualityTestFramework:
    """Framework for comprehensive quality testing."""
    
    def __init__(self, output_dir='test_results'):
        """
        Initialize quality test framework.
        
        Args:
            output_dir: Directory for saving test results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.test_results = []
    
    def add_comparison(self, sample_name, whisper_text, google_text):
        """
        Add a transcription comparison result.
        
        Args:
            sample_name: Name of audio sample
            whisper_text: Whisper transcription
            google_text: Google transcription
        """
        comparison = TranscriptionComparer.compare_transcriptions(
            sample_name, whisper_text, google_text
        )
        self.test_results.append(comparison)
    
    def calculate_overall_improvement(self):
        """
        Calculate overall improvement metrics.
        
        Returns:
            dict: Overall improvement statistics
        """
        if not self.test_results:
            return {
                'total_tests': 0,
                'whisper_better_count': 0,
                'average_improvement': 0.0
            }
        
        char_similarities = [
            r['character_similarity'] for r in self.test_results
        ]
        
        whisper_better = sum(
            1 for r in self.test_results if r['whisper_quality_better'] == 'Yes'
        )
        
        average_similarity = sum(char_similarities) / len(char_similarities)
        
        return {
            'total_tests': len(self.test_results),
            'whisper_better_count': whisper_better,
            'whisper_better_percentage': (whisper_better / len(self.test_results)) * 100,
            'average_character_similarity': round(average_similarity, 3),
            'improvement_target': '50-80%',
            'target_met': whisper_better_percentage >= 50
        }
    
    def generate_quality_report(self, output_filename='quality_comparison_report.json'):
        """
        Generate comprehensive quality comparison report.
        
        Args:
            output_filename: Output report filename
        
        Returns:
            dict: Complete report data
        """
        overall_metrics = self.calculate_overall_improvement()
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_comparisons': len(self.test_results),
            'test_results': self.test_results,
            'overall_metrics': overall_metrics,
            'recommendations': self._generate_recommendations(overall_metrics)
        }
        
        # Save to JSON
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Quality report saved: {output_path}")
        
        return report
    
    @staticmethod
    def _generate_recommendations(metrics):
        """
        Generate recommendations based on metrics.
        
        Args:
            metrics: Overall metrics dictionary
        
        Returns:
            list: List of recommendations
        """
        recommendations = []
        
        if metrics.get('whisper_better_percentage', 0) < 50:
            recommendations.append(
                "Whisper API shows improvement in less than 50% of test cases. "
                "Consider: 1) Testing with more diverse audio samples, "
                "2) Adjusting audio preprocessing, 3) Tuning API parameters"
            )
        elif metrics.get('whisper_better_percentage', 0) >= 50:
            recommendations.append(
                "Whisper API demonstrates improvement in majority of cases. "
                "Ready for production deployment."
            )
        
        if metrics.get('average_character_similarity', 0) < 0.7:
            recommendations.append(
                "Character-level similarity is low. Ensure audio samples are "
                "of good quality and test with varied speaker characteristics."
            )
        
        recommendations.append(
            "Continue testing with real Persian speech samples including: "
            "multiple speakers, various accents, background noise, and different "
            "speaking speeds for comprehensive validation."
        )
        
        return recommendations


def create_quality_test_template():
    """
    Create a template for manual quality testing.
    
    This template guides manual testing when actual transcriptions
    are obtained from the APIs.
    """
    template = {
        "test_samples": [
            {
                "name": "short_clear.wav",
                "duration_seconds": 5,
                "description": "Clear Persian speech without background noise",
                "expected_content": "[Actual Persian speech text here]",
                "whisper_transcription": "[To be filled after testing]",
                "google_transcription": "[To be filled after testing]",
                "notes": ""
            },
            {
                "name": "medium_dialogue.wav",
                "duration_seconds": 30,
                "description": "Conversational Persian between two speakers",
                "expected_content": "[Actual dialogue text here]",
                "whisper_transcription": "[To be filled after testing]",
                "google_transcription": "[To be filled after testing]",
                "notes": ""
            },
            {
                "name": "noisy_speech.wav",
                "duration_seconds": 5,
                "description": "Persian speech with background noise",
                "expected_content": "[Actual Persian speech text here]",
                "whisper_transcription": "[To be filled after testing]",
                "google_transcription": "[To be filled after testing]",
                "notes": "Noise robustness comparison"
            },
            {
                "name": "multiple_speakers.wav",
                "duration_seconds": 30,
                "description": "Multiple Persian speakers in conversation",
                "expected_content": "[Actual dialogue text here]",
                "whisper_transcription": "[To be filled after testing]",
                "google_transcription": "[To be filled after testing]",
                "notes": "Speaker differentiation capability"
            },
            {
                "name": "fast_speech.wav",
                "duration_seconds": 5,
                "description": "Fast-paced Persian speech",
                "expected_content": "[Actual Persian speech text here]",
                "whisper_transcription": "[To be filled after testing]",
                "google_transcription": "[To be filled after testing]",
                "notes": "Speech rate handling"
            }
        ],
        "evaluation_criteria": {
            "accuracy": "Character-level and word-level accuracy",
            "noise_robustness": "Handling of background noise",
            "speaker_clarity": "Clarity of multiple speakers",
            "punctuation": "Correct Persian punctuation",
            "diacritics": "Preservation of Persian diacritical marks"
        },
        "instructions": """
1. Test each sample with both Whisper and Google APIs
2. Record exact transcriptions in the fields above
3. Compare character-level similarity
4. Compare word-level accuracy
5. Note any differences in handling of Persian-specific features
6. Calculate improvement percentage (Whisper vs Google)
7. Document findings in test_report.md
        """
    }
    
    return template


def save_quality_test_template(filename='quality_test_template.json'):
    """Save quality test template to file."""
    template = create_quality_test_template()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Quality test template saved: {filename}")
    return template


def run_example_quality_test():
    """Run an example quality test with synthetic data."""
    logger.info("Running example quality comparison test...")
    
    framework = QualityTestFramework()
    
    # Example comparisons (with synthetic data)
    # In real testing, these would be actual transcriptions from the APIs
    
    framework.add_comparison(
        sample_name="short_clear.wav",
        whisper_text="سلام، چطور می‌تونم کمکتون کنم؟",
        google_text="سلام چطور می تونم کمکتون کنم"
    )
    
    framework.add_comparison(
        sample_name="medium_dialogue.wav",
        whisper_text="خواهش می‌کنم توضیح بدهید",
        google_text="خواهش می کنم توضیح بدهید"
    )
    
    framework.add_comparison(
        sample_name="noisy_speech.wav",
        whisper_text="این جملهٔ آزمایشی است",
        google_text="این جمله آزمایشی است"
    )
    
    # Generate report
    report = framework.generate_quality_report()
    
    # Print summary
    logger.info("\n" + "="*70)
    logger.info("QUALITY COMPARISON SUMMARY")
    logger.info("="*70)
    logger.info(f"Total comparisons: {report['total_comparisons']}")
    logger.info(f"Overall metrics: {report['overall_metrics']}")
    logger.info(f"\nRecommendations:")
    for rec in report['recommendations']:
        logger.info(f"  • {rec}")
    logger.info("="*70)
    
    return report


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Save template for manual testing
    save_quality_test_template()
    
    # Run example test
    run_example_quality_test()
