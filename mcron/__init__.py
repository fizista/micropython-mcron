import utime
import machine

PERIOD_CENTURY = 100 * 365 * 24 * 60 * 60
PERIOD_YEAR = 365 * 24 * 60 * 60
PERIOD_MONTH = int(PERIOD_YEAR / 12)
PERIOD_WEEK = 7 * 24 * 60 * 60
PERIOD_DAY = 24 * 60 * 60
PERIOD_HOUR = 60 * 60
PERIOD_MINUTE = 60

# {
#   <period: int>: {
#       period_steps: [<callback_id>, <callback_id>, ...]
#   }
# }
timer_table = {}

# {
#   <callback_id>: {}
# }
memory_table = {}

# {
#   <callback_id>: <callback>
# }
callback_table = {}

# machine.Timer instance
timer = None

# A list of functions that process the captured exception, received from the running callback.
# processor_exception_function(exception_instance)
callback_exception_processors = [lambda e: print('Callback EXCEPTION: %s' % e)]

STEP_TYPE_RANGE = const(1)
STEP_TYPE_SET = const(2)


def insert(period, period_steps, callback_id, callback):
    """

    Examples:
        * Starting once after XX seconds.
        mcron.insert(<seconds_from_now> + 1, {<seconds_from_now>}, 'callback-id', successfully_run_times(1)(<callback>))
        * Running twice a day at 23:59 and 6:00 a.m.
        mcron.insert(mcron.PERIOD_DAY, {23 * 59 * 59, 6 * 60 * 60}, 'callback-id', <callback>)
        * Once every 15 seconds
        mcron.insert(mcron.PERIOD_MINUTE, range(0, mcron.PERIOD_MINUTE, 15), 'callback-id', <callback>)

    :param period: A period of time during which the steps are repeated.
    :type  period: int
    :param period_steps: The steps where the callbacks are called. The steps must be integer type.
    :type period_steps: range or set
    :param callback_id:
    :type callback_id: str
    :param callback: callable(callback_id, current_time, callback_memory)
    :type callback: callable
    :return:
    """
    global timer_table, callback_table

    if callback_id in callback_table:
        raise Exception('Callback ID - exists')

    if type(period) is not int:
        raise TypeError('period is not int')

    if type(period_steps).__name__ == 'range':
        period_steps = (STEP_TYPE_RANGE,) + (period_steps.start, period_steps.stop, period_steps.step)
    elif type(period_steps).__name__ == 'set':
        period_steps = (STEP_TYPE_SET,) + tuple(period_steps)
    else:
        raise Exception('period_steps wrong type')

    for s in period_steps[1:]:
        if type(s) is not int:
            raise TypeError('period step is not int %s' % str(period_steps))

    callback_table[callback_id] = callback

    if period in timer_table:
        period_data = timer_table[period]
    else:
        period_data = {}
        timer_table[period] = period_data

    if period_steps in period_data:
        callback_ids = period_data[period_steps]
    else:
        callback_ids = set()
        period_data[period_steps] = callback_ids
    callback_ids.add(callback_id)


def remove(callback_id):
    for period, period_data in timer_table.items():
        for period_steps, callback_ids in period_data.items():
            if callback_id in callback_ids:
                callback_ids.remove(callback_id)
            if len(callback_ids) <= 0:
                period_data.pop(period_steps)
        if not period_data:
            timer_table.pop(period)
    if callback_id in callback_table:
        callback_table.pop(callback_id)


def run_actions(*args, **kwargs):
    global timer_table, memory_table, callback_table, callback_exception_processors
    current_time = utime.time()
    for period, period_data in timer_table.items():
        period_pointer = current_time % period
        for period_steps, callback_ids in period_data.items():
            if STEP_TYPE_SET == period_steps[0] and period_pointer in period_steps[1:] or \
                    STEP_TYPE_RANGE == period_steps[0] and period_pointer in range(*period_steps[1:]):
                for callback_id in callback_ids:
                    if callback_id in memory_table:
                        callback_memory = memory_table[callback_id]
                    else:
                        callback_memory = {}
                        memory_table[callback_id] = callback_memory
                    action_callback = callback_table[callback_id]

                    try:
                        action_callback(callback_id, current_time, callback_memory)
                    except Exception as e:
                        for processor in callback_exception_processors:
                            processor(e)


def init_timer(timer_id=3):
    global timer
    timer = machine.Timer(timer_id)
    timer.init(period=1000, mode=machine.Timer.PERIODIC, callback=run_actions)


# def dd(*a, **k):
#     print(a, k)
#
#
# def ddodd(*a, **k):
#     print(a, k)
#     return bool(a[1] % 2)
#
#
# def test_a():
#     insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 15), 'min_15s', dd)
#     insert(PERIOD_HOUR, range(0, PERIOD_HOUR, 60), 'h_1m', dd)
#
#
# def test_b():
#     from mcron import decorators
#     insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'd_run_times', decorators.run_times(3)(dd))
#     insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'd_successfully_run_times', decorators.successfully_run_times(3)(ddodd))
#     insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'd_call_counter', decorators.call_counter(dd))
#
# mcron.init_timer()