"""
Main WTI Oil Trading Bot
"""
import logging
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional

from .core.config import Config
from .strategies.volatility_expansion import VolatilityExpansionStrategy
from .risk.risk_manager import RiskManager
from .risk.profit_manager import ProfitManager
from .execution.mt5_connector import MT5Connector
from .utils.session_filter import SessionFilter
from .utils.news_calendar import NewsCalendar
from .utils.logger import setup_logger


class WTIOilTradingBot:
    """
    Systematic trading bot for WTI Oil (CFD)
    
    Strategy: Volatility expansion with structural breakout
    Timeframe: M15
    Risk Management: ATR-based with drawdown control
    Execution: MetaTrader 5
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize trading bot
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = Config(config_path)
        
        # Setup logging
        self.logger = setup_logger(
            level=self.config.get('logging.level', 'INFO'),
            log_file=self.config.get('logging.file', 'logs/trading_bot.log'),
            console=self.config.get('logging.console', True)
        )
        
        self.logger.info("=" * 60)
        self.logger.info("WTI Oil Trading Bot Initializing")
        self.logger.info("=" * 60)
        
        # Initialize components
        self.strategy = VolatilityExpansionStrategy(self.config)
        self.risk_manager = RiskManager(self.config)
        self.profit_manager = ProfitManager(self.config)
        self.mt5 = MT5Connector(self.config)
        self.session_filter = SessionFilter(self.config)
        self.news_calendar = NewsCalendar(self.config)
        
        # Bot state
        self.running = False
        self.positions = {}  # {ticket: position_info}
        
        self.logger.info(f"Symbol: {self.config.symbol}")
        self.logger.info(f"Timeframe: {self.config.timeframe}")
        self.logger.info(f"Strategy: Volatility Expansion + Structural Breakout")
    
    def connect_mt5(self, login: int = None, password: str = None, 
                    server: str = None) -> bool:
        """
        Connect to MetaTrader 5
        
        Args:
            login: MT5 account number
            password: MT5 password
            server: MT5 server
            
        Returns:
            True if connection successful
        """
        self.logger.info("Connecting to MetaTrader 5...")
        
        if self.mt5.connect(login, password, server):
            self.logger.info("MetaTrader 5 connected successfully")
            
            # Get account info
            account = self.mt5.get_account_info()
            if account:
                self.logger.info(f"Account Balance: {account['balance']} {account['currency']}")
                self.logger.info(f"Account Equity: {account['equity']} {account['currency']}")
            
            return True
        else:
            self.logger.error("Failed to connect to MetaTrader 5")
            return False
    
    def analyze_market(self) -> Optional[Dict]:
        """
        Analyze current market conditions
        
        Returns:
            Analysis results dictionary or None
        """
        # Get historical data
        rates = self.mt5.get_rates(count=200)
        if rates is None or len(rates) == 0:
            self.logger.error("Failed to retrieve market data")
            return None
        
        # Extract OHLC data
        high = np.array([r['high'] for r in rates])
        low = np.array([r['low'] for r in rates])
        close = np.array([r['close'] for r in rates])
        open_price = np.array([r['open'] for r in rates])
        volume = np.array([r['tick_volume'] for r in rates])
        
        # Run strategy analysis
        analysis = self.strategy.analyze(high, low, close, open_price, volume)
        
        return analysis
    
    def check_filters(self, current_time: datetime) -> Dict:
        """
        Check all trading filters
        
        Args:
            current_time: Current datetime
            
        Returns:
            Filter check results
        """
        results = {
            'all_passed': True,
            'checks': {}
        }
        
        # Session filter
        session_check = self.session_filter.is_trading_session(current_time)
        results['checks']['session'] = session_check
        if not session_check['allowed']:
            results['all_passed'] = False
        
        # News filter
        news_check = self.news_calendar.can_trade(current_time)
        results['checks']['news'] = news_check
        if not news_check['allowed']:
            results['all_passed'] = False
        
        # Risk filter
        account = self.mt5.get_account_info()
        if account:
            risk_check = self.risk_manager.can_trade(account['balance'], current_time)
            results['checks']['risk'] = risk_check
            if not risk_check['allowed']:
                results['all_passed'] = False
        else:
            results['all_passed'] = False
            results['checks']['risk'] = {'allowed': False, 'reason': 'Failed to get account info'}
        
        return results
    
    def execute_signal(self, signal_type: str, analysis: Dict):
        """
        Execute trading signal
        
        Args:
            signal_type: 'BUY' or 'SELL'
            analysis: Market analysis results
        """
        self.logger.info(f"Executing {signal_type} signal")
        
        # Get account and symbol info
        account = self.mt5.get_account_info()
        symbol_info = self.mt5.get_symbol_info()
        
        if not account or not symbol_info:
            self.logger.error("Failed to get account/symbol info")
            return
        
        # Calculate entry, SL, TP
        current_price = analysis['current_price']
        current_atr = analysis['current_atr']
        
        entry_price = self.strategy.calculate_entry_price(signal_type, current_price)
        stop_loss = self.strategy.calculate_stop_loss(entry_price, signal_type, current_atr)
        tp_levels = self.strategy.calculate_take_profit_levels(entry_price, signal_type, current_atr)
        
        # Calculate position size
        position_size = self.risk_manager.calculate_position_size(
            account['balance'],
            entry_price,
            stop_loss,
            symbol_info
        )
        
        # Use first TP level for initial TP, or None for manual management
        initial_tp = tp_levels[0]['price'] if tp_levels else None
        
        self.logger.info(f"Entry: {entry_price:.5f}, SL: {stop_loss:.5f}, Size: {position_size:.2f} lots")
        
        # Open position
        result = self.mt5.open_position(
            symbol=self.config.symbol,
            order_type=signal_type,
            volume=position_size,
            price=entry_price,
            sl=stop_loss,
            tp=initial_tp,
            comment=f"VE-{signal_type}"
        )
        
        if result:
            ticket = result['ticket']
            self.positions[ticket] = {
                'ticket': ticket,
                'type': signal_type,
                'entry_price': result['price'],
                'volume': result['volume'],
                'initial_volume': result['volume'],
                'sl': result['sl'],
                'tp': result['tp'],
                'entry_time': datetime.now(),
                'atr_at_entry': current_atr
            }
            
            # Initialize profit manager for this position
            self.profit_manager.initialize_position(ticket)
            
            self.logger.info(f"Position opened successfully: Ticket #{ticket}")
        else:
            self.logger.error("Failed to open position")
    
    def manage_positions(self):
        """
        Manage open positions (partial TP, trailing stop)
        """
        # Get current open positions from MT5
        open_positions = self.mt5.get_open_positions(symbol=self.config.symbol)
        
        if not open_positions:
            return
        
        # Get current market data
        analysis = self.analyze_market()
        if not analysis:
            return
        
        current_atr = analysis['current_atr']
        
        for position in open_positions:
            ticket = position['ticket']
            
            # Skip positions not managed by this bot
            if position['magic'] != self.config.magic_number:
                continue
            
            if ticket not in self.positions:
                # Add to tracking if missing
                self.positions[ticket] = {
                    'ticket': ticket,
                    'type': position['type'],
                    'entry_price': position['price_open'],
                    'volume': position['volume'],
                    'initial_volume': position['volume'],
                    'sl': position['sl'],
                    'tp': position['tp'],
                    'entry_time': datetime.now(),
                    'atr_at_entry': current_atr
                }
                self.profit_manager.initialize_position(ticket)
            
            pos_info = self.positions[ticket]
            
            # Check partial take profit
            tp_actions = self.profit_manager.check_partial_tp(
                ticket,
                pos_info['entry_price'],
                position['price_current'],
                pos_info['type'],
                current_atr,
                pos_info['initial_volume']
            )
            
            for action in tp_actions:
                if action['action'] == 'partial_close':
                    self.logger.info(f"Executing partial close: {action['reason']}")
                    success = self.mt5.close_position(ticket, action['volume'])
                    if success:
                        pos_info['volume'] -= action['volume']
            
            # Check trailing stop
            trail_action = self.profit_manager.check_trailing_stop(
                ticket,
                pos_info['entry_price'],
                position['price_current'],
                pos_info['type'],
                position['sl'],
                current_atr
            )
            
            if trail_action and trail_action['action'] == 'modify_sl':
                self.logger.info(f"Updating trailing stop: {trail_action['reason']}")
                success = self.mt5.modify_position(ticket, sl=trail_action['new_sl'])
                if success:
                    pos_info['sl'] = trail_action['new_sl']
        
        # Clean up closed positions
        current_tickets = {p['ticket'] for p in open_positions}
        closed_tickets = set(self.positions.keys()) - current_tickets
        
        for ticket in closed_tickets:
            self.logger.info(f"Position {ticket} closed")
            self.profit_manager.remove_position(ticket)
            del self.positions[ticket]
    
    def run(self, check_interval: int = 60):
        """
        Main bot loop
        
        Args:
            check_interval: Seconds between checks
        """
        self.logger.info("Starting trading bot main loop")
        self.running = True
        
        try:
            while self.running:
                current_time = datetime.utcnow()
                
                # Check filters
                filter_results = self.check_filters(current_time)
                
                if filter_results['all_passed']:
                    self.logger.debug("All filters passed, analyzing market")
                    
                    # Analyze market
                    analysis = self.analyze_market()
                    
                    if analysis:
                        # Check for signals
                        if analysis['buy_signal']:
                            self.logger.info("BUY signal detected!")
                            self.execute_signal('BUY', analysis)
                        elif analysis['sell_signal']:
                            self.logger.info("SELL signal detected!")
                            self.execute_signal('SELL', analysis)
                    
                    # Manage existing positions
                    self.manage_positions()
                else:
                    # Log why trading is blocked
                    for check_name, check_result in filter_results['checks'].items():
                        if not check_result['allowed']:
                            self.logger.info(f"{check_name.upper()} filter blocked: {check_result['reason']}")
                
                # Log statistics periodically
                if int(time.time()) % 3600 == 0:  # Every hour
                    self.log_statistics()
                
                # Wait before next check
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def log_statistics(self):
        """Log current bot statistics"""
        account = self.mt5.get_account_info()
        if account:
            risk_stats = self.risk_manager.get_statistics(account['balance'])
            
            self.logger.info("=" * 60)
            self.logger.info("BOT STATISTICS")
            self.logger.info(f"Account Balance: {account['balance']:.2f} {account['currency']}")
            self.logger.info(f"Account Equity: {account['equity']:.2f} {account['currency']}")
            self.logger.info(f"Open Positions: {len(self.positions)}")
            self.logger.info(f"Daily Drawdown: {risk_stats['daily_drawdown']*100:.2f}%")
            self.logger.info(f"Total Drawdown: {risk_stats['total_drawdown']*100:.2f}%")
            self.logger.info("=" * 60)
    
    def shutdown(self):
        """Shutdown bot gracefully"""
        self.logger.info("Shutting down trading bot")
        self.running = False
        
        # Close all positions (optional - uncomment if desired)
        # for ticket in list(self.positions.keys()):
        #     self.mt5.close_position(ticket)
        
        # Disconnect MT5
        self.mt5.disconnect()
        
        self.logger.info("Trading bot shutdown complete")


def main():
    """Main entry point"""
    # Create bot instance
    bot = WTIOilTradingBot()
    
    # Connect to MT5 (credentials should be provided via environment or args)
    # For now, assuming MT5 is already logged in
    if bot.connect_mt5():
        # Run the bot
        bot.run(check_interval=60)  # Check every 60 seconds
    else:
        bot.logger.error("Failed to connect to MetaTrader 5")


if __name__ == "__main__":
    main()
