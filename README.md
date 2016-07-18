# RTT-Logger

A simple rtt logging utility. The script connects to all avaiable devices through `pynrfjprog`, and prints all output to `stdout`.

The `examples/index.js` file shows how to call a bundled python script from JavaScript.

Bundling the python script to an executable could be done using the `make-exec.sh` script.

    ./make-exec.sh
    # run the executable directly
    bin/rtt-logger-linux
    # .. or though node.js
    node examples/index.js
