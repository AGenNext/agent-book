import { redirect } from 'next/navigation'

interface WorkspaceDetailRedirectProps {
  params: Promise<{ id: string }>
}

export default async function WorkspaceDetailRedirect({ params }: WorkspaceDetailRedirectProps) {
  const { id } = await params
  redirect(`/notebooks/${encodeURIComponent(id)}`)
}
