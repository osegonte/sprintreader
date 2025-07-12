"""
Analytics Manager - Reading insights and statistics
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from database.models import db_manager, ReadingSession, Document
from sqlalchemy import func, and_

class AnalyticsManager:
    """Manages reading analytics and insights"""
    
    def __init__(self):
        self.session = db_manager.get_session()
    
    def get_daily_stats(self, target_date: date = None) -> Dict:
        """Get reading statistics for a specific day"""
        if target_date is None:
            target_date = date.today()
        
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        try:
            # Query sessions for the day
            sessions = self.session.query(ReadingSession).filter(
                and_(
                    ReadingSession.start_time >= start_datetime,
                    ReadingSession.start_time <= end_datetime
                )
            ).all()
            
            total_time = sum(s.duration or 0 for s in sessions)
            total_pages = sum(s.pages_read or 0 for s in sessions)
            session_count = len(sessions)
            
            # Calculate reading speed
            avg_speed = (total_pages / total_time) if total_time > 0 else 0
            
            # Count different session types
            session_types = {}
            for session in sessions:
                session_type = session.session_type or 'regular'
                session_types[session_type] = session_types.get(session_type, 0) + 1
            
            return {
                'date': target_date.isoformat(),
                'total_reading_time': round(total_time, 1),
                'total_pages_read': total_pages,
                'session_count': session_count,
                'average_reading_speed': round(avg_speed, 2),
                'session_types': session_types,
                'longest_session': max([s.duration or 0 for s in sessions]) if sessions else 0
            }
            
        except Exception as e:
            print(f"❌ Error getting daily stats: {e}")
            return {}
    
    def get_weekly_stats(self, week_start: date = None) -> Dict:
        """Get reading statistics for a week"""
        if week_start is None:
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        # Get daily stats for each day of the week
        daily_stats = []
        total_time = 0
        total_pages = 0
        total_sessions = 0
        
        for i in range(7):
            day = week_start + timedelta(days=i)
            day_stats = self.get_daily_stats(day)
            daily_stats.append(day_stats)
            
            total_time += day_stats.get('total_reading_time', 0)
            total_pages += day_stats.get('total_pages_read', 0)
            total_sessions += day_stats.get('session_count', 0)
        
        # Calculate weekly averages
        avg_daily_time = total_time / 7
        avg_daily_pages = total_pages / 7
        
        # Find most productive day
        most_productive_day = max(daily_stats, 
                                key=lambda x: x.get('total_reading_time', 0))
        
        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'daily_stats': daily_stats,
            'total_reading_time': round(total_time, 1),
            'total_pages_read': total_pages,
            'total_sessions': total_sessions,
            'average_daily_time': round(avg_daily_time, 1),
            'average_daily_pages': round(avg_daily_pages, 1),
            'most_productive_day': most_productive_day.get('date'),
            'streak_days': self._calculate_reading_streak(week_start, week_end)
        }
    
    def get_document_analytics(self, document_id: int) -> Dict:
        """Get analytics for a specific document"""
        try:
            # Get document info
            document = self.session.query(Document).filter_by(id=document_id).first()
            if not document:
                return {}
            
            # Get all sessions for this document
            sessions = self.session.query(ReadingSession).filter_by(
                document_id=document_id
            ).all()
            
            total_time = sum(s.duration or 0 for s in sessions)
            total_pages = sum(s.pages_read or 0 for s in sessions)
            
            # Calculate progress
            progress_percent = 0
            if document.total_pages and document.current_page:
                progress_percent = (document.current_page / document.total_pages) * 100
            
            # Estimate completion time
            estimated_completion = None
            if document.reading_speed and document.total_pages and document.current_page:
                remaining_pages = document.total_pages - document.current_page
                estimated_minutes = remaining_pages / document.reading_speed
                estimated_completion = round(estimated_minutes, 1)
            
            # Session pattern analysis
            session_count = len(sessions)
            avg_session_length = total_time / session_count if session_count > 0 else 0
            
            return {
                'document_id': document_id,
                'title': document.title or document.filename,
                'total_pages': document.total_pages,
                'current_page': document.current_page,
                'progress_percent': round(progress_percent, 1),
                'total_reading_time': round(total_time, 1),
                'total_pages_read': total_pages,
                'session_count': session_count,
                'average_session_length': round(avg_session_length, 1),
                'reading_speed': document.reading_speed,
                'estimated_completion_time': estimated_completion,
                'first_session': sessions[0].start_time.isoformat() if sessions else None,
                'last_session': sessions[-1].start_time.isoformat() if sessions else None
            }
            
        except Exception as e:
            print(f"❌ Error getting document analytics: {e}")
            return {}
    
    def get_reading_trends(self, days: int = 30) -> Dict:
        """Get reading trends over specified number of days"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        trends = []
        total_time = 0
        total_pages = 0
        
        # Get daily data for trend analysis
        for i in range(days):
            day = start_date + timedelta(days=i)
            day_stats = self.get_daily_stats(day)
            
            trends.append({
                'date': day.isoformat(),
                'reading_time': day_stats.get('total_reading_time', 0),
                'pages_read': day_stats.get('total_pages_read', 0),
                'sessions': day_stats.get('session_count', 0)
            })
            
            total_time += day_stats.get('total_reading_time', 0)
            total_pages += day_stats.get('total_pages_read', 0)
        
        # Calculate trend indicators
        recent_avg = sum(t['reading_time'] for t in trends[-7:]) / 7  # Last 7 days
        previous_avg = sum(t['reading_time'] for t in trends[-14:-7]) / 7  # Previous 7 days
        
        trend_direction = "improving" if recent_avg > previous_avg else "declining"
        if abs(recent_avg - previous_avg) < 0.1:
            trend_direction = "stable"
        
        # Find best and worst days
        best_day = max(trends, key=lambda x: x['reading_time'])
        worst_day = min(trends, key=lambda x: x['reading_time'])
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'daily_trends': trends,
            'total_reading_time': round(total_time, 1),
            'total_pages_read': total_pages,
            'average_daily_time': round(total_time / days, 1),
            'trend_direction': trend_direction,
            'recent_7day_avg': round(recent_avg, 1),
            'previous_7day_avg': round(previous_avg, 1),
            'best_day': best_day,
            'worst_day': worst_day,
            'consistency_score': self._calculate_consistency_score(trends)
        }
    
    def get_timer_mode_effectiveness(self) -> Dict:
        """Analyze effectiveness of different timer modes"""
        try:
            # Get sessions by timer mode
            pomodoro_sessions = self.session.query(ReadingSession).filter_by(
                session_type='pomodoro'
            ).all()
            
            sprint_sessions = self.session.query(ReadingSession).filter_by(
                session_type='sprint'
            ).all()
            
            regular_sessions = self.session.query(ReadingSession).filter_by(
                session_type='regular'
            ).all()
            
            def analyze_sessions(sessions, mode_name):
                if not sessions:
                    return {'mode': mode_name, 'sessions': 0}
                
                total_time = sum(s.duration or 0 for s in sessions)
                total_pages = sum(s.pages_read or 0 for s in sessions)
                avg_speed = (total_pages / total_time) if total_time > 0 else 0
                avg_duration = total_time / len(sessions)
                
                return {
                    'mode': mode_name,
                    'sessions': len(sessions),
                    'total_time': round(total_time, 1),
                    'total_pages': total_pages,
                    'average_speed': round(avg_speed, 2),
                    'average_duration': round(avg_duration, 1),
                    'pages_per_session': round(total_pages / len(sessions), 1)
                }
            
            pomodoro_stats = analyze_sessions(pomodoro_sessions, 'Pomodoro')
            sprint_stats = analyze_sessions(sprint_sessions, 'Sprint')
            regular_stats = analyze_sessions(regular_sessions, 'Regular')
            
            # Determine most effective mode
            modes = [pomodoro_stats, sprint_stats, regular_stats]
            most_effective = max(modes, key=lambda x: x.get('average_speed', 0))
            
            return {
                'pomodoro': pomodoro_stats,
                'sprint': sprint_stats,
                'regular': regular_stats,
                'most_effective_mode': most_effective['mode'],
                'recommendation': self._get_mode_recommendation(modes)
            }
            
        except Exception as e:
            print(f"❌ Error analyzing timer modes: {e}")
            return {}
    
    def _calculate_reading_streak(self, start_date: date, end_date: date) -> int:
        """Calculate current reading streak in days"""
        current_date = end_date
        streak = 0
        
        while current_date >= start_date:
            day_stats = self.get_daily_stats(current_date)
            if day_stats.get('session_count', 0) > 0:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _calculate_consistency_score(self, trends: List[Dict]) -> float:
        """Calculate reading consistency score (0-100)"""
        if len(trends) < 2:
            return 0.0
        
        # Calculate standard deviation of reading times
        times = [t['reading_time'] for t in trends]
        mean_time = sum(times) / len(times)
        
        if mean_time == 0:
            return 0.0
        
        variance = sum((t - mean_time) ** 2 for t in times) / len(times)
        std_dev = variance ** 0.5
        
        # Consistency score: lower std deviation = higher consistency
        # Normalize to 0-100 scale
        consistency = max(0, 100 - (std_dev / mean_time * 100))
        return round(consistency, 1)
    
    def _get_mode_recommendation(self, modes: List[Dict]) -> str:
        """Generate recommendation based on timer mode analysis"""
        pomodoro = next(m for m in modes if m['mode'] == 'Pomodoro')
        sprint = next(m for m in modes if m['mode'] == 'Sprint')
        regular = next(m for m in modes if m['mode'] == 'Regular')
        
        if pomodoro['average_speed'] > sprint['average_speed'] and pomodoro['average_speed'] > regular['average_speed']:
            return "Try more Pomodoro sessions for better focus and speed"
        elif sprint['average_speed'] > regular['average_speed']:
            return "Sprint sessions work well for you - consider more quick reading bursts"
        else:
            return "Regular reading sessions suit your style - maintain your current approach"
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
