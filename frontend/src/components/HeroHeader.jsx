// 로그인 · 회원가입 · 계약 등록 · 세대 대시보드에서 쓰는 파란 밴드 + 흰 지붕 헤더.
// 지붕은 이미지 없이 CSS clip-path 삼각형으로 그립니다.
export default function HeroHeader({ title, eyebrow, brand, subtitle }) {
  return (
    <>
      <div className="hero">
        {brand && <div className="hero-brand">{brand}</div>}
        {eyebrow && <p className="hero-eyebrow">{eyebrow}</p>}
        <div className="hero-roofwrap">
          <div className="hero-roof" />
          <h1 className="hero-title">{title}</h1>
        </div>
      </div>
      {subtitle && <p className="hero-sub">{subtitle}</p>}
    </>
  )
}
