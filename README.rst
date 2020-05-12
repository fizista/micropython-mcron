.. role:: bash(code)
   :language: bash

.. role:: python(code)
   :language: python

***************************
MicroCRON for MicroPython
***************************

MicroCRON is a time-based task scheduling program.

The library was designed after the experience with its larger predecessor SimpleCRON. The current library focuses
on minimalism of code while keeping maximum functionality. It takes 3 times less memory than SimpleCRON.
It needs about 3kB of memory to work.

The software was tested under micropython 1.12 (esp32, esp8266).

What you can do with this library:
##################################

* Run any task at precisely defined intervals
* Delete and add tasks while the program is running.
* Run the task a certain number of times and many more.

Library working principle:
##########################

Generally, the working principle is, in a pseudo-code:

.. code-block::

    insert(action_period, action_pointers, 'minute_5s', callback)

    while (the hardware timer is running):
        current_action_period_pointer = current_time % action_period
        if current_action_period_pointer in action_pointers:
            run callback

We have almost complete freedom to choose the action_period as long as it is greater than zero.

The action_pointers variable should contain data of "set" or "range" type.

When we want to use irregular points in time we use "set". Otherwise, you can use "range". This gives us minimal
memory overhead and at the same time a lot of freedom in defining when actions are to start.

Requirements:
#############

* The board on which the micropython is installed(v1.12)
* The board must have support for hardware timers.

Install
#######
You can install using the upip:

.. code-block:: python

    import upip
    upip.install("micropython-mcron")

or

.. code-block:: bash

    micropython -m upip install -p modules micropython-mcron

You can clone this repository, and install it manually:

.. code-block:: bash

    git clone https://github.com/fizista/micropython-mcron.git
    cd ./micropython-mcron

Simple examples
###############

Simple code run every 5 seconds:

.. code-block:: python

    import utime
    import mcron
    import mcron.decorators

    c = 0

    def counter(callback_id, current_time, callback_memory):
        global c
        c += 1
        print('call: %s %s' % (c, utime.localtime()))

    mcron.init_timer()
    mcron.insert(mcron.PERIOD_MINUTE, range(0, mcron.PERIOD_MINUTE, 5), 'minute_5s', counter)

Start the task at exactly 6:30 a.m. and 10:30 p.m. every day.

.. code-block:: python

    mcron.insert(mcron.PERIOD_DAY, {6 * 60 * 60 + 30 * 60, 22 * 60 * 60 + 30 * 60}, 'day_6_30__22_30', callback)

Start the task 4 times a day.

.. code-block:: python

    mcron.insert(mcron.PERIOD_DAY, range(0, mcron.PERIOD_DAY, mcron.PERIOD_DAY // 4), 'day_x4', callback)

Start the task every 11 seconds from now.

.. code-block:: python

    mcron.insert(11, {0}, '11s_now', callback, from_now=True)

Start the task every 11 seconds.

.. code-block:: python

    mcron.insert(11, {0}, '11s', callback)

Start the task successfully three times. Start this task every 5 seconds.

.. code-block:: python

    mcron.insert(
        mcron.PERIOD_MINUTE, range(0, mcron.PERIOD_MINUTE, 5), 'minute_5s_3x_suc',
        mcron.decorators.successfully_run_times(3)(lambda *a, **k: utime.time() % 10 == 0)
    )

Start the task three times. Start this task every 5 seconds.

.. code-block:: python

    mcron.insert(
        mcron.PERIOD_MINUTE, range(0, mcron.PERIOD_MINUTE, 5), 'minute_5s_3x',
        mcron.decorators.run_times(3)(callback)
    )

Remove the action:

.. code-block:: python

    mcron.remove('action_id')

Remove all actions:

.. code-block:: python

    mcron.remove_all()

Capturing action errors is possible by replacing and/or adding your own function.

.. code-block:: python

    def my_exception_processor(e):
        send_exception_to_server(e)
        write_exception_to_disk(e)

    mcron.callback_exception_processors.append(my_exception_processor)

Important notes:
################

* If the execution time of all tasks is longer than (1000ms - 1.5 * _timer_period), then the TLPTimeException exception
  is thrown. This tells you that a task is blocking the device, and probably prevents the execution of the next action
  in the next second. It will be up to the programmer what he will do after intercepting this error. He can do nothing,
  and he can run the missed tasks.
* If there are several functions to run at a given time, then they are started without a specific order.

How to test
###########

Copy the tests.py file from the https://github.com/fizista/micropython-mcron.git repository to your test board
and run the command on this device:

.. code-block:: python

    import tests

*******************
Support and license
*******************

If you have found a mistake or other problem, write in the issues.

If you need a different license for this library (e.g. commercial),
please contact me: fizista+mcron@gmail.com.


