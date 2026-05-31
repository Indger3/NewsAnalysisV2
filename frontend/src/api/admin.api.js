import { del, get, post, put } from './rest_client'

// Users
export const listUsers    = ()              => get('/v1/admin/users')
export const setUserActive = (id, isActive) => put(`/v1/admin/users/${id}`, { is_active: isActive })
export const setUserRoles = (id, roleIds)   => put(`/v1/admin/users/${id}/roles`, { role_ids: roleIds })

// Roles
export const listRoles    = ()              => get('/v1/admin/roles')
export const createRole   = (body)          => post('/v1/admin/roles', body)
export const deleteRole   = (id)            => del(`/v1/admin/roles/${id}`)
export const setRolePages = (id, pageIds)   => put(`/v1/admin/roles/${id}/pages`, { page_ids: pageIds })

// Pages
export const listPages    = ()              => get('/v1/admin/pages')
export const createPage   = (body)          => post('/v1/admin/pages', body)
export const deletePage   = (id)            => del(`/v1/admin/pages/${id}`)
