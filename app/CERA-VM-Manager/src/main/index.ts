import { electronApp, is, optimizer } from '@electron-toolkit/utils'
import { ChildProcess, spawn } from 'child_process'
import { app, BrowserWindow, ipcMain, shell } from 'electron'
import fs from 'fs'
import net from 'net'
import os from 'os'
import { join } from 'path'
import si from 'systeminformation'
import icon from '../../resources/icon.png?asset'
let backendProcess: ChildProcess | null = null
let assignedPort = 8000
let isStoppingBackend = false
async function findAvailablePort(startPort: number): Promise<number> {
  const isPortAvailable = (port: number): Promise<boolean> => {
    return new Promise((resolve) => {
      const server = net.createServer()
      server.once('error', () => resolve(false))
      server.once('listening', () => {
        server.close()
        resolve(true)
      })
      server.listen(port)
    })
  }
  let port = startPort
  while (!(await isPortAvailable(port))) port++
  return port
}
function getScriptPath(): string {
  if (is.dev) {
    return join(app.getAppPath(), 'scripts', 'main.sh')
  }
  return join(process.resourcesPath, 'scripts', 'main.sh')
}

async function spawnBackend(): Promise<void> {
  assignedPort = await findAvailablePort(8000)
  const scriptPath = getScriptPath()

  if (!fs.existsSync(scriptPath)) {
    console.error(`Backend script not found at: ${scriptPath}`)
    return
  }

  console.log(`Spawning single backend process on port ${assignedPort}`)
  isStoppingBackend = false

  backendProcess = spawn('pkexec', ['bash', scriptPath, '--port', assignedPort.toString()], {
    stdio: ['ignore', 'pipe', 'pipe'],
    detached: false
  })

  backendProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[backend]: ${data.toString().trim()}`)
  })

  backendProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[backend:err]: ${data.toString().trim()}`)
  })

  backendProcess.on('error', (err) => {
    const action = isStoppingBackend ? 'stop' : 'start'
    console.error(`Failed to ${action} backend process: ${err.message}`)
    backendProcess = null
  })

  backendProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`)
    backendProcess = null
  })
}

function killBackend(): void {
  if (backendProcess && !backendProcess.killed) {
    console.log('Stopping backend process...')
    isStoppingBackend = true
    try {
      if (!backendProcess.kill('SIGTERM') && backendProcess.pid) {
        spawn('pkexec', ['kill', '-TERM', backendProcess.pid.toString()])
      }
    } catch (err) {
      if (backendProcess.pid) {
        spawn('pkexec', ['kill', '-TERM', backendProcess.pid.toString()])
      } else {
        console.error(`Failed to stop backend process: ${(err as Error).message}`)
      }
    }
    backendProcess = null
  }
}

function createWindow(port: number): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1440,
    height: 1080,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      additionalArguments: [`--api-port=${port}`]
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Spawn the Single Backend process then create the first window
  spawnBackend().then(() => createWindow(assignedPort))
  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))
  ipcMain.handle('system-info', async () => {
    const cpu = os.cpus().length
    const freeRAM = os.freemem() / 1024 ** 2
    const fs = await si.fsSize()
    const disk = (fs[0].size - fs[0].used) / 1024 ** 2
    return { cpu, ram: freeRAM, disk }
  })
  ipcMain.handle('get-api-config', () => ({ port: assignedPort }))
  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow(assignedPort)
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  killBackend()
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('will-quit', () => {
  killBackend()
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
