import utime
import machine
import mcron
from mcron import insert, remove, remove_all, PERIOD_WEEK, PERIOD_DAY, PERIOD_HOUR, PERIOD_MINUTE, \
    run_actions_callback, callback_table, memory_table
from mcron.decorators import run_times, successfully_run_times, call_counter, debug_call


def set_time(year, month, day, hour, minute, second):
    machine.RTC().datetime((year, month, day, 0, hour, minute, second, 0))
    t = utime.time()
    lt = utime.localtime(t)
    print('Current time: %s (%s)' % (str(lt), t))


test_callback_used = False


def test_time(year, month, day, hour, minute, second, callback_used):
    global test_callback_used
    test_callback_used = False
    set_time(year, month, day, hour, minute, second)
    run_actions_callback()
    if callback_used != test_callback_used:
        raise Exception('The callback function %s' % 'must be used' if callback_used else 'cannot be used')


test_title = ''


def test_start(title=''):
    global test_title
    print('START: %s' % title)
    test_title = title


def test_end():
    global test_title
    remove_all()
    print('END: %s' % test_title)
    test_title = ''


def mini_debug(callback_id, current_time, callback_memory):
    global test_callback_used
    print('CB: %10s (%s) %s %s' % (callback_id, current_time, callback_memory, utime.localtime(current_time)))
    test_callback_used = True


def mini_debug_call(f):
    def deco(callback_id, current_time, callback_memory):
        mini_debug(callback_id, current_time, callback_memory)
        return f(callback_id, current_time, callback_memory)

    return deco


mcron.init_timer()
mcron.timer.deinit()

test_start('minute_15s')
insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 15), 'minute_15s', mini_debug)
test_time(2020, 12, 24, 15, 30, 0, True)
test_time(2020, 12, 24, 15, 30, 20, False)
test_time(2020, 12, 24, 15, 30, 30, True)
test_time(2020, 12, 24, 15, 30, 31, False)
test_time(2020, 12, 24, 15, 30, 45, True)
test_end()

test_start('hour_60s')
insert(PERIOD_HOUR, range(0, PERIOD_HOUR, 60), 'hour_60s', mini_debug)
test_time(2020, 12, 24, 15, 30, 0, True)
test_time(2020, 12, 24, 15, 30, 0, False)  # We cannot allow callbacks to be restarted at the same time
for i in range(1, 60):
    test_time(2020, 12, 24, 15, 30, i, False)
test_end()

test_start('minute_5s_3x_suc')
insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'minute_5s_3x_suc',
       successfully_run_times(3)(mini_debug_call(lambda *a, **k: utime.time() % 10 == 0)))
test_time(2020, 12, 24, 15, 30, 21, False)
test_time(2020, 12, 24, 15, 30, 25, True)  # Call return False
test_time(2020, 12, 24, 15, 30, 23, False)
test_time(2020, 12, 24, 15, 30, 30, True)  # Call return True 1
test_time(2020, 12, 24, 15, 30, 35, True)  # Call return False
test_time(2020, 12, 24, 15, 30, 40, True)  # Call return True 2
test_time(2020, 12, 24, 15, 30, 50, True)  # Call return True 3
test_time(2020, 12, 24, 15, 31, 0, False)
test_time(2020, 12, 24, 15, 31, 5, False)
test_time(2020, 12, 24, 15, 31, 10, False)
assert len(callback_table) == 0
test_end()

test_start('minute_5s_3x')
insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'minute_5s_3x',
       run_times(3)(mini_debug_call(lambda *a, **k: utime.time() % 10 == 0)))
