'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { NotebookResponse, NoteResponse, SourceListResponse } from '@/lib/types/api'
import { BellDot, CheckCircle2, FileText, Flag, GitBranch, ShieldCheck, StickyNote, Users } from 'lucide-react'
import { useTranslation } from '@/lib/hooks/use-translation'

interface WorkspaceModuleViewsProps {
  workspace: NotebookResponse
  sources: SourceListResponse[]
  notes: NoteResponse[]
}

const ARTIFACT_TEMPLATES = [
  'Executive brief',
  'Research memo',
  'FAQ',
  'Onboarding summary',
  'Meeting prep',
  'Policy summary',
  'Decision brief',
]

export function WorkspaceOverview({ workspace, sources, notes }: WorkspaceModuleViewsProps) {
  const { t } = useTranslation()

  const stats = [
    { label: t('workspace.summaryCards.sources'), value: sources.length, icon: FileText },
    { label: t('workspace.summaryCards.notes'), value: notes.length, icon: StickyNote },
    { label: t('workspace.summaryCards.groundedCoverage'), value: `${Math.max(0, 85 - Math.min(sources.length, 30))}%`, icon: ShieldCheck },
    { label: t('workspace.summaryCards.openActions'), value: '3', icon: Flag },
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="pb-2">
              <CardDescription>{stat.label}</CardDescription>
              <CardTitle className="text-2xl">{stat.value}</CardTitle>
            </CardHeader>
            <CardContent>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t('workspace.pinnedKnowledge')}</CardTitle>
          <CardDescription>{t('workspace.pinnedKnowledgeDesc')}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="rounded-lg border p-3">{t('workspace.samplePinned.claim1')}</div>
          <div className="rounded-lg border p-3">{t('workspace.samplePinned.claim2')}</div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t('workspace.activityTitle')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>• {t('workspace.activity.sourceAdded').replace('{workspace}', workspace.name)}</p>
          <p>• {t('workspace.activity.noteCaptured')}</p>
          <p>• {t('workspace.activity.answerSaved')}</p>
        </CardContent>
      </Card>
    </div>
  )
}

export function ArtifactStudioView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.artifacts')}</CardTitle>
        <CardDescription>{t('workspace.artifactDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="flex flex-wrap gap-2">
          {ARTIFACT_TEMPLATES.map((template) => (
            <Badge key={template} variant="outline">{template}</Badge>
          ))}
        </div>
        <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          {t('workspace.artifactPlaceholder')}
        </div>
        <Button>{t('workspace.generateArtifact')}</Button>
      </CardContent>
    </Card>
  )
}

export function TimelineView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.timeline')}</CardTitle>
        <CardDescription>{t('workspace.timelineDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        {[t('workspace.activity.sourceAddedGeneric'), t('workspace.activity.noteCaptured'), t('workspace.activity.answerSaved'), t('workspace.activity.taskCreated')].map((event) => (
          <div key={event} className="flex items-start gap-3 rounded-md border p-3">
            <GitBranch className="h-4 w-4 mt-0.5 text-muted-foreground" />
            <p>{event}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function TasksView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.tasks')}</CardTitle>
        <CardDescription>{t('workspace.tasksDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded-md border p-3"><span>{t('workspace.sampleTasks.task1')}</span><Badge>Owner</Badge></div>
        <div className="flex items-center justify-between rounded-md border p-3"><span>{t('workspace.sampleTasks.task2')}</span><Badge variant="secondary">Editor</Badge></div>
      </CardContent>
    </Card>
  )
}

export function ActivityView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.activity')}</CardTitle>
        <CardDescription>{t('workspace.activityDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {[t('workspace.activity.answerSaved'), t('workspace.activity.noteCaptured'), t('workspace.activity.taskCreated')].map((item) => (
          <div key={item} className="flex items-center gap-2 rounded border p-2"><BellDot className="h-4 w-4" />{item}</div>
        ))}
      </CardContent>
    </Card>
  )
}

export function MembersView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.members')}</CardTitle>
        <CardDescription>{t('workspace.membersDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded border p-3"><span className="flex items-center gap-2"><Users className="h-4 w-4" />Workspace Owner</span><Badge>owner</Badge></div>
        <div className="flex items-center justify-between rounded border p-3"><span className="flex items-center gap-2"><Users className="h-4 w-4" />Research Analyst</span><Badge variant="secondary">editor</Badge></div>
        <div className="flex items-center justify-between rounded border p-3"><span className="flex items-center gap-2"><Users className="h-4 w-4" />Compliance Reviewer</span><Badge variant="outline">viewer</Badge></div>
      </CardContent>
    </Card>
  )
}

export function GovernanceSettingsView() {
  const { t } = useTranslation()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('workspace.tabs.settings')}</CardTitle>
        <CardDescription>{t('workspace.settingsDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex items-center justify-between rounded border p-3"><span>{t('workspace.settings.audit')}</span><CheckCircle2 className="h-4 w-4 text-emerald-600" /></div>
        <div className="flex items-center justify-between rounded border p-3"><span>{t('workspace.settings.insufficientEvidence')}</span><CheckCircle2 className="h-4 w-4 text-emerald-600" /></div>
        <div className="flex items-center justify-between rounded border p-3"><span>{t('workspace.settings.citationPolicy')}</span><CheckCircle2 className="h-4 w-4 text-emerald-600" /></div>
      </CardContent>
    </Card>
  )
}
