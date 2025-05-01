"""
Transaction Support for P.U.L.S.E.
Provides write-ahead logging for transaction integrity
"""

import os
import json
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Union, TypeVar, Generic, cast
from datetime import datetime
import structlog
from enum import Enum

from utils.repository.base import Entity, Repository, TransactionalRepository
from utils.error_handler import with_error_handling, ErrorSource
from utils.circuit_breaker import circuit_breaker

# Configure logger
logger = structlog.get_logger("transaction")

# Type variables
T = TypeVar('T', bound=Entity)

class TransactionStatus(str, Enum):
    """Transaction status enum"""
    PENDING = "pending"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"

class TransactionOperation(str, Enum):
    """Transaction operation enum"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class TransactionLog:
    """Transaction log entry"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        entity_type: str = "",
        entity_id: str = "",
        operation: TransactionOperation = TransactionOperation.CREATE,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize transaction log entry
        
        Args:
            id: Optional log entry ID (generated if not provided)
            entity_type: Entity type
            entity_id: Entity ID
            operation: Operation type
            data: Entity data
            timestamp: Timestamp (current time if not provided)
        """
        self.id = id or str(uuid.uuid4())
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.operation = operation
        self.data = data or {}
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert log entry to dictionary
        
        Returns:
            Dictionary representation of log entry
        """
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionLog':
        """
        Create log entry from dictionary
        
        Args:
            data: Dictionary representation of log entry
            
        Returns:
            Log entry instance
        """
        # Parse timestamp
        timestamp = None
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # Create log entry
        return TransactionLog(
            id=data.get("id"),
            entity_type=data.get("entity_type", ""),
            entity_id=data.get("entity_id", ""),
            operation=data.get("operation", TransactionOperation.CREATE),
            data=data.get("data", {}),
            timestamp=timestamp
        )

