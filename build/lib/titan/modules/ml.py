"""
Machine Learning-Based Bypass Pattern Optimization
==================================================

This module implements ML-based optimization for bypass patterns,
learning from success/failure patterns to improve bypass rates.
"""

import time
import statistics
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass
import logging

@dataclass
class BypassAttempt:
    """Represents a bypass attempt with all relevant data"""
    timestamp: float
    domain: str
    challenge_type: str
    bypass_strategy: str
    success: bool
    response_time: float
    status_code: int
    
    # Fingerprinting data
    tls_fingerprint: str
    canvas_fingerprint: str
    webgl_fingerprint: str
    
    # Timing data
    delay_used: float
    behavior_profile: str
    
    # Detection data
    detection_confidence: float
    anti_detection_enabled: bool
    
    # Context data
    time_of_day: int  # Hour 0-23
    day_of_week: int  # 0=Monday, 6=Sunday
    session_age: float
    
    def to_feature_vector(self) -> List[float]:
        """Convert to ML feature vector"""
        return [
            self.response_time,
            self.delay_used,
            self.session_age,
            float(self.time_of_day) / 24.0,
            float(self.day_of_week) / 7.0,
            hash(self.bypass_strategy) % 1000 / 1000.0,
            hash(self.behavior_profile) % 1000 / 1000.0,
            float(self.anti_detection_enabled),
            self.detection_confidence,
            float(self.status_code) / 1000.0,
            hash(self.tls_fingerprint) % 1000 / 1000.0,
            hash(self.canvas_fingerprint) % 1000 / 1000.0,
            hash(self.webgl_fingerprint) % 1000 / 1000.0,
        ]


