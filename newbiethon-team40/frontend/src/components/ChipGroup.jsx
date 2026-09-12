// 문제 카테고리 선택(grid)과 접수 내역 필터탭(pill) 둘 다 이 컴포넌트를 씁니다.
// options: [{ value, label }]
export default function ChipGroup({ options, value, onChange, variant = 'grid' }) {
  return (
    <div className={`chipgroup chipgroup--${variant}`}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className={`chipgroup-item${opt.value === value ? ' chipgroup-item--on' : ''}`}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}
