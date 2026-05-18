function Header({ onUnlock }) {
  return (
    <header>
      <div>
        <h1 style={{ margin: 0, fontSize: '24px' }}>Security Portal</h1>
      </div>
      <button className="btn btn-unlock" onClick={onUnlock}>
        FORCE OPEN GATE
      </button>
    </header>
  )
}

export default Header
