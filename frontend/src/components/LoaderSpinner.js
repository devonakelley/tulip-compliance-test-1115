import React from 'react';

const LoaderSpinner = ({ message = 'Loading...', size = 'md' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4'
  };

  const spinnerClass = sizeClasses[size] || sizeClasses.md;

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div className={`${spinnerClass} border-blue-600 border-t-transparent rounded-full animate-spin`}></div>
      {message && (
        <p className="mt-4 text-gray-600 text-sm font-medium">{message}</p>
      )}
    </div>
  );
};

export default LoaderSpinner;
