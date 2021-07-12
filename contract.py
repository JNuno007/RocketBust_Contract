random.seed()
# Hash for transfer movements
# This should be deleted and use currency lib
balance = Hash(default_value=0.0)
# Contract owner
owner = Variable()
# ID of single game
single_gameID = Variable()
# ID of multiplayer game
multiplayer_gameID = Variable()
# Percentage of profit to help maintain the project
dev_share = Variable()
dev_tau = Variable()
# Array of wallets and their bets
betters = Hash(default_value={})
# Multiplayer game state - it's changed by the owner
game_phase = Variable()
# Deprecate contract
is_deprecated = Variable()
# Factor to store decimal values as int
factor = Variable()
# Max amount in game per user
pool_budget = Variable()
# Seed for generating number
seed_block = Variable()


@construct
def seed():
    owner.set(ctx.caller)
    # Must be changed to the current wallets
    single_gameID.set(1)
    multiplayer_gameID.set(1)
    dev_share.set(0.01)
    game_phase.set("BETTING")
    betters['bets'] = []
    is_deprecated.set(False)
    factor.set(100)
    # Value in TAU
    pool_budget.set(5000)
    seed_block.set(15044)
    dev_tau.set(0)


@export
def single_bet(amount: float, bet: float):
    assert not is_deprecated.get(), "This contract is deprecated"
    assert amount < pool_budget.get(), "The amount exceeds the max amount"
    assert bet >= 0, "Bet cannot be negative and bigger than 0"
    assert amount >= 0, "Amount cannot be negative and bigger than 0"
    assert currency.balance_of(ctx.caller) >= amount, "Betting amount exceeds available balance"
    single_gameID.set(single_gameID.get() + 1)
    currency.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)
    result = generate_result()
    if result >= bet:
        profit = amount * bet
        dev_tau.set(dev_tau.get() + (profit * dev_share.get()))
        currency.transfer(amount=profit * (1 - dev_share.get()), to=ctx.caller)
        return "The Single game #" + str(single_gameID.get()) + " has a result of " + str(
            result) + " and you've won " + str(profit)

    return "The Single game #" + str(single_gameID.get()) + " has a result of " + str(
        result) + " and you've lost"

@export
def not_in_list():
    if len(betters['bets']) == 0:
        return True
    ids = list(map(get_ids, betters['bets']))
    return ctx.caller not in ids


def get_ids(bet):
    return bet['id']


@export
def multi_player_bet(amount: float, bet: float):
    assert not is_deprecated.get(), "The smart contract is deprecated"
    assert bet >= 0.0, "Bet cannot be negative and bigger than 0"
    assert amount >= 0.0, "Amount cannot be negative and bigger than 0"
    assert amount < pool_budget.get(), "The amount exceeds the max amount"
    assert currency.balance_of(ctx.caller) >= amount, "Betting amount exceeds available balance"
    assert game_phase.get() == "BETTING", "The game started, wait for another one"
    assert not_in_list(), "You are already on the betting list"

    currency.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)

    amount = amount * factor.get()
    bet = bet * factor.get()

    betters['bets'].append(
        {'id': ctx.caller, 'amount': int(amount), 'bet': int(bet), 'multiplication_factor': factor.get()})

    # Should I return something for the success?
    return "Thank you for playing, good luck!"


@export
def play_game():
    assert ctx.caller == owner.get(), "Only owner can access this function"
    assert not is_deprecated.get(), "The smart contract is deprecated"
    game_phase.set("PLAYING")
    result = generate_result()
    pay_winners(result)
    start_new_game()
    return str(result)


def pay_winners(result: float):
    for player in betters['bets']:
        if (player['bet'] / player['multiplication_factor']) < result:
            amount = (player['amount'] / player['multiplication_factor'])
            bet = (player['bet'] / player['multiplication_factor'])
            profit = (amount * bet)
            profit = profit * (1 - dev_share.get())
            dev_tau.set(dev_tau.get() + (profit * dev_share.get()))
            currency.transfer(amount=profit, to=ctx.caller)


def start_new_game():
    game_phase.set("BETTING")
    multiplayer_gameID.set(multiplayer_gameID.get() + 1)
    betters['bets'] = []


# Generates a random number
@export
def generate_result():
    rand_value = seed_block.get() * random.randint(1, 10000)
    seed = hashlib.sha256(str(rand_value))
    seed = seed[0:13]
    r = int(seed, 16)
    X = r / pow(1.899, 29)
    X = 99 / (1 - X)
    result = int(X) / 100
    return abs(result) + 1


@export
def add_to_list():
    betters['bets'].append(
        {'id': ctx.caller, 'amount': 0, 'bet': 0, 'multiplication_factor': factor.get()})

    return betters['bets']


@export
def deposit(amount: float):
    assert amount > 0, 'Cannot deposit negative balances!'
    assert ctx.caller == owner.get(), 'Authorization error'
    assert not is_deprecated.get(), "The smart contract is deprecated"
    currency.transfer_from(amount=amount, to=ctx.this, main_account=ctx.caller)


@export
def dev_payout():
    assert ctx.caller == owner.get(), 'Authorization error'

    # Transfer TAU from contract to Lamden dev
    currency.transfer(amount=dev_tau.get(), to=ctx.caller)
    dev_tau.set(0)


@export
def change_dev_share(amount: float):
    assert ctx.caller == owner.get(), "Only owner can access this function"
    dev_share.set(amount)


@export
def change_deprecated_value(value: bool):
    assert ctx.caller == owner.get(), "Only owner can access this function"
    is_deprecated.set(value)


@export
def change_factor_value(value: int):
    assert ctx.caller == owner.get(), "Only owner can access this function"
    factor.set(value)


@export
def change_max_amount(value: int):
    assert ctx.caller == owner.get(), "Only owner can access this function"
    pool_budget.set(value)


@export
def change_seed_block(value: int):
    assert ctx.caller == owner.get(), "Only owner can access this function"
    seed_block.set(value)
