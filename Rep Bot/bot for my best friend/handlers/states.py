from aiogram.fsm.state import State, StatesGroup

class SearchStates(StatesGroup):
    waiting_for_search = State()
    waiting_for_mailing = State()
    waiting_for_admin_search = State()
    waiting_for_ban_reason = State()
    waiting_for_deposit_amount = State()