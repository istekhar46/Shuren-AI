import { useState } from 'react';

interface Step12Props {
  initialData?: Record<string, any>;
  onNext: (data: Record<string, any>) => void;
  onBack: () => void;
}

const Step12Confirmation = ({ onNext, onBack }: Step12Props) => {
  const [confirmed, setConfirmed] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const handleSubmit = () => {
    if (!confirmed) {
      setError('Please confirm that you have reviewed your information');
      return;
    }

    setError('');
    // This step locks the profile and completes onboarding
    onNext({ confirmed: true, lockProfile: true });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Complete Your Profile
        </h2>
        <p className="text-gray-600">
          You're all set! Confirm to lock your profile and start your fitness journey.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
        <div className="text-center space-y-4">
          <div className="text-6xl">🎉</div>
          <h3 className="text-xl font-bold text-gray-900">
            Your Personalized Plan is Ready!
          </h3>
          <p className="text-gray-700">
            Based on your profile, we'll create:
          </p>
          <ul className="text-left max-w-md mx-auto space-y-2 text-gray-700">
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span>Customized workout plan matching your fitness level</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span>Personalized meal plans with your dietary preferences</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span>AI coaching tailored to your goals and schedule</span>
            </li>
            <li className="flex items-start">
              <span className="text-green-600 mr-2">✓</span>
              <span>Smart reminders to keep you on track</span>
            </li>
          </ul>
        </div>
      </div>

      <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h4 className="font-semibold text-gray-900 mb-2">Important:</h4>
        <ul className="text-sm text-gray-700 space-y-1">
          <li>
            • Your profile will be locked after confirmation to maintain plan consistency
          </li>
          <li>
            • You can unlock and edit your profile anytime from the dashboard
          </li>
          <li>
            • Our AI agents will adapt your plans based on your progress
          </li>
        </ul>
      </div>

      {/* Confirmation Checkbox */}
      <div
        onClick={() => setConfirmed(!confirmed)}
        className="flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all hover:border-gray-300"
      >
        <div className="flex items-center h-5">
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        </div>
        <div className="ml-3">
          <label className="font-medium text-gray-900 cursor-pointer">
            I confirm that I have reviewed my information and am ready to start
          </label>
        </div>
      </div>

      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleSubmit}
          disabled={!confirmed}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
        >
          Complete Onboarding
        </button>
      </div>
    </div>
  );
};

export default Step12Confirmation;
