import { createContext, useContext, useEffect, useState } from 'react'
import io from 'socket.io-client'

const SocketContext = createContext(null)

export const useSocket = () => {
  const context = useContext(SocketContext)
  if (!context) {
    throw new Error('useSocket must be used within SocketProvider')
  }
  return context
}

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const newSocket = io('http://localhost:5000', {
      transports: ['websocket'],
      autoConnect: false
    })

    newSocket.on('connect', () => {
      setConnected(true)
      console.log('WebSocket connected')
    })

    newSocket.on('disconnect', () => {
      setConnected(false)
      console.log('WebSocket disconnected')
    })

    newSocket.on('alert', (data) => {
      console.log('New alert received:', data)
      // Handle real-time alerts
    })

    newSocket.on('device_detected', (data) => {
      console.log('Device detected:', data)
      // Handle real-time device detection
    })

    setSocket(newSocket)

    return () => {
      newSocket.disconnect()
    }
  }, [])

  const connect = () => {
    if (socket) {
      socket.connect()
    }
  }

  const disconnect = () => {
    if (socket) {
      socket.disconnect()
    }
  }

  const value = {
    socket,
    connected,
    connect,
    disconnect
  }

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  )
}
