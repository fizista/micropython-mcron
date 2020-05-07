import mcron


def run_times(times):
    """
    The decorator determines how many times the given callback can be started.

    :param times: number of start-ups
    :return:
    """
    RUN_TIMES_ID = '__run_times'

    def decorator(callback):
        def wrapper(callback_id, current_time, callback_memory):
            if RUN_TIMES_ID in callback_memory:
                callback_memory[RUN_TIMES_ID] += 1
            else:
                callback_memory[RUN_TIMES_ID] = 1
            out = callback(callback_id, current_time, callback_memory)
            if callback_memory[RUN_TIMES_ID] >= times:
                mcron.remove(callback_id)
            return out

        return wrapper

    return decorator


def successfully_run_times(times):
    """
    The decorator determines how many times the given callback can be started.

    Launching a task is considered correct only if the callback returns True.

    :param times: number of start-ups
    :return:
    """
    RUN_TIMES_ID = '__s_run_times'

    def decorator(callback):
        def wrapper(callback_id, current_time, callback_memory):
            out = callback(callback_id, current_time, callback_memory)

            if RUN_TIMES_ID not in callback_memory and out == True:
                callback_memory[RUN_TIMES_ID] = 1
            elif RUN_TIMES_ID in callback_memory and out == True:
                callback_memory[RUN_TIMES_ID] += 1
            elif RUN_TIMES_ID not in callback_memory:
                callback_memory[RUN_TIMES_ID] = 0

            if callback_memory[RUN_TIMES_ID] >= times:
                mcron.remove(callback_id)
            return out

        return wrapper

    return decorator


class call_counter:
    """
    Decorator counts the number of callback calls.

    The number of calls is stored in memory[call_counter.ID].

    :param callback:
    :return:
    """
    ID = '__call_counter'

    def __init__(self, callback):
        self.callback = callback

    def __call__(self, callback_id, current_time, callback_memory):
        if self.ID in callback_memory:
            callback_memory[self.ID] += 1
        else:
            callback_memory[self.ID] = 1
        return self.callback(callback_id, current_time, callback_memory)


def debug_call(callback):
    """
    The decorator displays information about the current call

    :param callback:
    :return:
    """

    @call_counter
    def wrap(callback_id, current_time, callback_memory):
        import utime
        print(
            'START call(%3d): %25s,   pointer%18s' % (
                callback_memory[call_counter.ID],
                callback_id,
                str(utime.localtime(current_time))
            )
        )
        mem_before = dict([(k, d) for k, d in callback_memory.items() if not k.startswith('__')])
        print('    Memory before call: %s' % mem_before)
        out = callback(callback_id, current_time, callback_memory)
        mem_after = dict([(k, d) for k, d in callback_memory.items() if not k.startswith('__')])
        print('    Memory after  call: %s' % mem_after)
        print(
            'END   call(%3d): %25s,   pointer%18s' % (
                callback_memory[call_counter.ID],
                callback_id,
                str(utime.localtime(current_time))
            )
        )
        print()
        return out

    return wrap
