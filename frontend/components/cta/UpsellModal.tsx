'use client'

import { Fragment } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { XMarkIcon, SparklesIcon, CheckIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/ui/Button'
import Link from 'next/link'

interface UpsellModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description: string
  features: string[]
  ctaText: string
  ctaLink: string
  currentPlan?: string
  upgradePlan?: string
  price?: string
  highlightFeature?: string
}

export function UpsellModal({
  isOpen,
  onClose,
  title,
  description,
  features,
  ctaText,
  ctaLink,
  currentPlan,
  upgradePlan,
  price,
  highlightFeature,
}: UpsellModalProps) {
  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black bg-opacity-25" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all">
                <div className="absolute right-4 top-4">
                  <button
                    type="button"
                    className="text-gray-400 hover:text-gray-500"
                    onClick={onClose}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>

                <div className="text-center">
                  <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600">
                    <SparklesIcon className="h-8 w-8 text-white" />
                  </div>
                  <Dialog.Title
                    as="h3"
                    className="mt-4 text-2xl font-bold leading-6 text-gray-900"
                  >
                    {title}
                  </Dialog.Title>
                  <div className="mt-2">
                    <p className="text-sm text-gray-500">{description}</p>
                  </div>
                </div>

                {highlightFeature && (
                  <div className="mt-6 rounded-lg bg-gradient-to-r from-blue-50 to-purple-50 p-4 border border-blue-200">
                    <p className="text-sm font-semibold text-gray-900">
                      ✨ {highlightFeature}
                    </p>
                  </div>
                )}

                <div className="mt-6">
                  <ul className="space-y-3">
                    {features.map((feature, index) => (
                      <li key={index} className="flex items-start">
                        <CheckIcon className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {currentPlan && upgradePlan && (
                  <div className="mt-6 rounded-lg bg-gray-50 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-600">Current Plan</p>
                        <p className="text-sm font-semibold text-gray-900">{currentPlan}</p>
                      </div>
                      <div className="text-gray-400">→</div>
                      <div className="text-right">
                        <p className="text-sm text-gray-600">Upgrade to</p>
                        <p className="text-sm font-semibold text-blue-600">{upgradePlan}</p>
                      </div>
                    </div>
                  </div>
                )}

                {price && (
                  <div className="mt-4 text-center">
                    <p className="text-2xl font-bold text-gray-900">{price}</p>
                    <p className="text-sm text-gray-500">per month</p>
                  </div>
                )}

                <div className="mt-6 flex flex-col gap-3">
                  <Link href={ctaLink} className="w-full">
                    <Button className="w-full" size="lg">
                      {ctaText}
                    </Button>
                  </Link>
                  <button
                    type="button"
                    className="text-sm text-gray-500 hover:text-gray-700"
                    onClick={onClose}
                  >
                    Maybe later
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
