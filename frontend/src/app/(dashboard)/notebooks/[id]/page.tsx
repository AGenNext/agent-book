'use client'

import { useState, useEffect } from 'react'
import { useParams } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { NotebookHeader } from '../components/NotebookHeader'
import { SourcesColumn } from '../components/SourcesColumn'
import { NotesColumn } from '../components/NotesColumn'
import { ChatColumn } from '../components/ChatColumn'
import {
  ActivityView,
  ArtifactStudioView,
  GovernanceSettingsView,
  MembersView,
  TasksView,
  TimelineView,
  WorkspaceOverview,
} from '../components/WorkspaceModuleViews'
import { useNotebook } from '@/lib/hooks/use-notebooks'
import { useNotebookSources } from '@/lib/hooks/use-sources'
import { useNotes } from '@/lib/hooks/use-notes'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useNotebookColumnsStore } from '@/lib/stores/notebook-columns-store'
import { useIsDesktop } from '@/lib/hooks/use-media-query'
import { useTranslation } from '@/lib/hooks/use-translation'
import { cn } from '@/lib/utils'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, MessageSquare, StickyNote } from 'lucide-react'

export type ContextMode = 'off' | 'insights' | 'full'

export interface ContextSelections {
  sources: Record<string, ContextMode>
  notes: Record<string, ContextMode>
}

type WorkspaceTab = 'overview' | 'chat' | 'sources' | 'notes' | 'artifacts' | 'timeline' | 'tasks' | 'activity' | 'members' | 'settings'

