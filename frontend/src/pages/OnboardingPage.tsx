import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { onboardingService } from '../services/onboardingService';
import Step1FitnessLevel from '../components/onboarding/Step1FitnessLevel';
import Step2Goals from '../components/onboarding/Step2Goals';
import Step3PhysicalConstraints from '../components/onboarding/Step3PhysicalConstraints';
import Step4DietaryPreferences from '../components/onboarding/Step4DietaryPreferences';
import Step5MealPlan from '../components/onboarding/Step5MealPlan';
import Step6MealSchedule from '../components/onboarding/Step6MealSchedule';
import Step7WorkoutSchedule from '../components/onboarding/Step7WorkoutSchedule';
import Step8Hydration from '../components/onboarding/Step8Hydration';
import Step9LifestyleBaseline from '../components/onboarding/Step9LifestyleBaseline';
import Step10Notifications from '../components/onboarding/Step10Notifications';
import Step11Review from '../components/onboarding/Step11Review';
import Step12Confirmation from '../components/onboarding/Step12Confirmation';

export const OnboardingPage = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [stepData, setStepData] = useState<Record<number, Record<string, any>>>({});
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});
  const navigate = useNavigate();

  const totalSteps = 12;

  useEffect(() => {
    // Load progress on mount
    const loadProgress = async () => {
      try {
        const progress = await onboardingService.getProgress();
        if (progress.completed) {
          navigate('/dashboard');
        } else {
          setCurrentStep(progress.currentStep || 1);
        }
      } catch (err) {
        console.error('Failed to load progress:', err);
      }
    };
    loadProgress();
  }, [navigate]);

  const handleNext = async (data: Record<string, any>) => {
    setError(null);
    setValidationErrors({});

    try {
      // Save current step data
      await onboardingService.saveStep(currentStep, data);
      
      // Store data locally
      setStepData((prev) => ({ ...prev, [currentStep]: data }));

      // Move to next step or complete
      if (currentStep < totalSteps) {
        setCurrentStep(currentStep + 1);
      } else {
        // Onboarding complete, redirect to dashboard
        navigate('/dashboard');
      }
    } catch (err: any) {
      // Handle validation errors from backend
      if (err.response?.status === 422 && err.response?.data?.detail) {
        const details = err.response.data.detail;
        if (Array.isArray(details)) {
          // FastAPI validation error format
          const errors: Record<string, string[]> = {};
          details.forEach((error: any) => {
            const field = error.loc?.join('.') || 'general';
            if (!errors[field]) {
              errors[field] = [];
            }
            errors[field].push(error.msg);
          });
          setValidationErrors(errors);
          setError('Please fix the validation errors below');
        } else {
          setError(details.message || 'Validation failed');
        }
      } else {
        setError(err.response?.data?.message || 'Failed to save step');
      }
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setError(null);
      setValidationErrors({});
    }
  };

  const renderStep = () => {
    const commonProps = {
      initialData: stepData[currentStep],
      onNext: handleNext,
      onBack: handleBack,
    };

    switch (currentStep) {
      case 1:
        return <Step1FitnessLevel {...commonProps} />;
      case 2:
        return <Step2Goals {...commonProps} />;
      case 3:
        return <Step3PhysicalConstraints {...commonProps} />;
      case 4:
        return <Step4DietaryPreferences {...commonProps} />;
      case 5:
        return <Step5MealPlan {...commonProps} />;
      case 6:
        return <Step6MealSchedule {...commonProps} />;
      case 7:
        return <Step7WorkoutSchedule {...commonProps} />;
      case 8:
        return <Step8Hydration {...commonProps} />;
      case 9:
        return <Step9LifestyleBaseline {...commonProps} />;
      case 10:
        return <Step10Notifications {...commonProps} />;
      case 11:
        return <Step11Review {...commonProps} allStepData={stepData} />;
      case 12:
        return <Step12Confirmation {...commonProps} />;
      default:
        return <div>Invalid step</div>;
    }
  };

  return (
    <div className="onboarding-page min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4">
        {/* Progress Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Step {currentStep} of {totalSteps}
            </span>
            <span className="text-sm text-gray-500">
              {Math.round((currentStep / totalSteps) * 100)}% Complete
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(currentStep / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm font-semibold">{error}</p>
          </div>
        )}

        {/* Validation Errors */}
        {Object.keys(validationErrors).length > 0 && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm font-semibold mb-2">Validation Errors:</p>
            <ul className="list-disc list-inside space-y-1">
              {Object.entries(validationErrors).map(([field, errors]) => (
                <li key={field} className="text-red-700 text-sm">
                  <span className="font-medium">{field}:</span> {errors.join(', ')}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {renderStep()}
        </div>
      </div>
    </div>
  );
};
