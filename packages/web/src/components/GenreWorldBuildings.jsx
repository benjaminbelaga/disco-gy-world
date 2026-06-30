import { useRef, useMemo, useEffect } from 'react'
import * as THREE from 'three'
import { generateGenreBuildings } from '../lib/buildingGenerator'

const MAX_BOXES = 2000
const MAX_CYLINDERS = 500
const MAX_CONES = 500

const _obj = new THREE.Object3D()
const _color = new THREE.Color()

// Shared geometries (created once)
const _box = new THREE.BoxGeometry(1, 1, 1)
const _cylinder = new THREE.CylinderGeometry(0.5, 0.5, 1, 8)
const _cone = new THREE.ConeGeometry(0.5, 1, 8)

export default function GenreWorldBuildings({ genres }) {
  const boxRef = useRef()
  const cylRef = useRef()
  const coneRef = useRef()

  // Generate all buildings from all genres
  const { boxes, cylinders, cones } = useMemo(() => {
    const b = []
    const cy = []
    const co = []

    for (const genre of genres) {
      // Deterministic seed from slug
      let seed = 0
      for (let i = 0; i < (genre.slug || '').length; i++) {
        seed = ((seed << 5) - seed + genre.slug.charCodeAt(i)) | 0
      }

      const buildings = generateGenreBuildings(genre, seed)
      for (const bldg of buildings) {
        if (bldg.geometry === 'box' && b.length < MAX_BOXES) b.push(bldg)
        else if (bldg.geometry === 'cylinder' && cy.length < MAX_CYLINDERS) cy.push(bldg)
        else if (bldg.geometry === 'cone' && co.length < MAX_CONES) co.push(bldg)
      }
    }

    return { boxes: b, cylinders: cy, cones: co }
  }, [genres])

  // Update instance matrices and colors
  useEffect(() => {
    const updateMesh = (ref, items) => {
      if (!ref.current || items.length === 0) return

      for (let i = 0; i < items.length; i++) {
        const item = items[i]
        _obj.position.set(item.position[0], item.position[1], item.position[2])
        _obj.rotation.set(item.rotation[0], item.rotation[1], item.rotation[2])
        _obj.scale.set(item.scale[0], item.scale[1], item.scale[2])
        _obj.updateMatrix()
        ref.current.setMatrixAt(i, _obj.matrix)

        _color.set(item.emissiveColor || '#111122')
        ref.current.setColorAt(i, _color)
      }

      ref.current.count = items.length
      ref.current.instanceMatrix.needsUpdate = true

      // Per-instance colour via mesh.instanceColor (setColorAt allocates it);
      // a geometry attribute named "instanceColor" is inert and renders flat.
      if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true
    }

    updateMesh(boxRef, boxes)
    updateMesh(cylRef, cylinders)
    updateMesh(coneRef, cones)
  }, [boxes, cylinders, cones])

  return (
    <group>
      {/* Box buildings */}
      {boxes.length > 0 && (
        <instancedMesh ref={boxRef} args={[_box, undefined, boxes.length]} raycast={() => null}>
          <meshLambertMaterial
            color="#ffffff"
            emissive="#000000"
            emissiveIntensity={0.4}
          />
        </instancedMesh>
      )}

      {/* Cylinder buildings */}
      {cylinders.length > 0 && (
        <instancedMesh ref={cylRef} args={[_cylinder, undefined, cylinders.length]} raycast={() => null}>
          <meshLambertMaterial
            color="#ffffff"
            emissive="#000000"
            emissiveIntensity={0.4}
          />
        </instancedMesh>
      )}

      {/* Cone buildings */}
      {cones.length > 0 && (
        <instancedMesh ref={coneRef} args={[_cone, undefined, cones.length]} raycast={() => null}>
          <meshLambertMaterial
            color="#ffffff"
            emissive="#000000"
            emissiveIntensity={0.4}
          />
        </instancedMesh>
      )}
    </group>
  )
}
