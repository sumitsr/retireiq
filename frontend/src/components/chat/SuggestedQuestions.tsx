
import React from 'react';
import { Button } from '@/components/ui/button';
import { usePythonChat } from '@/contexts/PythonChatContext';

const SuggestedQuestions: React.FC = () => {
  const { suggestedQuestions, sendMessage } = usePythonChat();

  return (
    <div className="p-4 border-t border-gray-100">
      <h3 className="text-sm font-medium text-lloyds-darkGray mb-2">Suggested Questions</h3>
      <div className="flex flex-wrap gap-2">
        {suggestedQuestions.map((question) => (
          <Button
            key={question.id}
            variant="outline"
            size="sm"
            onClick={() => sendMessage(question.text)}
            className="text-xs bg-white border border-lloyds-lightBlue text-lloyds-darkBlue hover:bg-lloyds-lightBlue transition-colors"
          >
            {question.text}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default SuggestedQuestions;
