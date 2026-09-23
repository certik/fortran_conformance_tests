! rule: S9.7.3.2-008
! covers: intent-out-allocatable-actual-deallocated
! The caller proves the allocatable actual is allocated before invocation; the callee observes it unallocated on entry.
program dealloc_intent_out_actual
  implicit none
  integer, allocatable :: actual(:)
  integer :: stat, checks
  checks = 0
  allocate(actual(-4:-2), stat=stat)
  if (stat /= 0) error stop 'D9732:intent-out-actual:allocate-stat'
  actual = [191, 193, 197]
  if (.not. allocated(actual)) error stop 'D9732:intent-out-actual:before-allocated'
  checks = checks + 1
  if (lbound(actual,1) /= -4) error stop 'D9732:intent-out-actual:before-lower'
  checks = checks + 1
  if (ubound(actual,1) /= -2) error stop 'D9732:intent-out-actual:before-upper'
  checks = checks + 1
  if (any(actual /= [191, 193, 197])) error stop 'D9732:intent-out-actual:before-values'
  checks = checks + 1

  call replace_actual(actual, checks)

  if (.not. allocated(actual)) error stop 'D9732:intent-out-actual:after-allocated'
  checks = checks + 1
  if (lbound(actual,1) /= 8) error stop 'D9732:intent-out-actual:after-lower'
  checks = checks + 1
  if (ubound(actual,1) /= 10) error stop 'D9732:intent-out-actual:after-upper'
  checks = checks + 1
  if (any(actual /= [199, 211, 223])) error stop 'D9732:intent-out-actual:after-values'
  checks = checks + 1
  if (checks /= 9) error stop 'D9732:intent-out-actual:check-total'
  write(*,'(a)') 'DEALLOC INTENT OUT ACTUAL OK'
contains
  subroutine replace_actual(x, checks)
    integer, allocatable, intent(out) :: x(:)
    integer, intent(inout) :: checks
    integer :: stat
    if (allocated(x)) error stop 'D9732:intent-out-actual:callee-entry-unallocated'
    checks = checks + 1
    allocate(x(8:10), stat=stat)
    if (stat /= 0) error stop 'D9732:intent-out-actual:callee-allocate-stat'
    x = [199, 211, 223]
    if (lbound(x,1) /= 8) error stop 'D9732:intent-out-actual:callee-lower'
    if (ubound(x,1) /= 10) error stop 'D9732:intent-out-actual:callee-upper'
  end subroutine replace_actual
end program dealloc_intent_out_actual
