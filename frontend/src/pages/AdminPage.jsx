import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AppBar, Box, Button, Checkbox, Chip, CircularProgress,
  Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, IconButton, Snackbar, Alert,
  Switch, Tab, Tabs, Table, TableBody, TableCell,
  TableHead, TableRow, TextField, Toolbar, Tooltip, Typography,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import {
  createPage, createRole, deletePage, deleteRole,
  listPages, listRoles, listUsers,
  setRolePages, setUserActive, setUserRoles,
} from '../api/admin.api'
import { useAuth } from '../contexts/AuthContext'
import settings from '../settings'

// ── Helpers ────────────────────────────────────────────────────────────────

function useSnack() {
  const [snack, setSnack] = useState(null)
  const show = (msg, severity = 'success') => setSnack({ msg, severity })
  const close = () => setSnack(null)
  const el = snack ? (
    <Snackbar open anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }} autoHideDuration={3000} onClose={close}>
      <Alert severity={snack.severity} onClose={close}>{snack.msg}</Alert>
    </Snackbar>
  ) : null
  return { show, el }
}

// ── Tab: Users ─────────────────────────────────────────────────────────────

function UsersTab({ allRoles, snack }) {
  const [users, setUsers]             = useState([])
  const [loading, setLoading]         = useState(true)
  const [editUser, setEditUser]       = useState(null)   // user being role-edited
  const [selectedRoles, setSelectedRoles] = useState([]) // role ids in dialog

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listUsers()
      setUsers(res.data)
    } catch {
      snack.show('Failed to load users', 'error')
    } finally {
      setLoading(false)
    }
  }, []) // eslint-disable-line

  useEffect(() => { load() }, [load])

  async function handleToggleActive(user) {
    try {
      await setUserActive(user.id, !user.is_active)
      setUsers((prev) => prev.map((u) => u.id === user.id ? { ...u, is_active: !u.is_active } : u))
      snack.show(`User ${user.is_active ? 'deactivated' : 'activated'}`)
    } catch {
      snack.show('Failed to update user', 'error')
    }
  }

  function openRoleEdit(user) {
    setEditUser(user)
    setSelectedRoles(user.roles.map((r) => r.id))
  }

  async function handleSaveRoles() {
    try {
      const res = await setUserRoles(editUser.id, selectedRoles)
      const newRoles = res.data.roles
      setUsers((prev) => prev.map((u) =>
        u.id === editUser.id ? { ...u, roles: newRoles } : u
      ))
      snack.show('Roles updated')
      setEditUser(null)
    } catch {
      snack.show('Failed to update roles', 'error')
    }
  }

  if (loading) return <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>

  return (
    <>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Email</TableCell>
            <TableCell>Name</TableCell>
            <TableCell>Active</TableCell>
            <TableCell>Roles</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map((u) => (
            <TableRow key={u.id} hover>
              <TableCell>{u.email}</TableCell>
              <TableCell>{u.name ?? '—'}</TableCell>
              <TableCell>
                <Switch
                  size="small"
                  checked={u.is_active}
                  onChange={() => handleToggleActive(u)}
                />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {u.roles.length === 0
                    ? <Typography variant="caption" color="text.disabled">No roles</Typography>
                    : u.roles.map((r) => <Chip key={r.id} label={r.name} size="small" />)
                  }
                </Box>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Edit roles">
                  <IconButton size="small" onClick={() => openRoleEdit(u)}><EditIcon fontSize="small" /></IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!editUser} onClose={() => setEditUser(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit roles — {editUser?.email}</DialogTitle>
        <DialogContent>
          {allRoles.map((r) => (
            <FormControlLabel
              key={r.id}
              label={r.name}
              control={
                <Checkbox
                  checked={selectedRoles.includes(r.id)}
                  onChange={(e) => setSelectedRoles((prev) =>
                    e.target.checked ? [...prev, r.id] : prev.filter((id) => id !== r.id)
                  )}
                />
              }
            />
          ))}
          {allRoles.length === 0 && <Typography color="text.secondary">No roles defined yet.</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditUser(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveRoles}>Save</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

// ── Tab: Roles ─────────────────────────────────────────────────────────────

function RolesTab({ allPages, onRolesChange, snack }) {
  const [roles, setRoles]             = useState([])
  const [loading, setLoading]         = useState(true)
  const [newName, setNewName]         = useState('')
  const [newDesc, setNewDesc]         = useState('')
  const [creating, setCreating]       = useState(false)
  const [editRole, setEditRole]       = useState(null)
  const [selectedPages, setSelectedPages] = useState([])
  const [confirmDelete, setConfirmDelete] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listRoles()
      setRoles(res.data)
      onRolesChange(res.data)
    } catch {
      snack.show('Failed to load roles', 'error')
    } finally {
      setLoading(false)
    }
  }, []) // eslint-disable-line

  useEffect(() => { load() }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      const res = await createRole({ name: newName.trim(), description: newDesc.trim() || undefined })
      const updated = [...roles, res.data]
      setRoles(updated)
      onRolesChange(updated)
      setNewName('')
      setNewDesc('')
      snack.show('Role created')
    } catch {
      snack.show('Failed to create role', 'error')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(role) {
    try {
      await deleteRole(role.id)
      const updated = roles.filter((r) => r.id !== role.id)
      setRoles(updated)
      onRolesChange(updated)
      snack.show('Role deleted')
    } catch {
      snack.show('Failed to delete role', 'error')
    } finally {
      setConfirmDelete(null)
    }
  }

  function openPageEdit(role) {
    setEditRole(role)
    setSelectedPages(role.pages.map((p) => p.id))
  }

  async function handleSavePages() {
    try {
      await setRolePages(editRole.id, selectedPages)
      const updatedPages = allPages.filter((p) => selectedPages.includes(p.id))
      setRoles((prev) => prev.map((r) =>
        r.id === editRole.id ? { ...r, pages: updatedPages } : r
      ))
      snack.show('Pages updated')
      setEditRole(null)
    } catch {
      snack.show('Failed to update pages', 'error')
    }
  }

  if (loading) return <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>

  return (
    <>
      <Box component="form" onSubmit={handleCreate} sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'flex-start' }}>
        <TextField
          label="Role name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          size="small"
          sx={{ width: 180 }}
          disabled={creating}
        />
        <TextField
          label="Description (optional)"
          value={newDesc}
          onChange={(e) => setNewDesc(e.target.value)}
          size="small"
          sx={{ width: 240 }}
          disabled={creating}
        />
        <Button type="submit" variant="contained" size="small" disabled={!newName.trim() || creating}>
          {creating ? <CircularProgress size={16} /> : 'Add role'}
        </Button>
      </Box>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Description</TableCell>
            <TableCell>Pages</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {roles.map((r) => (
            <TableRow key={r.id} hover>
              <TableCell sx={{ fontWeight: 600 }}>{r.name}</TableCell>
              <TableCell>{r.description ?? '—'}</TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {r.pages.length === 0
                    ? <Typography variant="caption" color="text.disabled">No pages</Typography>
                    : r.pages.map((p) => <Chip key={p.id} label={p.label} size="small" variant="outlined" />)
                  }
                </Box>
              </TableCell>
              <TableCell align="right">
                <Tooltip title="Edit pages">
                  <IconButton size="small" onClick={() => openPageEdit(r)}><EditIcon fontSize="small" /></IconButton>
                </Tooltip>
                <Tooltip title="Delete role">
                  <IconButton size="small" color="error" onClick={() => setConfirmDelete(r)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Edit pages dialog */}
      <Dialog open={!!editRole} onClose={() => setEditRole(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Edit pages — {editRole?.name}</DialogTitle>
        <DialogContent>
          {allPages.map((p) => (
            <FormControlLabel
              key={p.id}
              label={`${p.label} (${p.slug})`}
              control={
                <Checkbox
                  checked={selectedPages.includes(p.id)}
                  onChange={(e) => setSelectedPages((prev) =>
                    e.target.checked ? [...prev, p.id] : prev.filter((id) => id !== p.id)
                  )}
                />
              }
            />
          ))}
          {allPages.length === 0 && <Typography color="text.secondary">No pages defined yet.</Typography>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditRole(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleSavePages}>Save</Button>
        </DialogActions>
      </Dialog>

      {/* Delete confirmation dialog */}
      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)} maxWidth="xs">
        <DialogTitle>Delete role</DialogTitle>
        <DialogContent>
          <Typography>Delete role <strong>{confirmDelete?.name}</strong>? This will remove it from all users.</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={() => handleDelete(confirmDelete)}>Delete</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

// ── Tab: Pages ─────────────────────────────────────────────────────────────

function PagesTab({ onPagesChange, snack }) {
  const [pages, setPages]         = useState([])
  const [loading, setLoading]     = useState(true)
  const [newSlug, setNewSlug]     = useState('')
  const [newLabel, setNewLabel]   = useState('')
  const [newIcon, setNewIcon]     = useState('')
  const [creating, setCreating]   = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listPages()
      setPages(res.data)
      onPagesChange(res.data)
    } catch {
      snack.show('Failed to load pages', 'error')
    } finally {
      setLoading(false)
    }
  }, []) // eslint-disable-line

  useEffect(() => { load() }, [load])

  async function handleCreate(e) {
    e.preventDefault()
    if (!newSlug.trim() || !newLabel.trim()) return
    setCreating(true)
    try {
      const res = await createPage({ slug: newSlug.trim(), label: newLabel.trim(), icon: newIcon.trim() || undefined })
      const updated = [...pages, res.data]
      setPages(updated)
      onPagesChange(updated)
      setNewSlug('')
      setNewLabel('')
      setNewIcon('')
      snack.show('Page created')
    } catch {
      snack.show('Failed to create page (slug may already exist)', 'error')
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(page) {
    try {
      await deletePage(page.id)
      const updated = pages.filter((p) => p.id !== page.id)
      setPages(updated)
      onPagesChange(updated)
      snack.show('Page deleted')
    } catch {
      snack.show('Failed to delete page', 'error')
    } finally {
      setConfirmDelete(null)
    }
  }

  if (loading) return <Box sx={{ p: 4, display: 'flex', justifyContent: 'center' }}><CircularProgress /></Box>

  return (
    <>
      <Box component="form" onSubmit={handleCreate} sx={{ display: 'flex', gap: 1, mb: 2, alignItems: 'flex-start' }}>
        <TextField
          label="Slug"
          value={newSlug}
          onChange={(e) => setNewSlug(e.target.value)}
          size="small"
          sx={{ width: 160 }}
          disabled={creating}
          placeholder="e.g. analysis"
        />
        <TextField
          label="Label"
          value={newLabel}
          onChange={(e) => setNewLabel(e.target.value)}
          size="small"
          sx={{ width: 160 }}
          disabled={creating}
          placeholder="e.g. Analysis"
        />
        <TextField
          label="Icon (optional)"
          value={newIcon}
          onChange={(e) => setNewIcon(e.target.value)}
          size="small"
          sx={{ width: 180 }}
          disabled={creating}
          placeholder="e.g. analytics"
        />
        <Button type="submit" variant="contained" size="small"
          disabled={!newSlug.trim() || !newLabel.trim() || creating}>
          {creating ? <CircularProgress size={16} /> : 'Add page'}
        </Button>
      </Box>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Slug</TableCell>
            <TableCell>Label</TableCell>
            <TableCell>Icon</TableCell>
            <TableCell />
          </TableRow>
        </TableHead>
        <TableBody>
          {pages.map((p) => (
            <TableRow key={p.id} hover>
              <TableCell><code>{p.slug}</code></TableCell>
              <TableCell>{p.label}</TableCell>
              <TableCell>{p.icon ?? '—'}</TableCell>
              <TableCell align="right">
                <Tooltip title="Delete page">
                  <IconButton size="small" color="error" onClick={() => setConfirmDelete(p)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={!!confirmDelete} onClose={() => setConfirmDelete(null)} maxWidth="xs">
        <DialogTitle>Delete page</DialogTitle>
        <DialogContent>
          <Typography>Delete page <strong>{confirmDelete?.label}</strong> ({confirmDelete?.slug})?
            This will remove it from all roles.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDelete(null)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={() => handleDelete(confirmDelete)}>Delete</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

// ── Main AdminPage ─────────────────────────────────────────────────────────

export default function AdminPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState(0)
  const [allRoles, setAllRoles] = useState([])
  const [allPages, setAllPages] = useState([])
  const snack = useSnack()

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <AppBar position="static" sx={{ bgcolor: '#0f172a', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <Toolbar sx={{ gap: 2 }}>
          <Box sx={{
            width: 28, height: 28, borderRadius: 1,
            bgcolor: 'primary.main',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Typography sx={{ color: '#fff', fontWeight: 900, fontSize: '0.75rem', lineHeight: 1 }}>N</Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1.5, flexGrow: 1 }}>
            <Typography sx={{ fontWeight: 800, letterSpacing: -0.3, color: '#fff', fontSize: '1rem' }}>
              {settings.appName}
            </Typography>
            <Typography sx={{ fontSize: '0.72rem', color: 'rgba(255,255,255,0.35)', fontWeight: 500 }}>
              Admin
            </Typography>
          </Box>
          {user?.pages?.some((p) => p.slug === 'analysis') && (
            <Button size="small" onClick={() => navigate('/')}
              sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: '#fff' } }}>
              Analysis
            </Button>
          )}
          {user?.pages?.some((p) => p.slug === 'pipeline') && (
            <Button size="small" onClick={() => navigate('/pipeline')}
              sx={{ color: 'rgba(255,255,255,0.5)', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: '#fff' } }}>
              Pipeline
            </Button>
          )}
          {user && (
            <Typography sx={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.45)', mr: 1 }}>
              {user.email}
            </Typography>
          )}
          <Button size="small" onClick={logout}
            sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem', textTransform: 'none', '&:hover': { color: '#fff' } }}>
            Sign out
          </Button>
        </Toolbar>
      </AppBar>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Users" />
          <Tab label="Roles" />
          <Tab label="Pages" />
        </Tabs>
      </Box>

      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 3 }}>
        {tab === 0 && <UsersTab allRoles={allRoles} snack={snack} />}
        {tab === 1 && <RolesTab allPages={allPages} onRolesChange={setAllRoles} snack={snack} />}
        {tab === 2 && <PagesTab onPagesChange={setAllPages} snack={snack} />}
      </Box>

      {snack.el}
    </Box>
  )
}
