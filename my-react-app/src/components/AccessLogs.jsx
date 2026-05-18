function AccessLogs({ logs, currentPage, totalPages, onPageChange }) {
  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Access History</h3>
      <table>
        <thead>
          <tr>
            <th>User</th>
            <th>Status</th>
            <th>Method</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log, index) => (
            <tr key={index}>
              <td><strong>{log.user}</strong></td>
              <td className={log.status === 'GRANTED' ? 'status-granted' : 'status-denied'}>
                {log.status === 'GRANTED' ? 'GRANTED' : 'DENIED'}
              </td>
              <td>{log.method}</td>
              <td>{new Date(log.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button className="btn btn-page" onClick={() => onPageChange(-1)}>
          Previous
        </button>
        <span style={{ fontWeight: 'bold' }}>
          Page {currentPage} / {totalPages}
        </span>
        <button className="btn btn-page" onClick={() => onPageChange(1)}>
          Next
        </button>
      </div>
    </div>
  )
}

export default AccessLogs
