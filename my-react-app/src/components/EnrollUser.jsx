import { useState, useRef } from 'react'

function EnrollUser({ onAddUser }) {
  const [name, setName] = useState('')
  const [processing, setProcessing] = useState(false)
  const fileInputRef = useRef(null)

  const handleSubmit = async () => {
    const file = fileInputRef.current?.files[0]
    if (!name || !file) {
      alert("Please fill name and photo")
      return
    }

    setProcessing(true)
    try {
      await onAddUser(name, file)
      setName('')
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err) {
      alert("Upload failed")
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Enroll New User</h3>
      <input
        type="text"
        placeholder="Enter Full Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <p style={{ fontSize: '12px', color: '#888' }}>
        Select profile photo (Resized automatically)
      </p>
      <input type="file" accept="image/*" ref={fileInputRef} />
      <button
        className="btn btn-add"
        onClick={handleSubmit}
        disabled={processing}
      >
        {processing ? 'Processing...' : 'ADD USER'}
      </button>
    </div>
  )
}

export default EnrollUser
