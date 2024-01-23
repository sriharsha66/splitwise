from typing import List, Optional, Union
from collections import defaultdict, ChainMap
from enum import Enum

class SplitType(Enum):
  EQUAL = 'equal'
  EXACT = 'exact'
  PERCENT = 'percent'

class TransactionType(Enum):
  OWE = 'owe'
  LEND = 'lend'
  
class Transaction:
  def __init__(self, amount: int, user_id: str, type: TransactionType):
    self.amount = amount
    self._type = type
    self.user_id = user_id

  @property
  def owed(self) -> bool:
    return self._type == TransactionType.OWE

  @property
  def lent(self) -> bool:
    return self._type == TransactionType.LEND

class SplitService:
  def __init__(self):
    self.transactions_for_users = defaultdict(list)

  def expense(self, amount_paid: int, user_owed: str, num_users: int, users: List[str], split_type: SplitType, split_amount: Optional[List[Union[int, float]]] = None):
    self.validate(split_type=split_type, split_amount=split_amount, num_users=num_users, amount_paid=amount_paid)
    
    if split_type == SplitType.EQUAL:
      amount_owed = amount_paid / num_users

      for user_id in users:
        if user_id == user_owed:
          continue
          
        self.transactions_for_users[user_owed].append(Transaction(user_id=user_id, amount=amount_owed, type=TransactionType.LEND))
        self.transactions_for_users[user_id].append(Transaction(user_id=user_owed, amount=amount_owed, type=TransactionType.OWE))

    if split_type == SplitType.EXACT:
      for user_id, amount_owed in zip(users, split_amount):
        if user_id == user_owed:
          continue
          
        self.transactions_for_users[user_owed].append(Transaction(user_id=user_id, amount=amount_owed, type=TransactionType.LEND))
        self.transactions_for_users[user_id].append(Transaction(user_id=user_owed, amount=amount_owed, type=TransactionType.OWE))

    if split_type == SplitType.PERCENT:
      for user_id, owed_percent in zip(users, split_amount):
        if user_id == user_owed:
          continue
          
        amount_owed = round((amount_paid * owed_percent / 100), 2)
        
        self.transactions_for_users[user_owed].append(Transaction(user_id=user_id, amount=amount_owed, type=TransactionType.LEND))
        self.transactions_for_users[user_id].append(Transaction(user_id=user_owed, amount=amount_owed, type=TransactionType.OWE))

  def validate(self, split_type: SplitType, split_amount: List[int], num_users: int, amount_paid: int):
    if split_type == SplitType.EQUAL:
      return

    if split_type == SplitType.EXACT:
      if num_users != len(split_amount):
        raise Exception(f'The number of users owing {len(split_amount)}, does not equal the total number of users {num_users}')
        
      if amount_paid != sum(split_amount):
        raise Exception(f'The sum of the split amount {split_amount} = {sum(split_amount)} does not equal the total amount paid {amount_paid}')

    if split_type == SplitType.PERCENT:
      if num_users != len(split_amount):
        raise Exception(f'The number of users owing {len(split_amount)}, does not equal the total number of users {num_users}')

      if 100 != sum(split_amount):
        raise Exception(f'The total percentage of {sum(split_amount)} does not equal 100')

  def calculate_transactions(self, user_id: str):
    if user_id not in self.transactions_for_users:
      print(f'No balances for {user_id}')
      return {}
      
    transaction_map = defaultdict(int)
    users_in_debt = defaultdict(list)
    
    for transaction in self.transactions_for_users[user_id]:
      if transaction.owed:
        transaction_map[transaction.user_id] += transaction.amount

      if transaction.lent:
        transaction_map[transaction.user_id] -= transaction.amount

    
    if all(amount_owed == 0 for _, amount_owed in transaction_map.items()):
      return {}
      
    for other_user_id, amount_owed in transaction_map.items():
      amount_owed = round(amount_owed, 2)
      
      if amount_owed < 0:
        users_in_debt[other_user_id].append((user_id, abs(amount_owed)))
        
      if amount_owed > 0:
        users_in_debt[user_id].append((other_user_id, amount_owed))

    return users_in_debt
    
  def show(self, user_id: Optional[str] = None):
    users_in_debt = defaultdict(list)
    
    if user_id:
      print('====' * 10)
      print('fshowing transactions for user: {user_id}\n')
      
      users_in_debt = self.calculate_transactions(user_id=user_id)
    else:
      print('====' * 10)
      print('showing transactions for all\n')
        
      for user_id in self.transactions_for_users.keys():
        for user_in_debt, owed_users in self.calculate_transactions(user_id=user_id).items():
          users_in_debt[user_in_debt] = list(set(users_in_debt[user_in_debt] + owed_users))

    if not users_in_debt:
      print('No balances')
      
    for user_in_debt, users_owed in users_in_debt.items():
        for (user_owed, amount_owed) in users_owed:
          print(f'{user_in_debt} owes {user_owed}: {abs(amount_owed)}')

# Inputs
split_service = SplitService()
split_service.show()
split_service.show(user_id='u1')
split_service.expense(amount_paid=1000,
                      user_owed='u1',
                      num_users=4,
                      users=['u1', 'u2', 'u3', 'u4'],
                      split_type=SplitType.EQUAL)
split_service.show(user_id='u4')
split_service.show(user_id='u1')
split_service.expense(amount_paid=1250,
                      user_owed='u1',
                      num_users=2,
                      users=['u2', 'u3'],
                      split_type=SplitType.EXACT,
                      split_amount=[370, 880])
split_service.show()
split_service.expense(amount_paid=1500,
                      user_owed='u4',
                      num_users=4,
                      users=['u1', 'u2', 'u3', 'u4'],
                      split_type=SplitType.PERCENT,
                      split_amount=[40, 20, 20, 20])
split_service.show(user_id='u1')
split_service.show()