import utime
import machine

PERIOD_CENTURY = const(100 * 365 * 24 * 60 * 60)  # Warning: average value
PERIOD_YEAR = const(365 * 24 * 60 * 60)  # Warning: average value
PERIOD_MONTH = const((365 * 24 * 60 * 60) // 12)  # Warning: average value
PERIOD_WEEK = const(7 * 24 * 60 * 60)
PERIOD_DAY = const(24 * 60 * 60)
PERIOD_HOUR = const(60 * 60)
PERIOD_MINUTE = const(60)

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

_last_run_time = None
_timer_period = None  # You have to turn the timer on by: init_timer
_max_time_task_calls = None  # You have to turn the timer on by: init_timer


class TLPTimeException(Exception):
    """
    Too long processing time.
    The maximum time is: 1000 [ms] - 1.5 * period [ms]
    """
    pass


def insert(period, period_steps, callback_id, callback, period_offset=0, from_now=False):
    """

    Examples:
        * Starting once after XX seconds.
            insert(<seconds_from_now>+1, {<seconds_from_now>}, 'callback-id', run_times(1)(<callback>), from_now=True)
        * Running twice a day at 23:59 and 6:00 a.m.
            insert(mcron.PERIOD_DAY, {23 * 59 * 59, 6 * 60 * 60}, 'callback-id', <callback>)

    :param period: A period of time during which the steps are repeated.
    :type  period: int
    :param period_steps: The steps where the callbacks are called. The steps must be integer type.
    :type period_steps: range or set
    :param callback_id:
    :type callback_id: str
    :param callback: callable(callback_id, current_time, callback_memory)
    :type callback: callable
    :param period_offset: The beginning of the period is shifted by the set value.
    :type period_offset: int
    :param from_now: The period will start when the task is added.
    :return:
    """
    global timer_table, memory_table, callback_table, callback_exception_processors

    if callback_id in callback_table:
        raise Exception('Callback ID - exists')

    if type(period) is not int:
        raise TypeError('period is not int')

    if from_now:
        period_offset = -1 * utime.time() % period

    if type(period_offset) is not int:
        raise TypeError('period_offset is not int')

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

    period_info = (period, period_offset)
    if period_info in timer_table:
        period_data = timer_table[period_info]
    else:
        period_data = {}
        timer_table[period_info] = period_data

    if period_steps in period_data:
        callback_ids = period_data[period_steps]
    else:
        callback_ids = set()
        period_data[period_steps] = callback_ids
    callback_ids.add(callback_id)


def remove(callback_id):
    global timer_table, memory_table, callback_table
    to_del_pi = []
    for period_info, period_data in timer_table.items():
        to_del_ps = []
        for period_steps, callback_ids in period_data.items():
            if callback_id in callback_ids:
                callback_ids.remove(callback_id)
            if callback_id in memory_table:
                memory_table.pop(callback_id)
            if len(callback_ids) <= 0:
                to_del_ps.append(period_steps)
        for period_steps in to_del_ps:
            period_data.pop(period_steps)
        del to_del_ps
        if not period_data:
            to_del_pi.append(period_info)
    for period_info in to_del_pi:
        timer_table.pop(period_info)
    del to_del_pi
    if callback_id in callback_table:
        callback_table.pop(callback_id)


def remove_all():
    global callback_table
    for cid in callback_table.keys():
        remove(cid)


def get_actions(current_time):
    global timer_table, memory_table, callback_table, callback_exception_processors
    for period_info, period_data in timer_table.items():
        period, period_offset = period_info
        period_pointer = (current_time + period_offset) % period
        for period_steps, callback_ids in period_data.items():
            if STEP_TYPE_SET == period_steps[0] and period_pointer in period_steps[1:] or \
                                STEP_TYPE_RANGE == period_steps[0] and period_pointer in range(*period_steps[1:]):
                yield from callback_ids


def run_actions(current_time):
    global timer_table, memory_table, callback_table, callback_exception_processors
    for callback_id in get_actions(current_time):
        callback_memory = memory_table.setdefault(callback_id, {})
        action_callback = callback_table[callback_id]

        try:
            action_callback(callback_id, current_time, callback_memory)
        except Exception as e:
            for processor in callback_exception_processors:
                processor(e)


def run_actions_callback(*args, **kwargs):
    global timer_table, memory_table, callback_table, callback_exception_processors, _last_run_time, _timer_period, _max_time_task_calls

    current_time = utime.time()
    if current_time == _last_run_time:
        return
    _last_run_time = current_time
    start = utime.ticks_ms()

    run_actions(current_time)

    stop = utime.ticks_ms()
    processing_time = utime.ticks_diff(stop, start)
    if processing_time > _max_time_task_calls:
        e = TLPTimeException(current_time, processing_time, ' '.join(get_actions(current_time)))
        for processor in callback_exception_processors:
            processor(e)


def init_timer(timer_id=3, timer_period=250):
    """

    :param timer_id:
    :param timer_period: Number of milliseconds between run_actions calls. The recommended value is 250ms. For values greater than 1000ms some action calls may be omitted.
    :type timer_period: int
    :return:
    """
    global timer, _timer_period, _max_time_task_calls, timer
    _timer_period = timer_period
    _max_time_task_calls = 1000 - 1.5 * _timer_period
    timer = machine.Timer(timer_id)
    timer.init(period=_timer_period, mode=machine.Timer.PERIODIC, callback=run_actions_callback)