export default function NotebookPage() {
  const { t } = useTranslation()
  const params = useParams()

  const notebookId = params?.id ? decodeURIComponent(params.id as string) : ''

  const { data: notebook, isLoading: notebookLoading } = useNotebook(notebookId)
  const {
    sources,
    isLoading: sourcesLoading,
    refetch: refetchSources,
    hasNextPage,
    isFetchingNextPage,
    fetchNextPage,
  } = useNotebookSources(notebookId)
  const { data: notes, isLoading: notesLoading } = useNotes(notebookId)

  const { sourcesCollapsed, notesCollapsed } = useNotebookColumnsStore()
  const isDesktop = useIsDesktop()
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('overview')
  const [mobileActiveTab, setMobileActiveTab] = useState<'sources' | 'notes' | 'chat'>('chat')

  const [contextSelections, setContextSelections] = useState<ContextSelections>({
    sources: {},
    notes: {}
  })

  useEffect(() => {
    if (sources && sources.length > 0) {
      setContextSelections(prev => {
        const newSourceSelections = { ...prev.sources }
        sources.forEach(source => {
          const currentMode = newSourceSelections[source.id]
          const hasInsights = source.insights_count > 0

          if (currentMode === undefined) {
            newSourceSelections[source.id] = hasInsights ? 'insights' : 'full'
          } else if (currentMode === 'full' && hasInsights) {
            newSourceSelections[source.id] = 'insights'
          }
        })
        return { ...prev, sources: newSourceSelections }
      })
    }
  }, [sources])

  useEffect(() => {
    if (notes && notes.length > 0) {
      setContextSelections(prev => {
        const newNoteSelections = { ...prev.notes }
        notes.forEach(note => {
          if (!(note.id in newNoteSelections)) {
            newNoteSelections[note.id] = 'full'
          }
        })
        return { ...prev, notes: newNoteSelections }
      })
    }
  }, [notes])

  const handleContextModeChange = (itemId: string, mode: ContextMode, type: 'source' | 'note') => {
    setContextSelections(prev => ({
      ...prev,
      [type === 'source' ? 'sources' : 'notes']: {
        ...(type === 'source' ? prev.sources : prev.notes),
        [itemId]: mode
      }
    }))
  }

  if (notebookLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!notebook) {
    return (
      <AppShell>
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-4">{t('notebooks.notFound')}</h1>
          <p className="text-muted-foreground">{t('notebooks.notFoundDesc')}</p>
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex flex-col flex-1 min-h-0">
        <div className="flex-shrink-0 p-6 pb-0">
          <NotebookHeader notebook={notebook} />
        </div>

        <div className="flex-1 p-6 pt-6 overflow-x-auto flex flex-col">
          <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as WorkspaceTab)} className="h-full">
            <TabsList className="mb-5 w-full justify-start overflow-x-auto">
              <TabsTrigger value="overview">{t('workspace.tabs.overview')}</TabsTrigger>
              <TabsTrigger value="chat">{t('workspace.tabs.chat')}</TabsTrigger>
              <TabsTrigger value="sources">{t('workspace.tabs.sources')}</TabsTrigger>
              <TabsTrigger value="notes">{t('workspace.tabs.notes')}</TabsTrigger>
              <TabsTrigger value="artifacts">{t('workspace.tabs.artifacts')}</TabsTrigger>
              <TabsTrigger value="timeline">{t('workspace.tabs.timeline')}</TabsTrigger>
              <TabsTrigger value="tasks">{t('workspace.tabs.tasks')}</TabsTrigger>
              <TabsTrigger value="activity">{t('workspace.tabs.activity')}</TabsTrigger>
              <TabsTrigger value="members">{t('workspace.tabs.members')}</TabsTrigger>
              <TabsTrigger value="settings">{t('workspace.tabs.settings')}</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="overflow-y-auto">
              <WorkspaceOverview workspace={notebook} sources={sources} notes={notes} />
            </TabsContent>

            <TabsContent value="chat" className="h-full min-h-0">
              {!isDesktop && (
                <div className="lg:hidden mb-4">
                  <Tabs value={mobileActiveTab} onValueChange={(value) => setMobileActiveTab(value as 'sources' | 'notes' | 'chat')}>
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="sources" className="gap-2">
                        <FileText className="h-4 w-4" />
                        {t('navigation.sources')}
                      </TabsTrigger>
                      <TabsTrigger value="notes" className="gap-2">
                        <StickyNote className="h-4 w-4" />
                        {t('common.notes')}
                      </TabsTrigger>
                      <TabsTrigger value="chat" className="gap-2">
                        <MessageSquare className="h-4 w-4" />
                        {t('common.chat')}
                      </TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>
              )}

              {!isDesktop && (
                <div className="flex-1 overflow-hidden lg:hidden min-h-[600px]">
                  {mobileActiveTab === 'sources' && (
                    <SourcesColumn
                      sources={sources}
                      isLoading={sourcesLoading}
                      notebookId={notebookId}
                      notebookName={notebook?.name}
                      onRefresh={refetchSources}
                      contextSelections={contextSelections.sources}
                      onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                      hasNextPage={hasNextPage}
                      isFetchingNextPage={isFetchingNextPage}
                      fetchNextPage={fetchNextPage}
                    />
                  )}
                  {mobileActiveTab === 'notes' && (
                    <NotesColumn
                      notes={notes}
                      isLoading={notesLoading}
                      notebookId={notebookId}
                      contextSelections={contextSelections.notes}
                      onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                    />
                  )}
                  {mobileActiveTab === 'chat' && (
                    <ChatColumn
                      notebookId={notebookId}
                      contextSelections={contextSelections}
                      sources={sources}
                      sourcesLoading={sourcesLoading}
                    />
                  )}
                </div>
              )}

              <div className={cn(
                'hidden lg:flex h-full min-h-[640px] gap-6 transition-all duration-150',
                'flex-row'
              )}>
                <div className={cn('transition-all duration-150', sourcesCollapsed ? 'w-12 flex-shrink-0' : 'flex-none basis-1/3')}>
                  <SourcesColumn
                    sources={sources}
                    isLoading={sourcesLoading}
                    notebookId={notebookId}
                    notebookName={notebook?.name}
                    onRefresh={refetchSources}
                    contextSelections={contextSelections.sources}
                    onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                    hasNextPage={hasNextPage}
                    isFetchingNextPage={isFetchingNextPage}
                    fetchNextPage={fetchNextPage}
                  />
                </div>

                <div className={cn('transition-all duration-150', notesCollapsed ? 'w-12 flex-shrink-0' : 'flex-none basis-1/3')}>
                  <NotesColumn
                    notes={notes}
                    isLoading={notesLoading}
                    notebookId={notebookId}
                    contextSelections={contextSelections.notes}
                    onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                  />
                </div>

                <div className="transition-all duration-150 flex-1 min-w-0 lg:pr-6 lg:-mr-6">
                  <ChatColumn
                    notebookId={notebookId}
                    contextSelections={contextSelections}
                    sources={sources}
                    sourcesLoading={sourcesLoading}
                  />
                </div>
              </div>
            </TabsContent>

            <TabsContent value="sources">
              <div className="min-h-[640px]">
                <SourcesColumn
                  sources={sources}
                  isLoading={sourcesLoading}
                  notebookId={notebookId}
                  notebookName={notebook?.name}
                  onRefresh={refetchSources}
                  contextSelections={contextSelections.sources}
                  onContextModeChange={(sourceId, mode) => handleContextModeChange(sourceId, mode, 'source')}
                  hasNextPage={hasNextPage}
                  isFetchingNextPage={isFetchingNextPage}
                  fetchNextPage={fetchNextPage}
                />
              </div>
            </TabsContent>

            <TabsContent value="notes">
              <div className="min-h-[640px]">
                <NotesColumn
                  notes={notes}
                  isLoading={notesLoading}
                  notebookId={notebookId}
                  contextSelections={contextSelections.notes}
                  onContextModeChange={(noteId, mode) => handleContextModeChange(noteId, mode, 'note')}
                />
              </div>
            </TabsContent>
            <TabsContent value="artifacts"><ArtifactStudioView /></TabsContent>
            <TabsContent value="timeline"><TimelineView /></TabsContent>
            <TabsContent value="tasks"><TasksView /></TabsContent>
            <TabsContent value="activity"><ActivityView /></TabsContent>
            <TabsContent value="members"><MembersView /></TabsContent>
            <TabsContent value="settings"><GovernanceSettingsView /></TabsContent>
          </Tabs>
        </div>
      </div>
    </AppShell>
  )
}
