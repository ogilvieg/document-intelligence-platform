# Document Intelligence Platform - Frontend

Next.js frontend for AI-powered document intelligence and decision support.

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:

```bash
npm install
```

2. Configure environment variables:

```bash
cp .env.local.example .env.local
# Edit .env.local with your API URL
```

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: http://localhost:8000/api/v1)

## Running the Application

Development mode:

```bash
npm run dev
```

The application will be available at http://localhost:3000

Build for production:

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx        # Root layout
│   ├── page.tsx          # Home page (upload & analysis)
│   └── globals.css       # Global styles
├── components/           # React components (to be added)
├── lib/                  # Utilities & API client (to be added)
├── types/                # TypeScript types (to be added)
├── public/               # Static assets
└── package.json
```

## Week 1 Implementation Plan

- [x] Next.js project created
- [x] Tailwind CSS configured
- [x] Basic UI layout designed
- [ ] Document upload component (drag-and-drop)
- [ ] API client for backend communication
- [ ] Analysis results display component
- [ ] Error handling & loading states
- [ ] TypeScript types for API responses

## Features

### Current (Week 1 MVP)

- Clean, modern UI with Tailwind CSS
- Document upload interface (placeholder)
- Analysis trigger button (placeholder)
- Results display area (placeholder)
- Dark mode support

### Planned

- Drag-and-drop file upload
- Multiple document management
- Real-time analysis status
- Structured results with citations
- Source document viewer
- Download results as JSON

## Development

### Type Checking

```bash
npm run build
```

### Linting

```bash
npm run lint
```

## Deployment

This frontend is designed to deploy on Vercel:

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically from main branch

## Next Steps

See `project-context.md` in the root directory for the full implementation roadmap.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
