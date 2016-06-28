# RTT-Logger

A simple rtt logging utility. The script connects to all avaiable devices through `pynrfjprog`, and prints all output to `stdout`.

The `index.js` file is an example script showing how to call a bundled python script from JavaScript.

Bundling the python script to an executable could be done using `pyinstaller`:

    pyintstaller -F rtt-logger.py
    # run the executable directly
    dist/rtt-logger.exe
    # .. or though node.js
    node index.js
