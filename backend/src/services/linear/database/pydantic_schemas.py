from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from .schema import ProjectMilestoneStatus


class OrganizationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    aiAddonEnabled: bool
    aiTelemetryEnabled: bool | None = None
    allowMembersToInvite: bool | None = None
    allowedAuthServices: list[str]
    allowedFileUploadContentTypes: list[str]
    archivedAt: datetime | None = None
    createdAt: datetime
    createdIssueCount: int
    customerCount: int
    customersConfiguration: dict[str, Any]
    customersEnabled: bool
    defaultFeedSummarySchedule: str | None = None
    deletionRequestedAt: datetime | None = None
    feedEnabled: bool
    fiscalYearStartMonth: float
    gitBranchFormat: str | None = None
    gitLinkbackMessagesEnabled: bool
    gitPublicLinkbackMessagesEnabled: bool
    hipaaComplianceEnabled: bool
    initiativeUpdateReminderFrequencyInWeeks: float | None = None
    initiativeUpdateRemindersDay: str
    initiativeUpdateRemindersHour: float
    logoUrl: str | None = None
    name: str
    oauthAppReview: bool | None = None
    personalApiKeysEnabled: bool | None = None
    periodUploadVolume: float
    previousUrlKeys: list[str]
    projectUpdateReminderFrequencyInWeeks: float | None = None
    projectUpdateRemindersDay: str
    projectUpdateRemindersHour: float
    projectUpdatesReminderFrequency: str
    reducedPersonalInformation: bool | None = None
    releaseChannel: str
    restrictAgentInvocationToMembers: bool | None = None
    restrictLabelManagementToAdmins: bool | None = None
    restrictTeamCreationToAdmins: bool | None = None
    roadmapEnabled: bool
    samlEnabled: bool
    samlSettings: dict[str, Any] | None = None
    scimEnabled: bool
    scimSettings: dict[str, Any] | None = None
    slaDayCount: str
    slaEnabled: bool | None = None
    themeSettings: dict[str, Any] | None = None
    trialEndsAt: datetime | None = None
    updatedAt: datetime
    urlKey: str
    userCount: int
    workingDays: list[float]


class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    active: bool
    admin: bool
    app: bool
    archivedAt: datetime | None = None
    avatarBackgroundColor: str
    avatarUrl: str | None = None
    calendarHash: str | None = None
    canAccessAnyPublicTeam: bool
    createdAt: datetime
    createdIssueCount: int
    description: str | None = None
    disableReason: str | None = None
    displayName: str
    email: str
    gitHubUserId: str | None = None
    discordUserId: str | None = None
    guest: bool
    initials: str
    inviteHash: str
    isAssignable: bool
    isMe: bool
    isMentionable: bool
    lastSeen: datetime | None = None
    name: str
    organizationId: str
    statusEmoji: str | None = None
    statusLabel: str | None = None
    statusUntilAt: datetime | None = None
    timezone: str | None = None
    updatedAt: datetime
    url: str


class TeamSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    parentId: str | None = None
    activeCycleId: str | None = None
    aiThreadSummariesEnabled: bool
    archivedAt: datetime | None = None
    autoArchivePeriod: float
    autoCloseChildIssues: bool | None = None
    autoCloseParentIssues: bool | None = None
    autoClosePeriod: float | None = None
    autoCloseStateId: str | None = None
    color: str | None = None
    createdAt: datetime
    currentProgress: dict[str, Any]
    cycleCalenderUrl: str
    cycleCooldownTime: float
    cycleDuration: float
    cycleIssueAutoAssignCompleted: bool
    cycleIssueAutoAssignStarted: bool
    cycleLockToActive: bool
    cycleStartDay: float
    cyclesEnabled: bool
    defaultIssueEstimate: float
    defaultIssueStateId: str | None = None
    defaultProjectTemplateId: str | None = None
    defaultTemplateForMembersId: str | None = None
    defaultTemplateForNonMembersId: str | None = None
    description: str | None = None
    displayName: str
    draftWorkflowStateId: str | None = None
    groupIssueHistory: bool
    icon: str | None = None
    inheritIssueEstimation: bool
    inheritWorkflowStatuses: bool
    inheritProductIntelligenceScope: bool | None = None
    productIntelligenceScope: str | None = None
    inviteHash: str
    issueCount: int
    issueEstimationAllowZero: bool
    issueEstimationExtended: bool
    issueEstimationType: str
    issueOrderingNoPriorityFirst: bool
    issueSortOrderDefaultToBottom: bool
    joinByDefault: bool | None = None
    key: str
    markedAsDuplicateWorkflowStateId: str | None = None
    mergeWorkflowStateId: str | None = None
    mergeableWorkflowStateId: str | None = None
    name: str
    organizationId: str
    private: bool
    progressHistory: dict[str, Any]
    requirePriorityToLeaveTriage: bool
    reviewWorkflowStateId: str | None = None
    scimGroupName: str | None = None
    scimManaged: bool
    setIssueSortOrderOnStateChange: str
    slackIssueComments: bool
    slackIssueStatuses: bool
    slackNewIssue: bool
    startWorkflowStateId: str | None = None
    timezone: str
    triageEnabled: bool
    triageIssueStateId: str | None = None
    upcomingCycleCount: float
    updatedAt: datetime


class WorkflowStateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    teamId: str
    archivedAt: datetime | None = None
    color: str
    createdAt: datetime
    description: str | None = None
    inheritedFromId: str | None = None
    name: str
    position: float
    type: str
    updatedAt: datetime


class IssueSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    activitySummary: dict[str, Any] | None = None
    addedToCycleAt: datetime | None = None
    addedToProjectAt: datetime | None = None
    addedToTeamAt: datetime | None = None
    archivedAt: datetime | None = None
    asksExternalUserRequesterId: str | None = None
    asksRequesterId: str | None = None
    assigneeId: str | None = None
    autoArchivedAt: datetime | None = None
    autoClosedAt: datetime | None = None
    autoClosedByParentClosing: bool | None = None
    boardOrder: float
    branchName: str
    canceledAt: datetime | None = None
    parentId: str | None = None
    completedAt: datetime | None = None
    createdAt: datetime
    creatorId: str | None = None
    customerTicketCount: int
    cycleId: str | None = None
    delegateId: str | None = None
    description: str | None = None
    descriptionData: dict[str, Any] | None = None
    descriptionState: str | None = None
    dueDate: date | None = None
    estimate: float | None = None
    externalUserCreatorId: str | None = None
    identifier: str
    integrationSourceType: str | None = None
    labelIds: list[str]
    lastAppliedTemplateId: str | None = None
    number: float
    previousIdentifiers: list[str]
    priority: float
    priorityLabel: str
    prioritySortOrder: float
    projectId: str | None = None
    projectMilestoneId: str | None = None
    reactionData: dict[str, Any]
    slaBreachesAt: datetime | None = None
    slaHighRiskAt: datetime | None = None
    slaMediumRiskAt: datetime | None = None
    slaStartedAt: datetime | None = None
    slaType: str | None = None
    snoozedById: str | None = None
    snoozedUntilAt: datetime | None = None
    sortOrder: float
    sourceCommentId: str | None = None
    startedAt: datetime | None = None
    startedTriageAt: datetime | None = None
    stateId: str
    subIssueSortOrder: float | None = None
    suggestionsGeneratedAt: datetime | None = None
    teamId: str
    title: str
    trashed: bool | None = None
    triagedAt: datetime | None = None
    updatedAt: datetime
    url: str
    uncompletedInCycleUponCloseId: str | None = None
    reminderAt: datetime | None = None


class CommentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    agentSessionId: str | None = None
    archivedAt: datetime | None = None
    body: str
    bodyData: str
    createdAt: datetime
    documentContentId: str | None = None
    documentId: str | None = None
    editedAt: datetime | None = None
    externalUserId: str | None = None
    initiativeUpdateId: str | None = None
    issueId: str | None = None
    parentId: str | None = None
    postId: str | None = None
    projectId: str | None = None
    projectUpdateId: str | None = None
    quotedText: str | None = None
    reactionData: dict[str, Any]
    resolvedAt: datetime | None = None
    resolvingCommentId: str | None = None
    resolvingUserId: str | None = None
    threadSummary: dict[str, Any] | None = None
    updatedAt: datetime
    url: str
    userId: str | None = None


class ProjectSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    archivedAt: datetime | None = None
    autoArchivedAt: datetime | None = None
    canceledAt: datetime | None = None
    color: str
    completedAt: datetime | None = None
    completedIssueCountHistory: list[float]
    completedScopeHistory: list[float]
    content: str | None = None
    contentState: str | None = None
    convertedFromIssueId: str | None = None
    createdAt: datetime
    creatorId: str | None = None
    currentProgress: dict[str, Any]
    description: str
    frequencyResolution: str
    health: str | None = None
    healthUpdatedAt: datetime | None = None
    icon: str | None = None
    inProgressScopeHistory: list[float]
    issueCountHistory: list[float]
    labelIds: list[str]
    lastAppliedTemplateId: str | None = None
    lastUpdateId: str | None = None
    leadId: str | None = None
    name: str
    priority: int
    priorityLabel: str
    prioritySortOrder: float
    progress: float
    progressHistory: dict[str, Any]
    projectUpdateRemindersPausedUntilAt: datetime | None = None
    scope: float
    scopeHistory: list[float]
    slackIssueComments: bool
    slackIssueStatuses: bool
    slackNewIssue: bool
    slugId: str
    sortOrder: float
    startDate: date | None = None
    startDateResolution: str | None = None
    startedAt: datetime | None = None
    state: str
    statusId: str | None = None
    targetDate: date | None = None
    targetDateResolution: str | None = None
    trashed: bool | None = None
    updateReminderFrequency: float | None = None
    updateReminderFrequencyInWeeks: float | None = None
    updateRemindersDay: float | None = None
    updateRemindersHour: float | None = None
    updatedAt: datetime
    url: str


class ProjectMilestoneSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    projectId: str
    archivedAt: datetime | None = None
    createdAt: datetime
    currentProgress: dict[str, Any]
    description: str | None = None
    descriptionData: dict[str, Any] | None = None
    descriptionState: str | None = None
    name: str
    progress: float
    progressHistory: dict[str, Any]
    sortOrder: float
    status: ProjectMilestoneStatus
    targetDate: date | None = None
    updatedAt: datetime


class CycleSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    archivedAt: datetime | None = None
    autoArchivedAt: datetime | None = None
    completedAt: datetime | None = None
    completedIssueCountHistory: list[float]
    completedScopeHistory: list[float]
    createdAt: datetime
    currentProgress: dict[str, Any]
    description: str | None = None
    endsAt: datetime
    inProgressScopeHistory: list[float]
    inheritedFromId: str | None = None
    isActive: bool
    isFuture: bool
    isNext: bool
    isPast: bool
    isPrevious: bool
    issueCountHistory: list[float]
    name: str | None = None
    number: float
    progress: float
    progressHistory: dict[str, Any]
    scopeHistory: list[float]
    startsAt: datetime
    teamId: str
    updatedAt: datetime


class InitiativeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    archivedAt: datetime | None = None
    color: str | None = None
    completedAt: datetime | None = None
    content: str | None = None
    createdAt: datetime
    description: str | None = None
    creatorId: str | None = None
    frequencyResolution: str
    health: str | None = None
    healthUpdatedAt: datetime | None = None
    icon: str | None = None
    lastUpdateId: str | None = None
    name: str
    organizationId: str | None = None
    ownerId: str | None = None
    parentInitiativeId: str | None = None
    slugId: str
    sortOrder: float
    startedAt: datetime | None = None
    status: str
    targetDate: date | None = None
    targetDateResolution: str | None = None
    trashed: bool | None = None
    updateReminderFrequency: float | None = None
    updateReminderFrequencyInWeeks: float | None = None
    updateRemindersDay: float | None = None
    updateRemindersHour: float | None = None
    updatedAt: datetime
    url: str


class DocumentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    projectId: str | None = None
    archivedAt: datetime | None = None
    color: str | None = None
    content: str | None = None
    contentState: str | None = None
    createdAt: datetime
    creatorId: str | None = None
    documentContentId: str | None = None
    hiddenAt: datetime | None = None
    icon: str | None = None
    initiativeId: str | None = None
    lastAppliedTemplateId: str | None = None
    resourceFolderId: str | None = None
    slugId: str
    sortOrder: float
    teamId: str | None = None
    title: str
    trashed: bool | None = None
    updatedAt: datetime
    updatedById: str | None = None
    url: str


class AttachmentSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    issueId: str
    originalIssueId: str | None = None
    archivedAt: datetime | None = None
    bodyData: str | None = None
    createdAt: datetime
    creatorId: str | None = None
    externalUserCreatorId: str | None = None
    groupBySource: bool
    metadata_: dict[str, Any]
    source: dict[str, Any] | None = None
    sourceType: str | None = None
    subtitle: str | None = None
    title: str
    updatedAt: datetime
    url: str
    iconUrl: str | None = None


class IssueLabelSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    teamId: str | None = None
    organizationId: str
    archivedAt: datetime | None = None
    parentId: str | None = None
    color: str
    createdAt: datetime
    creatorId: str | None = None
    description: str | None = None
    inheritedFromId: str | None = None
    isGroup: bool
    lastAppliedAt: datetime | None = None
    name: str
    retiredAt: datetime | None = None
    updatedAt: datetime


class IssueRelationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    archivedAt: datetime | None = None
    createdAt: datetime
    issueId: str
    relatedIssueId: str
    type: str
    issueTitle: str | None = None
    relatedIssueTitle: str | None = None
    updatedAt: datetime
