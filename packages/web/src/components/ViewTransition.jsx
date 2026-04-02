import useStore from '../stores/useStore'

const VIEW_MODES = ['genre', 'earth', 'planet']

export default function ViewTransition({ children }) {
  const viewMode = useStore(s => s.viewMode)

  return (
    <>
      {VIEW_MODES.map((mode, i) => (
        <div
          key={mode}
          className={`view-container ${viewMode === mode ? 'active' : 'inactive'}`}
          style={{ zIndex: viewMode === mode ? 1 : 0 }}
        >
          {children[i]}
        </div>
      ))}
    </>
  )
}
