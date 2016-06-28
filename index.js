const spawn = require('child_process').spawn;

// Printing functions
const printData  = data => console.log('[DATA]\t' + data)
const printError = data => console.log('[ERR]\t' + data)
const lines      = data => String(data).split('\n').filter(line => line.length > 0)


// Spawn logger process
const rttLoggerPath = __dirname + '/dist/rtt-logger.exe';
const rttLogger = spawn(rttLoggerPath);

// Data callbacks
rttLogger.stdout.on('data', data => {
    lines(data).map(printData)
});

rttLogger.stderr.on('data', data => {
    lines(data).map(printError)
});


rttLogger.on('close', code => {
    console.log(`rtt_logger exited with code ${code}`);
});


function cleanup() {
    console.log('Exiting rttLogger')
    rttLogger.kill()
}

process.on('SIGINT', cleanup);
