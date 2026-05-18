function UserGallery({ users, onDeleteUser }) {
  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Authorized Users</h3>
      <div className="user-list">
        {users.map(user => (
          <div key={user._id} className="user-item">
            <img src={user.image} alt={`${user.name} profile`} />
            <p>{user.name}</p>
            <button className="btn-del" onClick={() => onDeleteUser(user._id)}>
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default UserGallery
