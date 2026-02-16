import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import TransactionCard from '@/components/TransactionCard'

// Mock child components to isolate TransactionCard logic
vi.mock('@/components/VendorSelector', () => ({
    default: ({ currentPayee, onSelect }: any) => (
        <div data-testid="vendor-selector">
            <span>{currentPayee}</span>
            <button onClick={() => onSelect('New Vendor')}>Select Vendor</button>
        </div>
    ),
}))

vi.mock('@/components/CategorySelector', () => ({
    default: ({ currentCategory, onSelect }: any) => (
        <div data-testid="category-selector">
            <span>{currentCategory}</span>
            <button onClick={() => onSelect('New Category', 'cat_new')}>Select Category</button>
        </div>
    ),
}))

vi.mock('@/components/SplitEditorModal', () => ({
    default: () => <div data-testid="split-editor-modal" />,
}))

vi.mock('@/components/StreamingText', () => ({
    default: ({ text }: { text: string }) => <span>{text}</span>,
}))

vi.mock('@/lib/native-bridge', () => ({
    triggerHaptic: vi.fn(),
    takePhoto: vi.fn(),
    isNative: vi.fn().mockReturnValue(false),
}))

vi.mock('lucide-react', () => ({
    Check: () => <span data-testid="icon-check" />,
    Edit2: () => <span data-testid="icon-edit" />,
    Info: () => <span data-testid="icon-info" />,
    ArrowUpRight: () => <span data-testid="icon-arrow-up-right" />,
    FilePlus: () => <span data-testid="icon-file-plus" />,
    FileCheck: () => <span data-testid="icon-file-check" />,
    Tags: () => <span data-testid="icon-tags" />,
    Split: () => <span data-testid="icon-split" />,
    ExternalLink: () => <span data-testid="icon-external-link" />,
    CheckCircle2: () => <span data-testid="icon-check-circle" />,
    Sparkles: () => <span data-testid="icon-sparkles" />,
    Building2: () => <span data-testid="icon-building" />,
    X: () => <span data-testid="icon-x" />,
    Camera: () => <span data-testid="icon-camera" />,
}))

const mockTx = {
    id: 'tx_123',
    date: '2024-01-01T12:00:00Z',
    description: 'Test Transaction',
    amount: 50.00,
    currency: 'USD',
    status: 'pending',
    reasoning: 'AI reasoning',
    confidence: 0.95,
    suggested_category_name: 'Office Supplies',
    suggested_category_id: 'cat_1',
    payee: 'Test Vendor',
    account_name: 'Test Account',
    matching_method: 'ai' as const,
}

describe('TransactionCard', () => {
    it('renders transaction details correctly', () => {
        render(
            <TransactionCard
                tx={mockTx}
                onAccept={vi.fn()}
            />
        )

        expect(screen.getAllByText('Test Vendor')[0]).toBeInTheDocument()
        expect(screen.getByText(/\$50.00/)).toBeInTheDocument()
        expect(screen.getByText(/95%/)).toBeInTheDocument()
        expect(screen.getByText(/Jan 1/)).toBeInTheDocument()
    })

    it('calls onAccept when confirm button is clicked', async () => {
        const onAcceptMock = vi.fn()
        render(
            <TransactionCard
                tx={mockTx}
                onAccept={onAcceptMock}
            />
        )

        const confirmButton = screen.getByRole('button', { name: /confirm/i })
        fireEvent.click(confirmButton)

        await waitFor(() => {
            expect(onAcceptMock).toHaveBeenCalledWith('tx_123')
        })
    })

    it('displays duplicate warning when status is potential_duplicate', () => {
        const duplicateTx = {
            ...mockTx,
            status: 'potential_duplicate',
            duplicate_confidence: 0.9,
            potential_duplicate_id: 'tx_dup',
        }

        render(
            <TransactionCard
                tx={duplicateTx}
                onAccept={vi.fn()}
            />
        )

        expect(screen.getByText(/Potential Duplicate Detected/i)).toBeInTheDocument()
        expect(screen.getByText(/90%/)).toBeInTheDocument()
    })

    it('calls onAnalyze when AI Analyze button is clicked', async () => {
        const onAnalyzeMock = vi.fn()
        render(
            <TransactionCard
                tx={mockTx}
                onAccept={vi.fn()}
                onAnalyze={onAnalyzeMock}
            />
        )

        const analyzeButton = screen.getByRole('button', { name: /ai analyze/i })
        fireEvent.click(analyzeButton)

        await waitFor(() => {
            expect(onAnalyzeMock).toHaveBeenCalledWith('tx_123')
        })
    })

    it('handles category change via selector', () => {
        const onCategoryChangeMock = vi.fn()
        render(
            <TransactionCard
                tx={mockTx}
                onAccept={vi.fn()}
                onCategoryChange={onCategoryChangeMock}
            />
        )

        // Simulate opening the modal (mocked above implies interaction)
        // Here we just trigger the mock's select function
        // In the real component, we'd click to open, then select. 
        // Since we mocked CategorySelector to render a button that calls onSelect:

        // First, find the element that triggers the edit mode. 
        // In TransactionCard, clicking the category hub div sets isEditingCategory(true).
        // The CategorySelector is rendered conditionally? No, it's always rendered but controlled by isOpen.
        // However, our mocked CategorySelector is always in the DOM if the parent renders it.
        // Let's verify if TransactionCard renders CategorySelector unconditionally or only when open.
        // Looking at code: It renders <CategorySelector ... isOpen={isEditingCategory} />.
        // So it's always in the DOM, just maybe hidden by CSS or null implementation?
        // Wait, the real CategorySelector likely uses a Portal or conditional rendering inside.
        // But our mock renders a div. Let's see if it's visible.

        // Actually, let's just trust that the mock's onSelect prop is wired to the parent's handler.
        // But we need to define the interaction chain.

        // In TransactionCard:
        // <CategorySelector onSelect={(name, id) => onCategoryChange(...)} />

        // So if we find the mock button and click it:
        const mockSelectButton = screen.getByText('Select Category')
        fireEvent.click(mockSelectButton)

        expect(onCategoryChangeMock).toHaveBeenCalledWith('tx_123', 'cat_new', 'New Category')
    })
})
