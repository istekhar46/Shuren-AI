import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoadingSpinner } from '../../src/components/common/LoadingSpinner';
import { ErrorMessage } from '../../src/components/common/ErrorMessage';
import { ConfirmDialog } from '../../src/components/common/ConfirmDialog';

describe('Common Components Unit Tests', () => {
  describe('LoadingSpinner', () => {
    it('should render spinner with default size', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toBeInTheDocument();
      expect(spinner).toHaveAttribute('aria-label', 'Loading');
    });

    it('should render spinner with message', () => {
      render(<LoadingSpinner message="Loading data..." />);

      expect(screen.getByText('Loading data...')).toBeInTheDocument();
    });

    it('should render small size spinner', () => {
      render(<LoadingSpinner size="sm" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('w-6', 'h-6', 'border-2');
    });

    it('should render medium size spinner', () => {
      render(<LoadingSpinner size="md" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('w-12', 'h-12', 'border-4');
    });

    it('should render large size spinner', () => {
      render(<LoadingSpinner size="lg" />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('w-16', 'h-16', 'border-4');
    });

    it('should apply custom className', () => {
      const { container } = render(<LoadingSpinner className="my-custom-class" />);

      const wrapper = container.firstChild as HTMLElement;
      expect(wrapper).toHaveClass('my-custom-class');
    });

    it('should have spinning animation', () => {
      render(<LoadingSpinner />);

      const spinner = screen.getByRole('status');
      expect(spinner).toHaveClass('animate-spin');
    });

    it('should not render message when not provided', () => {
      const { container } = render(<LoadingSpinner />);

      const paragraph = container.querySelector('p');
      expect(paragraph).not.toBeInTheDocument();
    });
  });

  describe('ErrorMessage', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.restoreAllMocks();
      vi.useRealTimers();
    });

    it('should render error message', () => {
      render(<ErrorMessage message="Something went wrong" />);

      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('should call onDismiss when dismiss button is clicked', async () => {
      const onDismiss = vi.fn();

      render(<ErrorMessage message="Error occurred" onDismiss={onDismiss} autoDismiss={false} />);

      const dismissButton = screen.getByLabelText('Dismiss error');
      fireEvent.click(dismissButton);

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('should auto-dismiss after default timeout', async () => {
      const onDismiss = vi.fn();

      render(<ErrorMessage message="Auto dismiss test" onDismiss={onDismiss} />);

      expect(screen.getByText('Auto dismiss test')).toBeInTheDocument();

      // Fast-forward time by 5000ms (default timeout)
      await act(async () => {
        await vi.advanceTimersByTimeAsync(5000);
      });

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('should auto-dismiss after custom timeout', async () => {
      const onDismiss = vi.fn();

      render(
        <ErrorMessage
          message="Custom timeout test"
          onDismiss={onDismiss}
          dismissTimeout={3000}
        />
      );

      expect(screen.getByText('Custom timeout test')).toBeInTheDocument();

      // Fast-forward time by 3000ms
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000);
      });

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('should not auto-dismiss when autoDismiss is false', async () => {
      const onDismiss = vi.fn();

      render(
        <ErrorMessage
          message="No auto dismiss"
          onDismiss={onDismiss}
          autoDismiss={false}
        />
      );

      expect(screen.getByText('No auto dismiss')).toBeInTheDocument();

      // Fast-forward time
      await vi.advanceTimersByTimeAsync(10000);

      expect(screen.getByText('No auto dismiss')).toBeInTheDocument();
      expect(onDismiss).not.toHaveBeenCalled();
    });

    it('should not render dismiss button when onDismiss is not provided', () => {
      render(<ErrorMessage message="No dismiss button" />);

      expect(screen.queryByLabelText('Dismiss error')).not.toBeInTheDocument();
    });

    it('should hide error message after dismissal', () => {
      const onDismiss = vi.fn();

      render(<ErrorMessage message="Will be dismissed" onDismiss={onDismiss} autoDismiss={false} />);

      expect(screen.getByText('Will be dismissed')).toBeInTheDocument();

      const dismissButton = screen.getByLabelText('Dismiss error');
      fireEvent.click(dismissButton);

      expect(screen.queryByText('Will be dismissed')).not.toBeInTheDocument();
    });

    it('should apply custom className', () => {
      const { container } = render(
        <ErrorMessage message="Custom class" className="my-error-class" />
      );

      const errorDiv = container.querySelector('.my-error-class');
      expect(errorDiv).toBeInTheDocument();
    });

    it('should have proper ARIA attributes', () => {
      render(<ErrorMessage message="Accessible error" />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('should display error icon', () => {
      const { container } = render(<ErrorMessage message="Error with icon" />);

      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg).toHaveAttribute('aria-hidden', 'true');
    });

    it('should not auto-dismiss when dismissTimeout is 0', async () => {
      const onDismiss = vi.fn();

      render(
        <ErrorMessage
          message="No timeout"
          onDismiss={onDismiss}
          dismissTimeout={0}
        />
      );

      await vi.advanceTimersByTimeAsync(10000);

      expect(screen.getByText('No timeout')).toBeInTheDocument();
      expect(onDismiss).not.toHaveBeenCalled();
    });
  });

  describe('ConfirmDialog', () => {
    beforeEach(() => {
      // Mock body style
      document.body.style.overflow = 'unset';
    });

    afterEach(() => {
      document.body.style.overflow = 'unset';
    });

    it('should not render when isOpen is false', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={false}
        />
      );

      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });

    it('should render when isOpen is true', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Confirm Action')).toBeInTheDocument();
      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
    });

    it('should call onConfirm when confirm button is clicked', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      await userEvent.click(confirmButton);

      expect(onConfirm).toHaveBeenCalledTimes(1);
      expect(onCancel).not.toHaveBeenCalled();
    });

    it('should call onCancel when cancel button is clicked', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await userEvent.click(cancelButton);

      expect(onCancel).toHaveBeenCalledTimes(1);
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('should use custom button text', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Delete Item"
          message="This action cannot be undone"
          onConfirm={onConfirm}
          onCancel={onCancel}
          confirmText="Delete"
          cancelText="Keep"
          isOpen={true}
        />
      );

      expect(screen.getByRole('button', { name: 'Delete' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Keep' })).toBeInTheDocument();
    });

    it('should call onCancel when backdrop is clicked', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const backdrop = screen.getByRole('dialog');
      await userEvent.click(backdrop);

      expect(onCancel).toHaveBeenCalledTimes(1);
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('should call onCancel when Escape key is pressed', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      await userEvent.keyboard('{Escape}');

      expect(onCancel).toHaveBeenCalledTimes(1);
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('should prevent body scroll when open', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');
    });

    it('should restore body scroll when closed', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      const { rerender } = render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      expect(document.body.style.overflow).toBe('hidden');

      rerender(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={false}
        />
      );

      expect(document.body.style.overflow).toBe('unset');
    });

    it('should have proper ARIA attributes', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'dialog-title');

      const title = screen.getByText('Confirm Action');
      expect(title).toHaveAttribute('id', 'dialog-title');
    });

    it('should not call onCancel when clicking inside dialog content', async () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const message = screen.getByText('Are you sure?');
      await userEvent.click(message);

      expect(onCancel).not.toHaveBeenCalled();
      expect(onConfirm).not.toHaveBeenCalled();
    });

    it('should display title and message correctly', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Delete Account"
          message="This will permanently delete your account and all associated data."
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      expect(screen.getByText('Delete Account')).toBeInTheDocument();
      expect(
        screen.getByText('This will permanently delete your account and all associated data.')
      ).toBeInTheDocument();
    });

    it('should have destructive styling on confirm button', () => {
      const onConfirm = vi.fn();
      const onCancel = vi.fn();

      render(
        <ConfirmDialog
          title="Confirm Action"
          message="Are you sure?"
          onConfirm={onConfirm}
          onCancel={onCancel}
          isOpen={true}
        />
      );

      const confirmButton = screen.getByRole('button', { name: /confirm/i });
      expect(confirmButton).toHaveClass('bg-red-600');
    });
  });
});