test_time(2020, 12, 24, 15, 30, 21, False)
test_time(2020, 12, 24, 15, 30, 25, True)  # Call return False 1
test_time(2020, 12, 24, 15, 30, 23, False)
test_time(2020, 12, 24, 15, 30, 30, True)  # Call return True 2
test_time(2020, 12, 24, 15, 30, 35, True)  # Call return False 3
test_time(2020, 12, 24, 15, 30, 40, False)
test_time(2020, 12, 24, 15, 30, 50, False)
test_time(2020, 12, 24, 15, 31, 0, False)
test_time(2020, 12, 24, 15, 31, 5, False)
test_time(2020, 12, 24, 15, 31, 10, False)
assert len(callback_table) == 0
test_end()

test_start('minute_5s_cc7')
insert(PERIOD_MINUTE, range(0, PERIOD_MINUTE, 5), 'minute_5s_cc7',
       call_counter(mini_debug_call(lambda *a, **k: utime.time() % 10 == 0)))
test_time(2020, 12, 24, 15, 30, 21, False)
test_time(2020, 12, 24, 15, 30, 25, True)  # 1
test_time(2020, 12, 24, 15, 30, 23, False)
test_time(2020, 12, 24, 15, 30, 30, True)  # 2
test_time(2020, 12, 24, 15, 30, 35, True)  # 3
test_time(2020, 12, 24, 15, 30, 40, True)  # 4
test_time(2020, 12, 24, 15, 30, 50, True)  # 5
test_time(2020, 12, 24, 15, 31, 0, True)  # 6
test_time(2020, 12, 24, 15, 31, 5, True)  # 7
test_time(2020, 12, 24, 15, 31, 10, True)  # 8
assert list(memory_table['minute_5s_cc7'].values())[0] == 8
test_end()

# Start the task at exactly 6:30 a.m. and 10:30 p.m. every day.
test_start('day_6_30__22_30')
insert(PERIOD_DAY, {6 * 60 * 60 + 30 * 60, 22 * 60 * 60 + 30 * 60}, 'day_6_30__22_30', mini_debug)
test_time(2020, 12, 24, 5, 30, 21, False)
test_time(2020, 12, 24, 6, 30, 0, True)
test_time(2020, 12, 24, 6, 30, 1, False)
test_time(2020, 12, 24, 22, 30, 0, True)
test_end()

# Start the task 4 times a day
test_start('day_x4')
insert(PERIOD_DAY, range(0, PERIOD_DAY, PERIOD_DAY // 4), 'day_x4', mini_debug)
test_time(2020, 12, 24, 0, 0, 0, True)
test_time(2020, 12, 24, 0, 0, 1, False)
test_time(2020, 12, 24, 6, 0, 0, True)
test_time(2020, 12, 24, 12, 0, 0, True)
test_time(2020, 12, 24, 18, 0, 0, True)
test_end()

# Start the task every 11 seconds from now.
test_start('11s_now')
test_time(2020, 12, 24, 6, 6, 6, False)
insert(11, {0}, '11s_now', mini_debug, from_now=True)
test_time(2020, 12, 24, 6, 6, 6 + 11, True)
test_time(2020, 12, 24, 6, 6, 6 + 11 + 1, False)
test_time(2020, 12, 24, 6, 6, 6 + 11 * 2, True)
test_time(2020, 12, 24, 6, 6, 6 + 11 * 3, True)
test_end()

# Start the task every 11 seconds.
test_start('11s')
test_time(2020, 12, 24, 6, 6, 6, False)
insert(11, {0}, '11s', mini_debug, from_now=False)
test_time(2020, 12, 24, 6, 6, 6 + 11, False)
test_time(2020, 12, 24, 6, 6, 6 + 11 + 1, False)
test_time(2020, 12, 24, 6, 6, 6 + 11 * 2, False)
test_time(2020, 12, 24, 6, 6, 6 + 11 * 3, False)
test_time(2020, 12, 24, 6, 6, 9, True)
test_time(2020, 12, 24, 6, 6, 9 + 11, True)
test_time(2020, 12, 24, 6, 6, 9 + 11 * 2, True)
test_time(2020, 12, 24, 6, 6, 9 + 11 * 3, True)
test_time(2020, 12, 24, 6, 6, 9 + 11 * 4, True)
test_end()
