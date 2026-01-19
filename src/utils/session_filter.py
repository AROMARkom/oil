"""
Session filtering for trading hours (London/NY sessions)
"""
from datetime import datetime, time
from typing import Dict, List
import pytz

from ..core.config import Config


class SessionFilter:
    """
    Filter trading based on market sessions (London, New York)
    """
    
    def __init__(self, config: Config):
        """
        Initialize session filter
        
        Args:
            config: Configuration object
        """
        self.config = config
        
        # London session
        self.london_enabled = config.get('sessions.london.enabled', True)
        self.london_start = config.get('sessions.london.start_hour', 8)
        self.london_end = config.get('sessions.london.end_hour', 16)
        
        # New York session
        self.newyork_enabled = config.get('sessions.newyork.enabled', True)
        self.newyork_start = config.get('sessions.newyork.start_hour', 13)
        self.newyork_end = config.get('sessions.newyork.end_hour', 21)
        
        # Asian session
        self.asian_enabled = config.get('sessions.asian.enabled', False)
    
    def is_trading_session(self, current_time: datetime) -> Dict:
        """
        Check if current time is within allowed trading sessions
        
        Args:
            current_time: Current datetime (should be in UTC)
            
        Returns:
            Dictionary with session status
        """
        # Ensure UTC timezone
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)
        
        hour = current_time.hour
        
        # Check London session
        if self.london_enabled:
            if self.london_start <= hour < self.london_end:
                return {
                    'allowed': True,
                    'session': 'London',
                    'reason': f'London session active ({self.london_start}:00-{self.london_end}:00 UTC)'
                }
        
        # Check New York session
        if self.newyork_enabled:
            if self.newyork_start <= hour < self.newyork_end:
                return {
                    'allowed': True,
                    'session': 'New York',
                    'reason': f'New York session active ({self.newyork_start}:00-{self.newyork_end}:00 UTC)'
                }
        
        # Check if sessions overlap (London/NY overlap)
        if self.london_enabled and self.newyork_enabled:
            overlap_start = max(self.london_start, self.newyork_start)
            overlap_end = min(self.london_end, self.newyork_end)
            if overlap_start < overlap_end and overlap_start <= hour < overlap_end:
                return {
                    'allowed': True,
                    'session': 'London/NY Overlap',
                    'reason': f'London/NY overlap session ({overlap_start}:00-{overlap_end}:00 UTC)'
                }
        
        return {
            'allowed': False,
            'session': 'None',
            'reason': f'Outside trading sessions (current: {hour}:00 UTC)'
        }
    
    def get_active_sessions(self, current_time: datetime) -> List[str]:
        """
        Get list of currently active sessions
        
        Args:
            current_time: Current datetime (UTC)
            
        Returns:
            List of active session names
        """
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)
        
        hour = current_time.hour
        active = []
        
        if self.london_enabled and self.london_start <= hour < self.london_end:
            active.append('London')
        
        if self.newyork_enabled and self.newyork_start <= hour < self.newyork_end:
            active.append('New York')
        
        return active
    
    def next_session_start(self, current_time: datetime) -> Dict:
        """
        Get information about next session start
        
        Args:
            current_time: Current datetime (UTC)
            
        Returns:
            Dictionary with next session info
        """
        if current_time.tzinfo is None:
            current_time = pytz.UTC.localize(current_time)
        else:
            current_time = current_time.astimezone(pytz.UTC)
        
        hour = current_time.hour
        
        # Find next session
        sessions = []
        
        if self.london_enabled:
            sessions.append(('London', self.london_start))
        
        if self.newyork_enabled:
            sessions.append(('New York', self.newyork_start))
        
        # Sort by start hour
        sessions.sort(key=lambda x: x[1])
        
        # Find next session
        for session_name, start_hour in sessions:
            if hour < start_hour:
                hours_until = start_hour - hour
                return {
                    'session': session_name,
                    'start_hour': start_hour,
                    'hours_until': hours_until
                }
        
        # Next session is tomorrow (first session of the day)
        if sessions:
            next_session = sessions[0]
            hours_until = (24 - hour) + next_session[1]
            return {
                'session': next_session[0],
                'start_hour': next_session[1],
                'hours_until': hours_until
            }
        
        return {
            'session': 'None',
            'start_hour': None,
            'hours_until': None
        }
