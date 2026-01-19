"""
MetaTrader 5 integration for order execution
"""
import MetaTrader5 as mt5
from typing import Dict, Optional, List
from datetime import datetime
import logging

from ..core.config import Config


class MT5Connector:
    """
    MetaTrader 5 connector for order execution and market data
    """
    
    def __init__(self, config: Config):
        """
        Initialize MT5 connector
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.symbol = config.symbol
        self.magic_number = config.magic_number
        self.deviation = config.get('metatrader.deviation', 10)
        self.connected = False
        
        self.logger = logging.getLogger(__name__)
    
    def connect(self, login: int = None, password: str = None, 
                server: str = None) -> bool:
        """
        Connect to MetaTrader 5
        
        Args:
            login: MT5 account number
            password: MT5 account password
            server: MT5 server
            
        Returns:
            True if connection successful
        """
        try:
            # Initialize MT5
            if not mt5.initialize():
                self.logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
            
            # Login if credentials provided
            if login and password and server:
                if not mt5.login(login, password, server):
                    self.logger.error(f"MT5 login failed: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self.connected = True
            self.logger.info("MT5 connected successfully")
            
            # Get account info
            account_info = mt5.account_info()
            if account_info:
                self.logger.info(f"Account: {account_info.login}, Balance: {account_info.balance}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"MT5 connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MetaTrader 5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("MT5 disconnected")
    
    def get_symbol_info(self, symbol: str = None) -> Optional[Dict]:
        """
        Get symbol information
        
        Args:
            symbol: Symbol name (defaults to configured symbol)
            
        Returns:
            Dictionary with symbol info or None
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        symbol = symbol or self.symbol
        
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                self.logger.error(f"Symbol {symbol} not found")
                return None
            
            return {
                'symbol': info.name,
                'point': info.point,
                'digits': info.digits,
                'spread': info.spread,
                'contract_size': info.trade_contract_size,
                'min_lot': info.volume_min,
                'max_lot': info.volume_max,
                'lot_step': info.volume_step,
                'bid': info.bid,
                'ask': info.ask
            }
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Get account information
        
        Returns:
            Dictionary with account info or None
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'free_margin': info.margin_free,
                'profit': info.profit,
                'currency': info.currency
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    def get_rates(self, symbol: str = None, timeframe: str = None, 
                  count: int = 500) -> Optional[List]:
        """
        Get historical rates
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe (e.g., 'M15')
            count: Number of candles
            
        Returns:
            List of rates or None
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        symbol = symbol or self.symbol
        timeframe = timeframe or self.config.timeframe
        
        # Convert timeframe string to MT5 constant
        tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_M15)
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            if rates is None:
                self.logger.error(f"Failed to get rates: {mt5.last_error()}")
                return None
            
            return rates
            
        except Exception as e:
            self.logger.error(f"Error getting rates: {e}")
            return None
    
    def open_position(self, symbol: str, order_type: str, volume: float,
                     price: float = None, sl: float = None, tp: float = None,
                     comment: str = "") -> Optional[Dict]:
        """
        Open a trading position
        
        Args:
            symbol: Symbol name
            order_type: 'BUY' or 'SELL'
            volume: Position size in lots
            price: Entry price (None for market order)
            sl: Stop loss price
            tp: Take profit price
            comment: Order comment
            
        Returns:
            Order result dictionary or None
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return None
        
        try:
            # Determine order type
            if order_type.upper() == 'BUY':
                order_type_mt5 = mt5.ORDER_TYPE_BUY
                price = price or mt5.symbol_info_tick(symbol).ask
            else:  # SELL
                order_type_mt5 = mt5.ORDER_TYPE_SELL
                price = price or mt5.symbol_info_tick(symbol).bid
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type_mt5,
                "price": price,
                "deviation": self.deviation,
                "magic": self.magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Add SL/TP if provided
            if sl is not None:
                request["sl"] = float(sl)
            if tp is not None:
                request["tp"] = float(tp)
            
            # Send order
            result = mt5.order_send(request)
            
            if result is None:
                self.logger.error(f"Order send failed: {mt5.last_error()}")
                return None
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Order failed: {result.retcode}, {result.comment}")
                return None
            
            self.logger.info(f"Order opened: {order_type} {volume} {symbol} at {result.price}")
            
            return {
                'ticket': result.order,
                'volume': result.volume,
                'price': result.price,
                'type': order_type,
                'sl': sl,
                'tp': tp,
                'comment': comment
            }
            
        except Exception as e:
            self.logger.error(f"Error opening position: {e}")
            return None
    
    def close_position(self, ticket: int, volume: float = None) -> bool:
        """
        Close an open position
        
        Args:
            ticket: Position ticket number
            volume: Volume to close (None for full position)
            
        Returns:
            True if successful
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return False
        
        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if not position:
                self.logger.error(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            # Determine close parameters
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask
            
            close_volume = volume or position.volume
            
            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": float(close_volume),
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": self.deviation,
                "magic": self.magic_number,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send close order
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Position close failed: {result.retcode if result else 'None'}")
                return False
            
            self.logger.info(f"Position {ticket} closed: {close_volume} lots at {result.price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    def modify_position(self, ticket: int, sl: float = None, tp: float = None) -> bool:
        """
        Modify position SL/TP
        
        Args:
            ticket: Position ticket
            sl: New stop loss
            tp: New take profit
            
        Returns:
            True if successful
        """
        if not self.connected:
            self.logger.error("Not connected to MT5")
            return False
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                self.logger.error(f"Position {ticket} not found")
                return False
            
            position = position[0]
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": float(sl) if sl is not None else position.sl,
                "tp": float(tp) if tp is not None else position.tp,
            }
            
            result = mt5.order_send(request)
            
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error(f"Position modify failed: {result.retcode if result else 'None'}")
                return False
            
            self.logger.info(f"Position {ticket} modified: SL={sl}, TP={tp}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error modifying position: {e}")
            return False
    
    def get_open_positions(self, symbol: str = None) -> List[Dict]:
        """
        Get all open positions
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of open positions
        """
        if not self.connected:
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            result = []
            for pos in positions:
                result.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'magic': pos.magic,
                    'comment': pos.comment
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
