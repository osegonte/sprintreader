"""
Smart Time Estimation System
Calculates completion times based on actual reading behavior
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from database.models import db_manager, Document, ReadingSession
from sqlalchemy import func, and_

class TimeEstimator:
    """Estimates reading completion times based on user behavior"""
    
    def __init__(self):
        self.session = db_manager.get_session()
        self.minimum_sample_pages = 3  # Need at least 3 pages for reliable estimate
        self.default_time_per_page = 120  # 2 minutes default if no data
    
    def estimate_document_completion(self, document_id: int) -> Dict:
        """Estimate time to complete a specific document"""
        try:
            document = self.session.query(Document).filter_by(id=document_id).first()
            if not document:
                return {}
            
            # Get user's reading speed for this document
            avg_time_per_page = self._get_document_reading_speed(document_id)
            
            # Calculate remaining pages
            current_page = document.current_page or 1
            total_pages = document.total_pages or 0
            remaining_pages = max(0, total_pages - current_page)
            
            # Calculate estimates
            estimated_seconds = remaining_pages * avg_time_per_page
            estimated_minutes = estimated_seconds / 60
            
            # Calculate progress percentage
            progress_percent = (current_page / total_pages * 100) if total_pages > 0 else 0
            
            # Get completion date estimate based on daily reading habits
            daily_avg_minutes = self._get_daily_reading_average()
            days_to_complete = estimated_minutes / daily_avg_minutes if daily_avg_minutes > 0 else None
            
            estimated_completion_date = None
            if days_to_complete:
                estimated_completion_date = datetime.now() + timedelta(days=days_to_complete)
            
            return {
                'document_id': document_id,
                'document_title': document.title or document.filename,
                'total_pages': total_pages,
                'current_page': current_page,
                'remaining_pages': remaining_pages,
                'progress_percent': round(progress_percent, 1),
                'avg_time_per_page_seconds': round(avg_time_per_page, 1),
                'estimated_time_remaining_minutes': round(estimated_minutes, 1),
                'estimated_time_remaining_formatted': self._format_time_estimate(estimated_minutes),
                'estimated_completion_date': estimated_completion_date.isoformat() if estimated_completion_date else None,
                'confidence_level': self._calculate_confidence_level(document_id),
                'recommendation': self._get_reading_recommendation(estimated_minutes, days_to_complete)
            }
            
        except Exception as e:
            print(f"❌ Error estimating document completion: {e}")
            return {}
    
    def estimate_all_documents_completion(self) -> Dict:
        """Estimate total time to complete all documents"""
        try:
            documents = self.session.query(Document).all()
            
            total_estimated_minutes = 0
            document_estimates = []
            completed_documents = 0
            
            for doc in documents:
                estimate = self.estimate_document_completion(doc.id)
                if estimate:
                    document_estimates.append(estimate)
                    remaining_minutes = estimate.get('estimated_time_remaining_minutes', 0)
                    total_estimated_minutes += remaining_minutes
                    
                    if estimate.get('remaining_pages', 0) == 0:
                        completed_documents += 1
            
            # Calculate daily recommendation
            daily_avg_minutes = self._get_daily_reading_average()
            days_to_complete_all = total_estimated_minutes / daily_avg_minutes if daily_avg_minutes > 0 else None
            
            total_documents = len(documents)
            completion_percentage = (completed_documents / total_documents * 100) if total_documents > 0 else 0
            
            return {
                'total_documents': total_documents,
                'completed_documents': completed_documents,
                'remaining_documents': total_documents - completed_documents,
                'completion_percentage': round(completion_percentage, 1),
                'total_estimated_time_minutes': round(total_estimated_minutes, 1),
                'total_estimated_time_formatted': self._format_time_estimate(total_estimated_minutes),
                'daily_average_reading_minutes': round(daily_avg_minutes, 1),
                'estimated_days_to_complete': round(days_to_complete_all, 1) if days_to_complete_all else None,
                'document_estimates': document_estimates,
                'overall_recommendation': self._get_overall_recommendation(total_estimated_minutes, days_to_complete_all)
            }
            
        except Exception as e:
            print(f"❌ Error estimating total completion: {e}")
            return {}
    
    def estimate_goal_feasibility(self, target_date: datetime, document_ids: List[int] = None) -> Dict:
        """Check if completing documents by target date is feasible"""
        try:
            # Get documents to analyze
            if document_ids:
                documents = self.session.query(Document).filter(Document.id.in_(document_ids)).all()
            else:
                documents = self.session.query(Document).all()
            
            total_estimated_minutes = 0
            for doc in documents:
                estimate = self.estimate_document_completion(doc.id)
                total_estimated_minutes += estimate.get('estimated_time_remaining_minutes', 0)
            
            # Calculate time available
            days_available = (target_date - datetime.now()).days
            if days_available <= 0:
                return {
                    'feasible': False,
                    'reason': 'Target date is in the past or today',
                    'required_daily_minutes': 0
                }
            
            # Calculate required daily reading time
            required_daily_minutes = total_estimated_minutes / days_available
            daily_avg_minutes = self._get_daily_reading_average()
            
            # Determine feasibility
            feasible = required_daily_minutes <= (daily_avg_minutes * 1.5)  # Allow 50% increase
            
            return {
                'target_date': target_date.isoformat(),
                'days_available': days_available,
                'total_estimated_minutes': round(total_estimated_minutes, 1),
                'total_estimated_formatted': self._format_time_estimate(total_estimated_minutes),
                'required_daily_minutes': round(required_daily_minutes, 1),
                'current_daily_average': round(daily_avg_minutes, 1),
                'feasible': feasible,
                'difficulty_ratio': round(required_daily_minutes / daily_avg_minutes, 1) if daily_avg_minutes > 0 else None,
                'recommendation': self._get_goal_recommendation(feasible, required_daily_minutes, daily_avg_minutes)
            }
            
        except Exception as e:
            print(f"❌ Error estimating goal feasibility: {e}")
            return {}
    
    def _get_document_reading_speed(self, document_id: int) -> float:
        """Get average time per page for a specific document"""
        try:
            # Get recent sessions for this document
            sessions = self.session.query(ReadingSession).filter_by(
                document_id=document_id
            ).order_by(ReadingSession.start_time.desc()).limit(10).all()
            
            total_time = 0
            total_pages = 0
            
            for session in sessions:
                if session.duration and session.pages_read and session.pages_read > 0:
                    total_time += session.duration * 60  # Convert to seconds
                    total_pages += session.pages_read
            
            if total_pages >= self.minimum_sample_pages:
                return total_time / total_pages
            else:
                # Fall back to user's overall reading speed
                return self._get_user_overall_reading_speed()
                
        except Exception as e:
            print(f"❌ Error getting document reading speed: {e}")
            return self.default_time_per_page
    
    def _get_user_overall_reading_speed(self) -> float:
        """Get user's overall reading speed across all documents"""
        try:
            # Get recent sessions across all documents
            sessions = self.session.query(ReadingSession).filter(
                and_(
                    ReadingSession.duration.isnot(None),
                    ReadingSession.pages_read.isnot(None),
                    ReadingSession.pages_read > 0
                )
            ).order_by(ReadingSession.start_time.desc()).limit(50).all()
            
            total_time = 0
            total_pages = 0
            
            for session in sessions:
                total_time += session.duration * 60  # Convert to seconds
                total_pages += session.pages_read
            
            if total_pages >= self.minimum_sample_pages:
                return total_time / total_pages
            else:
                return self.default_time_per_page
                
        except Exception as e:
            print(f"❌ Error getting overall reading speed: {e}")
            return self.default_time_per_page
    
    def _get_daily_reading_average(self) -> float:
        """Get user's average daily reading time in minutes"""
        try:
            # Get sessions from last 30 days
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            result = self.session.query(
                func.avg(ReadingSession.duration)
            ).filter(
                and_(
                    ReadingSession.start_time >= thirty_days_ago,
                    ReadingSession.duration.isnot(None)
                )
            ).scalar()
            
            return float(result) if result else 30.0  # Default 30 minutes
            
        except Exception as e:
            print(f"❌ Error getting daily average: {e}")
            return 30.0
    
    def _calculate_confidence_level(self, document_id: int) -> str:
        """Calculate confidence level of the estimate"""
        try:
            session_count = self.session.query(ReadingSession).filter_by(
                document_id=document_id
            ).count()
            
            if session_count >= 5:
                return "High"
            elif session_count >= 2:
                return "Medium"
            else:
                return "Low"
                
        except Exception as e:
            return "Unknown"
    
    def _format_time_estimate(self, minutes: float) -> str:
        """Format time estimate in human-readable format"""
        if minutes < 60:
            return f"{int(minutes)}m"
        else:
            hours = int(minutes // 60)
            remaining_minutes = int(minutes % 60)
            if remaining_minutes == 0:
                return f"{hours}h"
            else:
                return f"{hours}h {remaining_minutes}m"
    
    def _get_reading_recommendation(self, estimated_minutes: float, days_to_complete: float) -> str:
        """Get recommendation based on estimated time"""
        if estimated_minutes < 30:
            return "Quick read - can finish in one session"
        elif estimated_minutes < 120:
            return "Medium read - plan 2-3 focused sessions"
        elif days_to_complete and days_to_complete < 7:
            return "Intensive reading needed - consider daily sessions"
        else:
            return "Long-term reading - pace yourself with regular sessions"
    
    def _get_overall_recommendation(self, total_minutes: float, days_to_complete: float) -> str:
        """Get overall reading recommendation"""
        if total_minutes < 60:
            return "Light reading load - easily manageable"
        elif total_minutes < 300:  # 5 hours
            return "Moderate reading load - plan regular sessions"
        elif days_to_complete and days_to_complete < 14:
            return "Heavy reading load - consider intensive study schedule"
        else:
            return "Substantial reading ahead - create structured study plan"
    
    def _get_goal_recommendation(self, feasible: bool, required_daily: float, current_average: float) -> str:
        """Get recommendation for goal feasibility"""
        if feasible:
            if required_daily <= current_average:
                return "Goal is easily achievable at your current pace"
            else:
                increase = (required_daily / current_average - 1) * 100
                return f"Goal is achievable with {increase:.0f}% increase in daily reading"
        else:
            if required_daily > current_average * 2:
                return "Goal requires significant increase in reading time - consider extending deadline"
            else:
                return "Goal is challenging but possible with focused effort"
    
    def close(self):
        """Close database session"""
        if self.session:
            self.session.close()
