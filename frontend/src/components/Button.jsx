export default function Button({ children, variant = 'primary', full = false, small = false, ...rest }) {
  const classes = ['btn', `btn--${variant}`]
  if (full) classes.push('btn--full')
  if (small) classes.push('btn--small')

  return (
    <button type="button" className={classes.join(' ')} {...rest}>
      {children}
    </button>
  )
}
