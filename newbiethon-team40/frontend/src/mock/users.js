// GET /auth/me 응답 형태
export const LANDLORD = {
  id: 'u1',
  role: 'LANDLORD',
  name: '박서연',
  phone: '010-1111-2222',
  contractId: null, // 임대인은 사용 안 함
}

export const TENANT = {
  id: 'u2',
  role: 'TENANT',
  name: '김민재',
  phone: '010-2345-6789',
  contractId: null, // 초대코드를 입력해야 채워집니다
}

// /invite 화면에서 검증할 데모용 초대코드
export const DEMO_INVITE_CODE = 'A1B2C3D4'
export const DEMO_INVITE_CONTRACT_ID = 'c1'
