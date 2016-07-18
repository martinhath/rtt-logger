const spawn = require('child_process').spawn;
const os = require('os');
const path = require('path')

// Printing functions
const printData  = data => console.log('[DATA]\t' + data)
const printError = data => console.log('[ERR]\t' + data)
const lines      = data => String(data).split('\n').filter(line => line.length > 0)

const platformSuffix = () => {
  switch (os.platform()) {
    case 'darwin':
      return '-osx'
    case 'linux':
      return '-linux'
    case 'win32':
      return '.exe'
  }
}

// Spawn logger process
const rttLoggerPath = path.join(__dirname, '..', 'bin', 'rtt-logger' + platformSuffix());
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
    rttLogger.kill('SIGINT')
}

process.on('SIGINT', cleanup);
