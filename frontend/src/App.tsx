import { useState } from 'react'
import { Board } from './components/Board'
import { CreateTicketForm } from './components/CreateTicketForm'
import { Header } from './components/Header'
import { TicketDrawer } from './components/TicketDrawer'
import { ToastProvider } from './components/ToastProvider'
import { useCurrentUser } from './hooks/useCurrentUser'
import { useTickets } from './hooks/useTickets'

function App() {
  const { user, setRole, setName } = useCurrentUser()
  const { tickets, loading, error, refresh } = useTickets()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  return (
    <ToastProvider>
      <Header userName={user.name} role={user.role} onRoleChange={setRole} onNameChange={setName} />
      <main className="layout">
        <CreateTicketForm currentUser={user.name} onCreated={() => void refresh()} />
        <Board
          tickets={tickets}
          loading={loading}
          error={error}
          onRetry={() => void refresh()}
          onTicketClick={(t) => setSelectedId(t.id)}
        />
      </main>
      {selectedId !== null && (
        <TicketDrawer
          key={selectedId}
          ticketId={selectedId}
          user={user}
          onClose={() => setSelectedId(null)}
          onChanged={() => void refresh()}
        />
      )}
    </ToastProvider>
  )
}

export default App