class SimpleMLOptimizer:
    """Simple ML-based optimizer using basic statistical learning"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.attempt_history = deque(maxlen=max_history)
        self.domain_models = defaultdict(lambda: {
            'success_patterns': defaultdict(list),
            'failure_patterns': defaultdict(list),
            'optimal_strategies': {},
            'last_updated': 0
        })
        self.feature_weights = [1.0] * 13
        self.learning_rate = 0.01
        
    def record_attempt(self, attempt: BypassAttempt):
        self.attempt_history.append(attempt)
        domain_model = self.domain_models[attempt.domain]
        if attempt.success:
            domain_model['success_patterns'][attempt.bypass_strategy].append(attempt)
        else:
            domain_model['failure_patterns'][attempt.bypass_strategy].append(attempt)
        domain_model['last_updated'] = time.time()
        self._update_feature_weights(attempt)
        self._cleanup_old_data(attempt.domain)
    
    def _update_feature_weights(self, attempt: BypassAttempt):
        features = attempt.to_feature_vector()
        adjustment = self.learning_rate if attempt.success else -self.learning_rate
        for i, feature_value in enumerate(features):
            if feature_value > 0:
                self.feature_weights[i] += adjustment * feature_value
                self.feature_weights[i] = max(0.1, min(2.0, self.feature_weights[i]))
    
    def _cleanup_old_data(self, domain: str):
        domain_model = self.domain_models[domain]
        cutoff_time = time.time() - 86400  # 24 hours
        for strategy, attempts in domain_model['success_patterns'].items():
            domain_model['success_patterns'][strategy] = [a for a in attempts if a.timestamp > cutoff_time]
        for strategy, attempts in domain_model['failure_patterns'].items():
            domain_model['failure_patterns'][strategy] = [a for a in attempts if a.timestamp > cutoff_time]
    
    def predict_best_strategy(self, domain: str, context: Dict[str, Any]) -> Dict[str, Any]:
        domain_model = self.domain_models[domain]
        if not domain_model['success_patterns']:
            return {'strategy': 'default', 'confidence': 0.0, 'reasoning': 'No historical data'}
        
        strategy_scores = {}
        for strategy, successes in domain_model['success_patterns'].items():
            failures = domain_model['failure_patterns'].get(strategy, [])
            total = len(successes) + len(failures)
            if total == 0: continue
            
            success_rate = len(successes) / total
            recent = sum(1 for a in successes if a.timestamp > time.time() - 3600)
            recency_bonus = recent * 0.1
            similarity = self._calculate_context_similarity(successes, context)
            strategy_scores[strategy] = (success_rate + recency_bonus) * similarity
        
        if not strategy_scores:
            return {'strategy': 'default', 'confidence': 0.0, 'reasoning': 'No viable strategies'}
        
        best = max(strategy_scores.items(), key=lambda x: x[1])
        return {
            'strategy': best[0],
            'confidence': min(1.0, best[1]),
            'reasoning': 'Best success rate with context similarity',
            'alternatives': sorted(strategy_scores.items(), key=lambda x: x[1], reverse=True)[1:3]
        }
    
    def _calculate_context_similarity(self, attempts: List[BypassAttempt], context: Dict[str, Any]) -> float:
        if not attempts: return 0.5
        current_hour = context.get('time_of_day', 12)
        current_day = context.get('day_of_week', 1)
        similarities = []
        for attempt in attempts[-10:]:
            s = 0.0
            h_diff = abs(attempt.time_of_day - current_hour)
            s += (1.0 - (min(h_diff, 24 - h_diff) / 12.0)) * 0.3
            d_diff = abs(attempt.day_of_week - current_day)
            s += (1.0 - (min(d_diff, 7 - d_diff) / 3.5)) * 0.2
            s += (1.0 if attempt.behavior_profile == context.get('behavior_profile') else 0.5) * 0.3
            age_h = (time.time() - attempt.timestamp) / 3600
            s += max(0.0, 1.0 - (age_h / 24.0)) * 0.2
            similarities.append(s)
        return statistics.mean(similarities) if similarities else 0.5


class AdaptiveStrategySelector:
    def __init__(self, optimizer: SimpleMLOptimizer):
        self.optimizer = optimizer
        self.strategy_registry = {
            'conservative': {'behavior_profile': 'research', 'spoofing_level': 'low', 'timing_multiplier': 2.0, 'anti_detection': True},
            'balanced': {'behavior_profile': 'casual', 'spoofing_level': 'medium', 'timing_multiplier': 1.0, 'anti_detection': True},
            'aggressive': {'behavior_profile': 'focused', 'spoofing_level': 'high', 'timing_multiplier': 0.5, 'anti_detection': True},
            'stealth': {'behavior_profile': 'research', 'spoofing_level': 'high', 'timing_multiplier': 3.0, 'anti_detection': True}
        }
    
    def select_strategy(self, domain: str, context: Dict[str, Any]) -> Dict[str, Any]:
        prediction = self.optimizer.predict_best_strategy(domain, context)
        strategy = prediction['strategy']
        config = self.strategy_registry.get(strategy, self.strategy_registry['balanced']).copy()
        
        # Adjustments
        hour = context.get('time_of_day', 12)
        if 1 <= hour <= 6:
            config['timing_multiplier'] *= 1.5
            config['spoofing_level'] = 'high'
        
        return {
            'name': strategy,
            'config': config,
            'confidence': prediction['confidence'],
            'reasoning': prediction['reasoning']
        }


class MLBypassOrchestrator:
    def __init__(self, scraper_instance):
        self.scraper = scraper_instance
        self.optimizer = SimpleMLOptimizer()
        self.selector = AdaptiveStrategySelector(self.optimizer)
        self.enabled = True
        self.current_strategy = None
        
    def optimize_request(self, domain: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.enabled: return {'optimized': False}
        
        from datetime import datetime
        dt = datetime.fromtimestamp(time.time())
        ctx = {
            'time_of_day': dt.hour,
            'day_of_week': dt.weekday(),
            **(context or {})
        }
        
        strategy = self.selector.select_strategy(domain, ctx)
        self.current_strategy = strategy
        self._apply_strategy(strategy)
        return {'optimized': True, 'strategy': strategy}
    
    def record_outcome(self, domain: str, success: bool, response_time: float, status_code: int):
        if not self.enabled: return
        
        from datetime import datetime
        now = time.time()
        dt = datetime.fromtimestamp(now)
        
        # Safe access to scraper components
        tls_fp = getattr(self.scraper.tls, 'current_fingerprint', 'unknown') if hasattr(self.scraper, 'tls') else 'unknown'
        # Simplified for now
        
        attempt = BypassAttempt(
            timestamp=now,
            domain=domain,
            challenge_type='unknown',
            bypass_strategy=self.current_strategy['name'] if self.current_strategy else 'unknown',
            success=success,
            response_time=response_time,
            status_code=status_code,
            tls_fingerprint=str(tls_fp),
            canvas_fingerprint='unknown',
            webgl_fingerprint='unknown',
            delay_used=response_time,
            behavior_profile=self.current_strategy['config'].get('behavior_profile', 'unknown') if self.current_strategy else 'unknown',
            detection_confidence=1.0,
            anti_detection_enabled=True,
            time_of_day=dt.hour,
            day_of_week=dt.weekday(),
            session_age=0 # Todo
        )
        self.optimizer.record_attempt(attempt)
        
    def _apply_strategy(self, strategy: Dict[str, Any]):
        config = strategy['config']
        if hasattr(self.scraper, 'stealth'):
             # Apply changes if stealth module exists
             pass
        logging.info(f"Applied strategy: {strategy['name']}")
