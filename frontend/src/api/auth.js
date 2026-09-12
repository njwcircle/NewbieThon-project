import { api } from './client'

export const signupLandlord = (name, phone, password) =>
  api.post('/auth/signup/landlord', { name, phone, password })

export const signupTenant = (name, phone, password) =>
  api.post('/auth/signup/tenant', { name, phone, password })

export const login = (phone, password) => api.post('/auth/login', { phone, password })

export const getMe = () => api.get('/auth/me')

export const changePassword = (current_password, new_password) =>
  api.patch('/auth/password', { current_password, new_password })

// 임차인이 초대코드로 계약에 연결. 같은 계정으로 여러 번 호출 가능(재계약/이사).
export const redeemInviteCode = (invite_code) => api.post('/auth/redeem-invite-code', { invite_code })

// 임대인은 본인이 등록한 계약, 임차인은 본인이 연결된 계약
export const getMyContracts = () => api.get('/users/me/contracts')
