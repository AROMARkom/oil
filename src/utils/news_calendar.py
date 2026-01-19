"""
News calendar and EIA news avoidance
"""
from datetime import datetime, timedelta
from typing import Dict, List
import pytz

from ..core.config import Config


class NewsCalendar:
    """
    News calendar for avoiding high-impact news events (especially EIA)
    """
    
    def __init__(self, config: Config):
        """
        Initialize news calendar
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # EIA settings
        self.eia_enabled = config.get('news.eia.enabled', True)
        self.avoid_before = config.get('news.eia.avoid_minutes_before', 30)
        self.avoid_after = config.get('news.eia.avoid_minutes_after', 60)
        self.release_day = config.get('news.eia.release_day', 3)  # Wednesday
        self.release_hour = config.get('news.eia.release_hour', 15)  # 15:30 UTC
        self.release_minute = config.get('news.eia.release_minute', 30)
    
    def is_eia_release_time(self, current_time: datetime) -> Dict:
        """
        Check if current time is during EIA release window
        
        EIA Petroleum Status Report is released every Wednesday at 10:30 AM ET (15:30 UTC)
        
        Args:
            current_time: Current datetime
            
        Returns:
            Dictionary with EIA status
        """
        if not self.eia_enabled:
            return {
                'is_eia_time': False,
                'reason': 'EIA filtering disabled'
            }
        
        # Ensure UTC timezone
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)
        
        # Check if it's Wednesday (0=Monday, 3=Wednesday)
        if current_time.weekday() != self.release_day:
            return {
                'is_eia_time': False,
                'reason': f'Not EIA release day (current: {current_time.strftime("%A")})'
            }
        
        # Create EIA release datetime for current week
        eia_release = current_time.replace(
            hour=self.release_hour,
            minute=self.release_minute,
            second=0,
            microsecond=0
        )
        
        # Calculate avoidance window
        avoid_start = eia_release - timedelta(minutes=self.avoid_before)
        avoid_end = eia_release + timedelta(minutes=self.avoid_after)
        
        # Check if current time is in avoidance window
        if avoid_start <= current_time <= avoid_end:
            minutes_to_release = int((eia_release - current_time).total_seconds() / 60)
            return {
                'is_eia_time': True,
                'reason': f'EIA release window (±{self.avoid_before}/{self.avoid_after} min)',
                'release_time': eia_release,
                'minutes_to_release': minutes_to_release
            }
        
        return {
            'is_eia_time': False,
            'reason': 'Outside EIA release window'
        }
    
    def can_trade(self, current_time: datetime) -> Dict:
        """
        Check if trading is allowed based on news calendar
        
        Args:
            current_time: Current datetime
            
        Returns:
            Dictionary with trading permission
        """
        # Check EIA
        eia_status = self.is_eia_release_time(current_time)
        
        if eia_status['is_eia_time']:
            return {
                'allowed': False,
                'reason': f"EIA release time - {eia_status['reason']}"
            }
        
        return {
            'allowed': True,
            'reason': 'No major news events'
        }
    
    def get_next_eia_release(self, current_time: datetime) -> datetime:
        """
        Get next EIA release datetime
        
        Args:
            current_time: Current datetime
            
        Returns:
            Next EIA release datetime
        """
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)
        
        # Calculate days until next Wednesday
        days_ahead = self.release_day - current_time.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_wednesday = current_time + timedelta(days=days_ahead)
        
        # Set release time
        next_release = next_wednesday.replace(
            hour=self.release_hour,
            minute=self.release_minute,
            second=0,
            microsecond=0
        )
        
        # If today is Wednesday but past release time, get next week
        if current_time.weekday() == self.release_day:
            release_today = current_time.replace(
                hour=self.release_hour,
                minute=self.release_minute,
                second=0,
                microsecond=0
            )
            if current_time > release_today:
                next_release = next_release + timedelta(days=7)
        
        return next_release
    
    def get_news_schedule(self, current_time: datetime, days_ahead: int = 7) -> List[Dict]:
        """
        Get upcoming news schedule
        
        Args:
            current_time: Current datetime
            days_ahead: Number of days to look ahead
            
        Returns:
            List of upcoming news events
        """
        schedule = []
        
        if self.eia_enabled:
            # Get next EIA releases
            next_release = self.get_next_eia_release(current_time)
            
            # Add weekly releases for specified days ahead
            weeks = (days_ahead // 7) + 1
            for i in range(weeks):
                release_time = next_release + timedelta(weeks=i)
                if release_time <= current_time + timedelta(days=days_ahead):
                    schedule.append({
                        'event': 'EIA Petroleum Status Report',
                        'datetime': release_time,
                        'impact': 'HIGH',
                        'avoid_before': self.avoid_before,
                        'avoid_after': self.avoid_after
                    })
        
        return sorted(schedule, key=lambda x: x['datetime'])
