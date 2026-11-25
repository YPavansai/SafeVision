import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Float, Sphere, MeshWobbleMaterial } from '@react-three/drei';
import * as THREE from 'three';

function SafetyHelmet3D() {
  const helmetGroup = useRef();

  useFrame((state) => {
    if (helmetGroup.current) {
      helmetGroup.current.rotation.y = state.clock.getElapsedTime() * 0.4;
      helmetGroup.current.position.y = Math.sin(state.clock.getElapsedTime() * 1.5) * 0.15;
    }
  });

  return (
    <group ref={helmetGroup} scale={1.2}>
      {/* Helmet Main Dome */}
      <mesh position={[0, 0.3, 0]}>
        <sphereGeometry args={[0.9, 32, 32, 0, Math.PI * 2, 0, Math.PI * 0.55]} />
        <meshStandardMaterial color="#f59e0b" roughness={0.2} metalness={0.6} />
      </mesh>

      {/* Helmet Rim / Brim */}
      <mesh position={[0, 0.28, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.85, 1.15, 32]} />
        <meshStandardMaterial color="#d97706" roughness={0.3} metalness={0.5} side={THREE.DoubleSide} />
      </mesh>

      {/* Front Safety Badge / Lamp mount */}
      <mesh position={[0, 0.4, 0.88]}>
        <boxGeometry args={[0.3, 0.2, 0.1]} />
        <meshStandardMaterial color="#38bdf8" roughness={0.1} metalness={0.9} emissive="#0284c7" emissiveIntensity={0.5} />
      </mesh>
    </group>
  );
}

function ConstructionCrane3D() {
  const craneRef = useRef();

  useFrame((state) => {
    if (craneRef.current) {
      craneRef.current.rotation.y = Math.sin(state.clock.getElapsedTime() * 0.3) * 0.3 - 0.5;
    }
  });

  return (
    <group ref={craneRef} position={[-2.8, -1.2, -1.5]} scale={0.7}>
      {/* Tower Mast */}
      <mesh position={[0, 2.5, 0]}>
        <boxGeometry args={[0.3, 5, 0.3]} />
        <meshStandardMaterial color="#475569" wireframe />
      </mesh>
      {/* Horizontal Jib Arm */}
      <mesh position={[1.2, 4.8, 0]}>
        <boxGeometry args={[3.2, 0.25, 0.25]} />
        <meshStandardMaterial color="#f59e0b" />
      </mesh>
      {/* Crane Hook line */}
      <mesh position={[2.2, 3.8, 0]}>
        <cylinderGeometry args={[0.02, 0.02, 2]} />
        <meshStandardMaterial color="#94a3b8" />
      </mesh>
    </group>
  );
}

function ParticleCloud() {
  const particlesRef = useRef();
  const count = 40;
  const positions = React.useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 6;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return pos;
  }, []);

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.getElapsedTime() * 0.05;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.08} color="#06b6d4" transparent opacity={0.6} />
    </points>
  );
}

export default function SafetyScene3D() {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: '260px', position: 'relative' }}>
      <Canvas camera={{ position: [0, 1.2, 4], fov: 45 }}>
        <ambientLight intensity={0.7} />
        <directionalLight position={[5, 8, 5]} intensity={1.2} color="#ffffff" castShadow />
        <pointLight position={[-4, -2, -2]} intensity={0.8} color="#06b6d4" />
        
        <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
          <SafetyHelmet3D />
        </Float>
        
        <ConstructionCrane3D />
        <ParticleCloud />
        
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.8} maxPolarAngle={Math.PI / 2} />
      </Canvas>
    </div>
  );
}
