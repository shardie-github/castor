'use client'

import { useState, useEffect } from 'react'
import { Header } from '@/components/navigation/Header'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { FeatureGate } from '@/components/cta/FeatureGate'
import { UpgradePrompt } from '@/components/cta/UpgradePrompt'
import { UpsellModal } from '@/components/cta/UpsellModal'
import {
  UserGroupIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  ShieldCheckIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline'

export default function TeamPage() {
  const [teamMembers, setTeamMembers] = useState<any[]>([])
  const [hasAccess, setHasAccess] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showUpsellModal, setShowUpsellModal] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')

  useEffect(() => {
    // Check subscription tier
    fetch('/api/v1/users/me')
      .then((res) => res.json())
      .then((data) => {
        setHasAccess(data.subscriptionTier === 'enterprise')
      })
      .catch(() => {})

    // Fetch team members
    fetch('/api/v1/team/members')
      .then((res) => res.json())
      .then((data) => setTeamMembers(data))
      .catch(() => {})
  }, [])

  const handleInvite = () => {
    if (!hasAccess) {
      setShowUpsellModal(true)
      return
    }
    setShowInviteModal(true)
  }

  const handleSendInvite = () => {
    fetch('/api/v1/team/invite', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: inviteEmail }),
    })
      .then(() => {
        setShowInviteModal(false)
        setInviteEmail('')
        // Refresh team members
      })
      .catch(() => {})
  }

  const handleRemoveMember = (memberId: string) => {
    if (!confirm('Are you sure you want to remove this team member?')) return

    fetch(`/api/v1/team/members/${memberId}`, {
      method: 'DELETE',
    })
      .then(() => {
        setTeamMembers(teamMembers.filter((m) => m.member_id !== memberId))
      })
      .catch(() => {})
  }

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Team Management</h1>
            <p className="text-gray-600 mt-2">Manage your team members and their permissions</p>
          </div>

          {!hasAccess && (
            <div className="mb-6">
              <UpgradePrompt
                title="Team Collaboration Requires Enterprise Plan"
                description="Upgrade to Enterprise to add team members, assign roles, and collaborate effectively."
                ctaText="Upgrade to Enterprise"
                ctaLink="/settings/subscription"
                features={[
                  'Unlimited team members',
                  'Role-based permissions',
                  'Team analytics',
                  'Collaboration tools',
                ]}
                variant="banner"
              />
            </div>
          )}

          <FeatureGate
            hasAccess={hasAccess}
            featureName="Team Management"
            requiredPlan="Enterprise"
            upgradeLink="/settings/subscription"
            description="Team management allows you to collaborate with your team and assign different roles and permissions."
          >
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Team Members</h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Invite team members and manage their access to your account.
                  </p>
                </div>
                <Button onClick={handleInvite}>
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Invite Member
                </Button>
              </div>

              {teamMembers.length === 0 ? (
                <div className="text-center py-12">
                  <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">No team members yet</p>
                  <Button onClick={handleInvite}>Invite Your First Team Member</Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {teamMembers.map((member) => (
                    <div
                      key={member.member_id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-4">
                        <div className="h-10 w-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                          <span className="text-white font-semibold">
                            {member.name?.charAt(0).toUpperCase() || 'U'}
                          </span>
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-gray-900">{member.name || 'Unknown'}</span>
                            {member.role === 'admin' && (
                              <ShieldCheckIcon className="h-4 w-4 text-blue-600" />
                            )}
                          </div>
                          <div className="flex items-center space-x-2 text-sm text-gray-600">
                            <EnvelopeIcon className="h-4 w-4" />
                            <span>{member.email}</span>
                            <span className="text-gray-400">•</span>
                            <span className="capitalize">{member.role}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button className="text-gray-400 hover:text-gray-600">
                          <PencilIcon className="h-5 w-5" />
                        </button>
                        {member.role !== 'admin' && (
                          <button
                            onClick={() => handleRemoveMember(member.member_id)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </FeatureGate>
        </div>
      </div>

      {/* Invite Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Invite Team Member</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="colleague@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="mt-6 flex space-x-3">
              <Button onClick={handleSendInvite} className="flex-1">Send Invite</Button>
              <Button variant="secondary" onClick={() => setShowInviteModal(false)} className="flex-1">
                Cancel
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Upsell Modal */}
      <UpsellModal
        isOpen={showUpsellModal}
        onClose={() => setShowUpsellModal(false)}
        title="Upgrade to Enterprise"
        description="Unlock team collaboration features to work together more effectively"
        features={[
          'Unlimited team members',
          'Role-based access control',
          'Team analytics dashboard',
          'Collaboration tools',
          'Dedicated account manager',
          'Custom SLA',
        ]}
        ctaText="Upgrade Now"
        ctaLink="/settings/subscription"
        upgradePlan="Enterprise"
        price="$299/month"
        highlightFeature="Get your first month free when you upgrade today"
      />
    </>
  )
}
