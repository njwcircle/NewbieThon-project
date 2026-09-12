export default function Card({ children, bordered = false, className = '', ...rest }) {
  const classes = ['card']
  if (bordered) classes.push('card--bordered')
  if (className) classes.push(className)

  return (
    <div className={classes.join(' ')} {...rest}>
      {children}
    </div>
  )
}
