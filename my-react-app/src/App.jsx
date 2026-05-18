import { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import EnrollUser from './components/EnrollUser'
import UserGallery from './components/UserGallery'
import AccessLogs from './components/AccessLogs'
import './App.css'

const API_BASE = "http://xxx-xxx-xxx-xxx/api"

function App() {
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/logs?page=${currentPage}`)
      const data = await res.json()
      setLogs(data.logs)
      setTotalPages(data.totalPages || 1)
    } catch (e) {
      console.error("Log fetch error", e)
    }
  }, [currentPage])

  const fetchUsers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/users`)
      const data = await res.json()
      setUsers(data)
    } catch (e) {
      console.error("User fetch error", e)
    }
  }, [])

  useEffect(() => {
    fetchUsers()
    fetchLogs()
  }, [fetchUsers, fetchLogs])

  useEffect(() => {
    const interval = setInterval(() => {
      if (currentPage === 1) fetchLogs()
    }, 4000)
    return () => clearInterval(interval)
  }, [currentPage, fetchLogs])

  const handleRemoteUnlock = async () => {
    try {
      await fetch(`${API_BASE}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: "OPEN" })
      })
    } catch (e) {
      console.error("Remote unlock failed", e)
    }
  }

  const handleAddUser = async (name, file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.readAsDataURL(file)
      reader.onload = (e) => {
        const img = new Image()
        img.src = e.target.result
        img.onload = async () => {
          const canvas = document.createElement('canvas')
          const MAX_WIDTH = 600
          const scale = MAX_WIDTH / img.width
          canvas.width = MAX_WIDTH
          canvas.height = img.height * scale

          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
          const compressed = canvas.toDataURL('image/jpeg', 0.7)

          try {
            const response = await fetch(`${API_BASE}/users`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ name, image: compressed })
            })
            if (response.ok) {
              fetchUsers()
              resolve()
            } else {
              reject(new Error("Upload failed"))
            }
          } catch (err) {
            reject(err)
          }
        }
      }
      reader.onerror = () => reject(new Error("File read failed"))
    })
  }

  const handleDeleteUser = async (id) => {
    if (!confirm("Permanently remove this user's access?")) return
    try {
      const res = await fetch(`${API_BASE}/users/${id}`, { method: 'DELETE' })
      if (res.ok) fetchUsers()
    } catch (e) {
      alert("Delete failed")
    }
  }

  const handlePageChange = (step) => {
    setCurrentPage(prev => Math.max(1, prev + step))
  }

  return (
    <div className="container">
      <Header onUnlock={handleRemoteUnlock} />

      <div className="dashboard-grid">
        <EnrollUser onAddUser={handleAddUser} />
        <UserGallery users={users} onDeleteUser={handleDeleteUser} />
      </div>

      <AccessLogs
        logs={logs}
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={handlePageChange}
      />
    </div>
  )
}

export default App
