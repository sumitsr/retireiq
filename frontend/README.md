
# RetireIQ - Retirement Planning Assistant

RetireIQ is an interactive retirement planning assistant that uses AI to provide personalized retirement advice. Built with a modern React frontend and styled to match Lloyds Bank's professional aesthetic, RetireIQ offers a user-friendly interface for retirement planning conversations.

## Features

- **Professional Landing Page**: Clean, modern design introducing the retirement chat service
- **Interactive Chat Interface**: Engage with the retirement planning assistant
- **Pre-defined Questions**: Quick access to common retirement planning topics
- **Custom Questions**: Type your own retirement planning queries
- **Configurable LLM Integration**: Choose between different AI providers and models
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Frontend**: React with TypeScript
- **Styling**: Tailwind CSS with custom Lloyds Bank theme
- **UI Components**: shadcn/ui
- **Routing**: React Router
- **State Management**: React Context for chat state
- **API Integration**: Ready for integration with Python backend

## Getting Started

### Prerequisites

- Node.js (v14 or later)
- npm (v6 or later)

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd retireiq
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

4. Open your browser and navigate to `http://localhost:8080`

## Project Structure

```
retireiq/
├── public/
│   └── ...
├── src/
│   ├── components/         # Reusable components
│   │   ├── ui/             # UI components (shadcn)
│   │   ├── chat/           # Chat interface components
│   │   ├── Navbar.tsx      # Navigation bar
│   │   └── Footer.tsx      # Footer component
│   ├── contexts/           # React contexts
│   │   └── ChatContext.tsx # Chat state management
│   ├── hooks/              # Custom React hooks
│   ├── lib/                # Utility functions
│   ├── pages/              # Page components
│   │   ├── Index.tsx       # Landing page
│   │   ├── Chat.tsx        # Chat interface
│   │   ├── Settings.tsx    # LLM configuration page
│   │   └── NotFound.tsx    # 404 page
│   ├── types/              # TypeScript type definitions
│   │   └── chat.ts         # Chat-related types
│   ├── App.tsx             # Main app component with routes
│   ├── index.css           # Global styles
│   └── main.tsx            # App entry point
├── tailwind.config.ts      # Tailwind configuration
├── ...
└── README.md
```

## Customization

### Styling

The application uses Tailwind CSS with a custom theme that matches Lloyds Bank's color palette and design language. You can modify the theme in `tailwind.config.ts` and global styles in `src/index.css`.

### LLM Integration

The chat interface is designed to work with various LLM providers. Configuration can be managed through the Settings page:

1. Navigate to `/settings`
2. Choose your preferred AI provider (OpenAI, Anthropic, or Perplexity)
3. Select a model and enter your API key
4. Adjust the temperature parameter for response creativity

### Adding New Features

To extend the application with new features:

1. **Add new pages**: Create new components in `src/pages/` and add routes in `App.tsx`
2. **Extend chat capabilities**: Modify `ChatContext.tsx` to add new chat features
3. **Add new chat components**: Create components in `src/components/chat/`

## Backend Integration

While the current implementation simulates responses, you can integrate with a real Python backend:

1. Create a Python backend service (e.g., using Flask, FastAPI) with endpoints for:
   - Message processing
   - LLM interaction
   - User profile management

2. Update the `sendMessage` function in `ChatContext.tsx` to call your backend API:

```typescript
const sendMessage = async (content: string) => {
  if (!content.trim()) return;
  
  addMessage(content, 'user');
  setIsProcessing(true);
  
  try {
    const response = await fetch('https://your-backend-api.com/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: content,
        userProfile,
        llmConfig,
      }),
    });
    
    const data = await response.json();
    addMessage(data.response, 'bot');
  } catch (error) {
    console.error('Failed to send message:', error);
    toast.error('Failed to get a response. Please try again.');
  } finally {
    setIsProcessing(false);
  }
};
```

3. Implement authentication and secure API key handling in your backend

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
