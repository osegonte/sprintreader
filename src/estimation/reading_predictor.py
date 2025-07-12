"""
Reading Predictor - Advanced estimation algorithms
"""

from datetime import datetime, timedelta
from typing import Dict, List
import statistics
from database.models import db_manager, ReadingSession, Document

class ReadingPredictor:
    """Advanced reading prediction and pattern analysis"""
    
    def __init__(self):
        self.session = db_manager.get_session()
    
    def predict_session_duration(self, document_id: int, target_pages: int) -> Dict:
        """Predict how long a reading session will take"""
        try:
            # Get historical data for this document
            time_per_page = self._get_document_time_per_page(document_id)
            
            # Calculate prediction
            estimated_seconds = target_pages * time_per_page
            estimated_minutes = estimated_seconds / 60
            
            # Add confidence intervals
            confidence_range = self._calculate_confidence_range(document_id, estimated_minutes)
            
            return {
                'target_pages': target_pages,
                'estimated_minutes': round(estimated_minutes, 1),
                'estimated_range_min': round(confidence_range[0], 1),
                'estimated_range_max': round(confidence_range[1], 1),
                'recommended_timer_mode': self._recommend_timer_mode(estimated_minutes),
                'break_recommendations': self._get_break_recommendations(estimated_minutes)
            }
            
        except Exception as e:
            print(f"❌ Error predicting session duration: {e}")
            return {}
    
    def analyze_reading_patterns(self) -> Dict:
        """Analyze user's reading patterns and habits"""
        try:
            sessions = self.session.query(ReadingSession).order_by(
                ReadingSession.start_time.desc()
            ).limit(100).all()
            
            if not sessions:
                return {}
            
            # Analyze patterns
            session_lengths = [s.duration for s in sessions if s.duration]
            pages_per_session = [s.pages_read for s in sessions if s.pages_read]
            
            # Time of day analysis
            hour_counts = {}
            for session in sessions:
                hour = session.start_time.hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            most_productive_hour = max(hour_counts, key=hour_counts.get) if hour_counts else None
            
            # Reading efficiency over time
            recent_speed = self._calculate_recent_reading_speed()
            historical_speed = self._calculate_historical_reading_speed()
            speed_trend = "improving" if recent_speed > historical_speed else "declining"
            
            return {
                'total_sessions_analyzed': len(sessions),
                'average_session_length': round(statistics.mean(session_lengths), 1) if session_lengths else 0,
                'average_pages_per_session': round(statistics.mean(pages_per_session), 1) if pages_per_session else 0,
                'most_productive_hour': most_productive_hour,
                'reading_speed_trend': speed_trend,
                'recent_avg_speed': round(recent_speed, 2),
                'historical_avg_speed': round(historical_speed, 2),
                'consistency_score': self._calculate_consistency_score(session_lengths),
                'recommendations': self._generate_pattern_recommendations(sessions)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing reading patterns: {e}")
            return {}
    
    def _get_document_time_per_page(self, document_id: int) -> float:
        """Get time per page for specific document"""
        sessions = self.session.query(ReadingSession).filter_by(
            document_id=document_id
        ).all()
        
        total_time = 0
        total_pages = 0
        
        for session in sessions:
            if session.duration and session.pages_read:
                total_time += session.duration * 60  # Convert to seconds
                total_pages += session.pages_read
        
        return total_time / total_pages if total_pages > 0 else 120  # Default 2 minutes
    
    def _calculate_confidence_range(self, document_id: int, estimated_minutes: float) -> tuple:
        """Calculate confidence range for estimate"""
        # Simple confidence range: ±20% based on variance
        variance_factor = 0.2
        min_estimate = estimated_minutes * (1 - variance_factor)
        max_estimate = estimated_minutes * (1 + variance_factor)
        return (min_estimate, max_estimate)
    
    def _recommend_timer_mode(self, estimated_minutes: float) -> str:
        """Recommend best timer mode for estimated duration"""
        if estimated_minutes <= 7:
            return "Sprint (5 min)"
        elif estimated_minutes <= 30:
            return "Pomodoro (25 min)"
        elif estimated_minutes <= 60:
            return "Custom (60 min)"
        else:
            return "Multiple Pomodoro sessions"
    
    def _get_break_recommendations(self, estimated_minutes: float) -> List[str]:
        """Get break recommendations for session length"""
        recommendations = []
        
        if estimated_minutes > 25:
            recommendations.append("Take 5-minute breaks every 25 minutes")
        if estimated_minutes > 60:
            recommendations.append("Consider a longer 15-minute break halfway through")
        if estimated_minutes > 120:
            recommendations.append("Split into multiple sessions across different times")
        
        return recommendations or ["No breaks needed for short session"]
    
    def _calculate_recent_reading_speed(self) -> float:
        """Calculate reading speed from recent sessions"""
        recent_date = datetime.now() - timedelta(days=7)
        sessions = self.session.query(ReadingSession).filter(
            ReadingSession.start_time >= recent_date
        ).all()
        
        total_time = sum(s.duration for s in sessions if s.duration)
        total_pages = sum(s.pages_read for s in sessions if s.pages_read)
        
        return total_pages / total_time if total_time > 0 else 0
    
    def _calculate_historical_reading_speed(self) -> float:
        """Calculate reading speed from historical sessions"""
        old_date = datetime.now() - timedelta(days=30)
        recent_date = datetime.now() - timedelta(days=7)
        
        sessions = self.session.query(ReadingSession).filter(
            ReadingSession.start_time.between(old_date, recent_date)
        ).all()
        
        total_time = sum(s.duration for s in sessions if s.duration)
        total_pages = sum(s.pages_read for s in sessions if s.pages_read)
        
        return total_pages / total_time if total_time > 0 else 0
    
    def _calculate_consistency_score(self, session_lengths: List[float]) -> float:
        """Calculate reading consistency score (0-100)"""
        if len(session_lengths) < 2:
            return 0
        
        mean_length = statistics.mean(session_lengths)
        std_dev = statistics.stdev(session_lengths)
        
        # Lower standard deviation = higher consistency
        consistency = max(0, 100 - (std_dev / mean_length * 100))
        return round(consistency, 1)
    
    def _generate_pattern_recommendations(self, sessions: List) -> List[str]:
        """Generate recommendations based on reading patterns"""
        recommendations = []
        
        if len(sessions) < 10:
            recommendations.append("Build more reading data for better predictions")
        
        # Analyze session frequency
        session_dates = [s.start_time.date() for s in sessions]
        unique_dates = len(set(session_dates))
        
        if unique_dates < len(sessions) * 0.7:
            recommendations.append("Try spreading reading across more days for better retention")
        
        return recommendations
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
