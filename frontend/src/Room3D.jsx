import { Suspense, useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import {
  Bounds,
  ContactShadows,
  Environment,
  Html,
  OrbitControls,
  useGLTF,
} from "@react-three/drei";
import * as THREE from "three";


function BathroomModel({ modelUrl }) {
  const group = useRef();
  const { scene } = useGLTF(modelUrl);

  const clonedScene = useMemo(
    () => scene.clone(true),
    [scene]
  );

  useEffect(() => {
    clonedScene.traverse((object) => {
      if (!object.isMesh) return;

      object.castShadow = true;
      object.receiveShadow = true;

      const materials = Array.isArray(object.material)
        ? object.material
        : [object.material];

      materials.forEach((material) => {
        if (!material) return;

        if (material.map) {
          material.map.colorSpace = THREE.SRGBColorSpace;
        }

        material.needsUpdate = true;
      });
    });
  }, [clonedScene]);

  useFrame((state, delta) => {
    if (!group.current) return;

    // Tiny floating motion only. The user controls the actual view.
    const t = state.clock.getElapsedTime();

    group.current.position.y = THREE.MathUtils.lerp(
      group.current.position.y,
      Math.sin(t * 0.55) * 0.015,
      1 - Math.pow(0.001, delta)
    );
  });

  return (
    <group ref={group}>
      <primitive object={clonedScene} />
    </group>
  );
}


function ModelLoader() {
  return (
    <Html center>
      <div className="true-3d-loader">
        <span>LOADING 3D MODEL</span>
        <i />
      </div>
    </Html>
  );
}


export default function Room3D({
  modelUrl,
  loading = false,
  error = "",
  onGenerate,
}) {
  if (loading) {
    return (
      <div className="room3d-shell true-room3d-shell true-room3d-placeholder">
        <div>
          <span>STABILITY 3D</span>
          <h3>BUILDING THE MODEL...</h3>
          <div className="true-3d-progress"><i /></div>
        </div>
      </div>
    );
  }

  if (!modelUrl) {
    return (
      <div className="room3d-shell true-room3d-shell true-room3d-placeholder">
        <div>
          <span>GENERATED IMAGE → 3D MODEL</span>
          <h3>CREATE AN INTERACTIVE 3D MODEL</h3>
          <p>
            Build a real textured GLB model from the generated bathroom visualization.
          </p>

          {error && (
            <div className="true-3d-error">
              {error}
            </div>
          )}

          <button
            type="button"
            className="true-3d-generate"
            onClick={onGenerate}
          >
            GENERATE 3D MODEL ↗
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="room3d-shell true-room3d-shell">
      <Canvas
        shadows
        dpr={[1, 1.75]}
        camera={{
          position: [4.4, 3.0, 5.5],
          fov: 38,
          near: 0.01,
          far: 1000,
        }}
      >
        <color
          attach="background"
          args={["#ece8e1"]}
        />

        <ambientLight intensity={1.15} />

        <directionalLight
          position={[5, 8, 6]}
          intensity={2.2}
          castShadow
        />

        <Suspense fallback={<ModelLoader />}>
          <Bounds
            fit
            clip
            observe
            margin={1.25}
          >
            <BathroomModel modelUrl={modelUrl} />
          </Bounds>

          <Environment preset="apartment" />

          <ContactShadows
            position={[0, -1.5, 0]}
            opacity={0.28}
            scale={20}
            blur={2.5}
            far={6}
          />
        </Suspense>

        <OrbitControls
          makeDefault
          enablePan
          enableZoom
          enableRotate
          enableDamping
          dampingFactor={0.075}
          minDistance={1}
          maxDistance={30}
        />
      </Canvas>

      <div className="room3d-overlay room3d-overlay-left">
        <span>TRUE GLB MODEL / GENERATED FROM YOUR IMAGE</span>
      </div>

      <div className="room3d-overlay room3d-overlay-right">
        <span>DRAG TO ROTATE</span>
        <i />
        <span>SCROLL TO ZOOM</span>
      </div>
    </div>
  );
}
