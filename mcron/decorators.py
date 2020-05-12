import mcron

RUN_TIMES_MEM_ID = const(2)


def run_times(times):
    """
    The decorator determines how many times the given callback can be started.

    :param times: number of start-ups
    :return:
    """

    def decorator(callback):
        def wrapper(callback_id, current_time, callback_memory):
            callback_memory[RUN_TIMES_MEM_ID] = callback_memory.setdefault(RUN_TIMES_MEM_ID, 0) + 1
            out = callback(callback_id, current_time, callback_memory)
            if callback_memory[RUN_TIMES_MEM_ID] >= times:
                mcron.remove(callback_id)
            return out

        return wrapper

    return decorator


SUCCESSFULLY_RUN_TIMES_MEM_ID = const(3)


def successfully_run_times(times):
    """
    The decorator determines how many times the given callback can be started.

    Launching a task is considered correct only if the callback returns True.

    :param times: number of start-ups
    :return:
    """
    MEM_ID = '__srt'

    def decorator(callback):
        def wrapper(callback_id, current_time, callback_memory):
            out = callback(callback_id, current_time, callback_memory)
            callback_memory[SUCCESSFULLY_RUN_TIMES_MEM_ID] = \
                callback_memory.setdefault(SUCCESSFULLY_RUN_TIMES_MEM_ID, 0) + int(bool(out))
            if callback_memory[SUCCESSFULLY_RUN_TIMES_MEM_ID] >= times:
                mcron.remove(callback_id)
            return out

        return wrapper

    return decorator


CALL_COUNTER_MEM_ID = const(4)


def call_counter(callback):
    """
    Decorator counts the number of callback calls.

    The number of calls is stored in memory[call_counter.ID].

    :param callback:
    :return:
    """

    def decorator(callback_id, current_time, callback_memory):
        callback_memory[CALL_COUNTER_MEM_ID] = callback_memory.setdefault(CALL_COUNTER_MEM_ID, 0) + 1
        return callback(callback_id, current_time, callback_memory)

    return decorator


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
                callback_memory[CALL_COUNTER_MEM_ID],
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
                callback_memory[CALL_COUNTER_MEM_ID],
                callback_id,
                str(utime.localtime(current_time))
            )
        )
        print()
        return out

    return wrap
