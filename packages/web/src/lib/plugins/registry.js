/**
 * Plugin Registry — manages RecordStoreAdapter instances.
 */
import { validateAdapter } from './RecordStoreAdapter'

const adapters = new Map()

export function registerAdapter(adapter) {
  const { valid, errors } = validateAdapter(adapter)
  if (!valid) {
    throw new Error(`Invalid adapter: ${errors.join(', ')}`)
  }
  if (adapters.has(adapter.id)) {
    console.warn(`Plugin registry: overwriting adapter '${adapter.id}'`)
  }
  adapters.set(adapter.id, adapter)
  return true
}

export function getAdapter(id) {
  return adapters.get(id) || null
}

export function getAllAdapters() {
  return [...adapters.values()]
}

export function removeAdapter(id) {
  return adapters.delete(id)
}

export function hasAdapter(id) {
  return adapters.has(id)
}

export function getAdapterCount() {
  return adapters.size
}

export function clearAdapters() {
  adapters.clear()
}
