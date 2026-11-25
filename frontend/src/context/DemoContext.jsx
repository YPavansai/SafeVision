import React, { createContext, useContext, useState, useEffect } from 'react';

const DemoContext = createContext();

export const DemoProvider = ({ children }) => {
  const [isDemoActive, setIsDemoActive] = useState(false);
  const [demoStep, setDemoStep] = useState(0);

  const demoStepsList = [
    'Initializing AI Pipeline...',
    'Step 1: Worker Detection & Tracking (ByteTrack)',
    'Step 2: Face Recognition & Attendance (ArcFace)',
    'Step 3: Helmet & Safety Vest Inspection (YOLOv8)',
    'Step 4: Safety Violation Alert Triggered',
    'Step 5: Evidence Snapshot Captured & DB Logged',
    'Demo Presentation Cycle Complete'
  ];

  useEffect(() => {
    let interval;
    if (isDemoActive) {
      interval = setInterval(() => {
        setDemoStep((prev) => (prev + 1) % demoStepsList.length);
      }, 3500);
    } else {
      setDemoStep(0);
    }
    return () => clearInterval(interval);
  }, [isDemoActive]);

  const toggleDemo = () => {
    setIsDemoActive((prev) => !prev);
  };

  return (
    <DemoContext.Provider value={{ isDemoActive, toggleDemo, demoStep, currentStepText: demoStepsList[demoStep] }}>
      {children}
    </DemoContext.Provider>
  );
};

export const useDemo = () => useContext(DemoContext);