class Transaction:
    """Transaction for atomic operations"""
    
    def __init__(
        self,
        id: Optional[str] = None,
        status: TransactionStatus = TransactionStatus.PENDING,
        logs: Optional[List[TransactionLog]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize transaction
        
        Args:
            id: Optional transaction ID (generated if not provided)
            status: Transaction status
            logs: Transaction logs
            timestamp: Timestamp (current time if not provided)
        """
        self.id = id or str(uuid.uuid4())
        self.status = status
        self.logs = logs or []
        self.timestamp = timestamp or datetime.now()
    
    def add_log(self, log: TransactionLog) -> None:
        """
        Add log entry to transaction
        
        Args:
            log: Log entry to add
        """
        self.logs.append(log)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert transaction to dictionary
        
        Returns:
            Dictionary representation of transaction
        """
        return {
            "id": self.id,
            "status": self.status,
            "logs": [log.to_dict() for log in self.logs],
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Create transaction from dictionary
        
        Args:
            data: Dictionary representation of transaction
            
        Returns:
            Transaction instance
        """
        # Parse timestamp
        timestamp = None
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                timestamp = datetime.fromisoformat(data["timestamp"])
            elif isinstance(data["timestamp"], datetime):
                timestamp = data["timestamp"]
        
        # Parse logs
        logs = []
        if "logs" in data and data["logs"]:
            for log_data in data["logs"]:
                logs.append(TransactionLog.from_dict(log_data))
        
        # Create transaction
        return Transaction(
            id=data.get("id"),
            status=data.get("status", TransactionStatus.PENDING),
            logs=logs,
            timestamp=timestamp
        )

class TransactionManager:
    """Transaction manager for atomic operations"""
    
    def __init__(self, log_dir: str = "data/transactions"):
        """
        Initialize transaction manager
        
        Args:
            log_dir: Directory for transaction logs
        """
        self.log_dir = log_dir
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Active transactions
        self.active_transactions: Dict[str, Transaction] = {}
        
        # Lock for thread safety
        self.lock = asyncio.Lock()
    
    def _get_log_path(self, transaction_id: str) -> str:
        """
        Get path to transaction log file
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Path to log file
        """
        return os.path.join(self.log_dir, f"{transaction_id}.json")
    
    async def _write_log(self, transaction: Transaction) -> None:
        """
        Write transaction log to disk
        
        Args:
            transaction: Transaction to log
        """
        # Get log path
        log_path = self._get_log_path(transaction.id)
        
        # Write log to disk
        async with asyncio.Lock():
            with open(log_path, "w") as f:
                json.dump(transaction.to_dict(), f, indent=2)
    
    async def _read_log(self, transaction_id: str) -> Optional[Transaction]:
        """
        Read transaction log from disk
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        # Get log path
        log_path = self._get_log_path(transaction_id)
        
        # Check if log exists
        if not os.path.exists(log_path):
            return None
        
        # Read log from disk
        try:
            with open(log_path, "r") as f:
                data = json.load(f)
                return Transaction.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to read transaction log: {str(e)}")
            return None
    
    async def _delete_log(self, transaction_id: str) -> None:
        """
        Delete transaction log from disk
        
        Args:
            transaction_id: Transaction ID
        """
        # Get log path
        log_path = self._get_log_path(transaction_id)
        
        # Delete log if it exists
        if os.path.exists(log_path):
            os.remove(log_path)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def begin_transaction(self) -> Transaction:
        """
        Begin a new transaction
        
        Returns:
            Transaction object
        """
        async with self.lock:
            # Create transaction
            transaction = Transaction()
            
            # Add to active transactions
            self.active_transactions[transaction.id] = transaction
            
            # Write transaction log
            await self._write_log(transaction)
            
            logger.info(f"Transaction {transaction.id} started")
            
            return transaction
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def commit_transaction(self, transaction_id: str) -> bool:
        """
        Commit a transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if transaction was committed, False otherwise
        """
        async with self.lock:
            # Get transaction
            transaction = self.active_transactions.get(transaction_id)
            
            if not transaction:
                # Try to read from disk
                transaction = await self._read_log(transaction_id)
                
                if not transaction:
                    logger.warning(f"Transaction {transaction_id} not found")
                    return False
            
            # Check if transaction is already committed or rolled back
            if transaction.status != TransactionStatus.PENDING:
                logger.warning(f"Transaction {transaction_id} is already {transaction.status}")
                return False
            
            # Update transaction status
            transaction.status = TransactionStatus.COMMITTED
            
            # Write transaction log
            await self._write_log(transaction)
            
            # Remove from active transactions
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
            
            logger.info(f"Transaction {transaction_id} committed")
            
            return True
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def rollback_transaction(self, transaction_id: str) -> bool:
        """
        Rollback a transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            True if transaction was rolled back, False otherwise
        """
        async with self.lock:
            # Get transaction
            transaction = self.active_transactions.get(transaction_id)
            
            if not transaction:
                # Try to read from disk
                transaction = await self._read_log(transaction_id)
                
                if not transaction:
                    logger.warning(f"Transaction {transaction_id} not found")
                    return False
            
            # Check if transaction is already committed or rolled back
            if transaction.status != TransactionStatus.PENDING:
                logger.warning(f"Transaction {transaction_id} is already {transaction.status}")
                return False
            
            # Update transaction status
            transaction.status = TransactionStatus.ROLLED_BACK
            
            # Write transaction log
            await self._write_log(transaction)
            
            # Remove from active transactions
            if transaction_id in self.active_transactions:
                del self.active_transactions[transaction_id]
            
            logger.info(f"Transaction {transaction_id} rolled back")
            
            return True
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def add_log(self, transaction_id: str, log: TransactionLog) -> bool:
        """
        Add log entry to transaction
        
        Args:
            transaction_id: Transaction ID
            log: Log entry to add
            
        Returns:
            True if log was added, False otherwise
        """
        async with self.lock:
            # Get transaction
            transaction = self.active_transactions.get(transaction_id)
            
            if not transaction:
                # Try to read from disk
                transaction = await self._read_log(transaction_id)
                
                if not transaction:
                    logger.warning(f"Transaction {transaction_id} not found")
                    return False
                
                # Add to active transactions
                self.active_transactions[transaction_id] = transaction
            
            # Check if transaction is already committed or rolled back
            if transaction.status != TransactionStatus.PENDING:
                logger.warning(f"Transaction {transaction_id} is already {transaction.status}")
                return False
            
            # Add log entry
            transaction.add_log(log)
            
            # Write transaction log
            await self._write_log(transaction)
            
            return True
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get transaction by ID
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction if found, None otherwise
        """
        # Get transaction from active transactions
        transaction = self.active_transactions.get(transaction_id)
        
        if transaction:
            return transaction
        
        # Try to read from disk
        return await self._read_log(transaction_id)
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def get_pending_transactions(self) -> List[Transaction]:
        """
        Get all pending transactions
        
        Returns:
            List of pending transactions
        """
        # Get pending transactions from active transactions
        pending = [t for t in self.active_transactions.values() if t.status == TransactionStatus.PENDING]
        
        # Get pending transactions from disk
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".json"):
                transaction_id = filename[:-5]
                
                # Skip active transactions
                if transaction_id in self.active_transactions:
                    continue
                
                # Read transaction
                transaction = await self._read_log(transaction_id)
                
                if transaction and transaction.status == TransactionStatus.PENDING:
                    pending.append(transaction)
        
        return pending
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def recover_transactions(self) -> Dict[str, Any]:
        """
        Recover pending transactions
        
        Returns:
            Recovery result with counts
        """
        # Get pending transactions
        pending = await self.get_pending_transactions()
        
        # Recovery stats
        result = {
            "pending": len(pending),
            "committed": 0,
            "rolled_back": 0,
            "errors": 0
        }
        
        # Process each pending transaction
        for transaction in pending:
            try:
                # Check transaction age
                age = (datetime.now() - transaction.timestamp).total_seconds()
                
                # If transaction is older than 1 hour, roll it back
                if age > 3600:
                    await self.rollback_transaction(transaction.id)
                    result["rolled_back"] += 1
                else:
                    # Otherwise, commit it
                    await self.commit_transaction(transaction.id)
                    result["committed"] += 1
            except Exception as e:
                logger.error(f"Failed to recover transaction {transaction.id}: {str(e)}")
                result["errors"] += 1
        
        return result
    
    @with_error_handling(source=ErrorSource.APPLICATION)
    async def cleanup_transactions(self, max_age: int = 86400) -> Dict[str, Any]:
        """
        Clean up old transactions
        
        Args:
            max_age: Maximum age of transactions to keep (in seconds)
            
        Returns:
            Cleanup result with counts
        """
        # Cleanup stats
        result = {
            "deleted": 0,
            "errors": 0
        }
        
        # Get current time
        now = datetime.now()
        
        # Process each transaction log file
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".json"):
                transaction_id = filename[:-5]
                
                try:
                    # Read transaction
                    transaction = await self._read_log(transaction_id)
                    
                    if not transaction:
                        continue
                    
                    # Check transaction age
                    age = (now - transaction.timestamp).total_seconds()
                    
                    # If transaction is older than max_age, delete it
                    if age > max_age:
                        # Delete transaction log
                        await self._delete_log(transaction_id)
                        result["deleted"] += 1
                except Exception as e:
                    logger.error(f"Failed to clean up transaction {transaction_id}: {str(e)}")
                    result["errors"] += 1
        
        return result

class TransactionalRepositoryImpl(TransactionalRepository[T, str]):
    """Transactional repository implementation"""
    
    def __init__(
        self,
        repository: Repository[T, str],
        transaction_manager: TransactionManager,
        entity_type: str
    ):
        """
        Initialize transactional repository
        
        Args:
            repository: Base repository
            transaction_manager: Transaction manager
            entity_type: Entity type
        """
        self.repository = repository
        self.transaction_manager = transaction_manager
        self.entity_type = entity_type
    
    async def save(self, entity: T) -> T:
        """
        Save entity to repository
        
        Args:
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        return await self.repository.save(entity)
    
    async def find_by_id(self, id: str) -> Optional[T]:
        """
        Find entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            Entity if found, None otherwise
        """
        return await self.repository.find_by_id(id)
    
    async def find_all(self) -> List[T]:
        """
        Find all entities
        
        Returns:
            List of all entities
        """
        return await self.repository.find_all()
    
    async def delete(self, id: str) -> bool:
        """
        Delete entity by ID
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        return await self.repository.delete(id)
    
    async def exists(self, id: str) -> bool:
        """
        Check if entity exists
        
        Args:
            id: Entity ID
            
        Returns:
            True if entity exists, False otherwise
        """
        return await self.repository.exists(id)
    
    async def count(self) -> int:
        """
        Count entities in repository
        
        Returns:
            Number of entities
        """
        return await self.repository.count()
    
    async def begin_transaction(self) -> Transaction:
        """
        Begin a transaction
        
        Returns:
            Transaction object
        """
        return await self.transaction_manager.begin_transaction()
    
    async def commit_transaction(self, transaction: Transaction) -> bool:
        """
        Commit a transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            True if transaction was committed, False otherwise
        """
        return await self.transaction_manager.commit_transaction(transaction.id)
    
    async def rollback_transaction(self, transaction: Transaction) -> bool:
        """
        Rollback a transaction
        
        Args:
            transaction: Transaction object
            
        Returns:
            True if transaction was rolled back, False otherwise
        """
        return await self.transaction_manager.rollback_transaction(transaction.id)
    
    async def save_in_transaction(self, transaction: Transaction, entity: T) -> T:
        """
        Save entity in transaction
        
        Args:
            transaction: Transaction object
            entity: Entity to save
            
        Returns:
            Saved entity with ID
        """
        # Check if entity exists
        exists = await self.exists(entity.id)
        
        # Create log entry
        log = TransactionLog(
            entity_type=self.entity_type,
            entity_id=entity.id,
            operation=TransactionOperation.UPDATE if exists else TransactionOperation.CREATE,
            data=entity.to_dict()
        )
        
        # Add log to transaction
        await self.transaction_manager.add_log(transaction.id, log)
        
        # Save entity
        return await self.repository.save(entity)
    
    async def delete_in_transaction(self, transaction: Transaction, id: str) -> bool:
        """
        Delete entity in transaction
        
        Args:
            transaction: Transaction object
            id: Entity ID
            
        Returns:
            True if entity was deleted, False otherwise
        """
        # Check if entity exists
        entity = await self.find_by_id(id)
        
        if not entity:
            return False
        
        # Create log entry
        log = TransactionLog(
            entity_type=self.entity_type,
            entity_id=id,
            operation=TransactionOperation.DELETE,
            data=entity.to_dict()
        )
        
        # Add log to transaction
        await self.transaction_manager.add_log(transaction.id, log)
        
        # Delete entity
        return await self.repository.delete(id)
