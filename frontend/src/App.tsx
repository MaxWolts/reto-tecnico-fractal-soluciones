import { Board } from './components/Board'
import { CreateTicketForm } from './components/CreateTicketForm'
import { Header } from './components/Header'
import { ToastProvider } from './components/ToastProvider'
import { useCurrentUser } from './hooks/useCurrentUser'
import { useTickets } from './hooks/useTickets'
import type { Ticket } from './types'

function noop(ticket: Ticket) {
  // Detail drawer arrives in the next stage.
  void ticket
}

function App() {
  const { user, setRole } = useCurrentUser()
  const { tickets, loading, error, refresh } = useTickets()

  return (
    <ToastProvider>
      <Header userName={user.name} role={user.role} onRoleChange={setRole} />
      <main className="layout">
        <CreateTicketForm currentUser={user.name} onCreated={() => void refresh()} />
        <Board tickets={tickets} loading={loading} error={error} onRetry={() => void refresh()} onTicketClick={noop} />
      </main>
    </ToastProvider>
  )
}

export default App
