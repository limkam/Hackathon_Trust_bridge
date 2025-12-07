/**
 * CV Builder Stepper UI Component
 * Multi-step form for building CVs with AI assistance
 */
import { useState } from "react";
import { User, GraduationCap, Briefcase, Sparkles, Award, Eye } from "lucide-react";

const STEPS = [
  { id: 1, name: "Personal Info", icon: User },
  { id: 2, name: "Education", icon: GraduationCap },
  { id: 3, name: "Work Experience", icon: Briefcase },
  { id: 4, name: "Skills & Languages", icon: Sparkles },
  { id: 5, name: "Awards & Additional", icon: Award },
  { id: 6, name: "Review", icon: Eye },
];

export default function StepperUI({ currentStep, onStepChange, cvData, onUpdate }) {
  return (
    <div className="stepper-container">
      <div className="flex justify-between items-center mb-8">
        {STEPS.map((step, index) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isCompleted = currentStep > step.id;
          
          return (
            <div key={step.id} className="flex items-center flex-1">
              <div
                className={`flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all ${
                  isActive
                    ? "bg-blue-600 border-blue-600 text-white"
                    : isCompleted
                    ? "bg-green-500 border-green-500 text-white"
                    : "bg-gray-100 border-gray-300 text-gray-400"
                }`}
                onClick={() => onStepChange(step.id)}
              >
                <Icon className="w-6 h-6" />
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 ${
                    isCompleted ? "bg-green-500" : "bg-gray-300"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

