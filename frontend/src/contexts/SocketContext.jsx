import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import io from 'socket.io-client'

const SocketContext = createContext(null)

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider')
  }
  return context
}

const playAlertSound = () => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.frequency.value = 880
    gain.gain.value = 0.15
    osc.start()
    osc.stop(ctx.currentTime + 0.2)
  } catch {
    /* ignore if audio blocked */
  }
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)
  const [lastAlert, setLastAlert] = useState(null)

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    const socketUrl = import.meta.env.VITE_SOCKET_URL || ''
    const newSocket = io(socketUrl || undefined, {
      transports: ['websocket', 'polling'],
      autoConnect: false
    })

    newSocket.on('connect', () => {
      setConnected(true)
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
    })

    newSocket.on('alert', (data) => {
      setLastAlert({ ...data, receivedAt: Date.now() })
      playAlertSound()
      if (Notification.permission === 'granted') {
        new Notification('Security Alert', {
          body: data.title || 'New security alert detected',
        })
      }
      window.dispatchEvent(new CustomEvent('compliance:new-alert', { detail: data }))
    })

    newSocket.on('device_detected', (data) => {
      if (Notification.permission === 'granted') {
        new Notification('Device Detected', {
          body: `New device: ${data.hostname || 'Unknown'}`,
        })
      }
    })

    setSocket(newSocket)
    return () => {
      newSocket.disconnect()
    }
  }, [])

  const connect = useCallback(() => {
    if (socket && !socket.connected) {
      socket.connect()
    }
  }, [socket])

  const disconnect = useCallback(() => {
    if (socket) {
      socket.disconnect()
    }
  }, [socket])

  return (
    <SocketContext.Provider value={{ socket, connected, connect, disconnect, lastAlert }}>
      {children}
    </SocketContext.Provider>
  )
}
