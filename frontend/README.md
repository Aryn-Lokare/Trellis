# Compliance GraphRAG frontend

## Supabase authentication setup

1. Create a Supabase project and copy its Project URL and publishable (or anon) key into a local `.env` file using `.env.example` as the template.
2. Run `backend/schema.sql` in the Supabase SQL editor. It creates the protected `public.profiles` table and a trigger that mirrors a new `auth.users` account's email and display name. Passwords remain managed by Supabase Auth and are never stored in `profiles`.
3. In Supabase Authentication settings, add your local and deployed application URLs to the allowed redirect URLs. Enable email confirmation if you want account verification before the first sign-in.

Workspace routes require a valid Supabase session in the frontend. Configure backend JWT verification separately before exposing the ingestion and query APIs publicly.

## Getting started

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
