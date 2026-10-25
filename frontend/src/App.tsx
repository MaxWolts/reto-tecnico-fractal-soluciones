import { useState } from 'react'
import { Board } from './components/Board'
import { CreateTicketForm } from './components/CreateTicketForm'
import { FiltersBar } from './components/FiltersBar'
import { Header } from './components/Header'
import { TicketDrawer } from './components/TicketDrawer'
import { ToastProvider } from './components/ToastProvider'
import { useCurrentUser } from './hooks/useCurrentUser'
import { useFilters } from './hooks/useFilters'
import { useOperators } from './hooks/useOperators'
import { useTickets } from './hooks/useTickets'

function App() {
  const { user, setRole, setName } = useCurrentUser()
  const { filters, update, clear } = useFilters()
  const { tickets, loading, error, refresh } = useTickets(filters)
  const operators = useOperators()
  const [selectedId, setSelectedId] = useState<number | null>(null)

  return (
    <ToastProvider>
      <Header
        userName={user.name}
        role={user.role}
        onRoleChange={setRole}
        onNameChange={setName}
        onOpenTicket={setSelectedId}
      />
      <main className="layout">
        <CreateTicketForm currentUser={user.name} onCreated={() => void refresh()} />
        <div className="content">
          <FiltersBar filters={filters} operators={operators} onChange={update} onClear={clear} />
          <Board
            tickets={tickets}
            loading={loading}
            error={error}
            statusFilter={filters.status}
            onRetry={() => void refresh()}
            onTicketClick={(t) => setSelectedId(t.id)}
          />
        </div>
      </main>
      {selectedId !== null && (
        <TicketDrawer
          key={selectedId}
          ticketId={selectedId}
          user={user}
          operators={operators}
          onClose={() => setSelectedId(null)}
          onChanged={() => void refresh()}
        />
      )}
    </ToastProvider>
  )
}

export default App
