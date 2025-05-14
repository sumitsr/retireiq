import React from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ChatHeader from "@/components/chat/ChatHeader";
import ChatContainer from "@/components/chat/ChatContainer";
import ChatInput from "@/components/chat/ChatInput";
import SuggestedQuestions from "@/components/chat/SuggestedQuestions";

const Chat: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 lloyds-container py-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8">
            <div className="bg-white border rounded-lg shadow-sm flex flex-col h-[600px]">
              <ChatHeader />
              <ChatContainer />
              <SuggestedQuestions />
              <ChatInput />
            </div>
          </div>

          <div className="lg:col-span-4">
            <div className="bg-white border rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-lloyds-darkGreen mb-4">
                Retirement Planning Guide
              </h2>

              <div className="space-y-4">
                <div className="border-b pb-4">
                  <h3 className="font-medium text-lloyds-darkBlue mb-2">
                    Understanding Your Needs
                  </h3>
                  <p className="text-sm text-gray-600">
                    Start by understanding what you want from retirement.
                    Travel? Hobbies? Family time? Your goals will help determine
                    how much you need to save.
                  </p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="font-medium text-lloyds-darkBlue mb-2">
                    State Pension
                  </h3>
                  <p className="text-sm text-gray-600">
                    The full new State Pension is £203.85 per week (2023/24).
                    Check if you're eligible and how to increase your
                    entitlement.
                  </p>
                </div>

                <div className="border-b pb-4">
                  <h3 className="font-medium text-lloyds-darkBlue mb-2">
                    Workplace & Private Pensions
                  </h3>
                  <p className="text-sm text-gray-600">
                    These are crucial building blocks for retirement income.
                    Consider consolidating old workplace pensions for easier
                    management.
                  </p>
                </div>

                <div>
                  <h3 className="font-medium text-lloyds-darkBlue mb-2">
                    Other Investments
                  </h3>
                  <p className="text-sm text-gray-600">
                    ISAs, property, and other assets can complement your
                    pension. Ask our RetireIQ assistant about tax-efficient
                    investment strategies.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
};

export default Chat;
