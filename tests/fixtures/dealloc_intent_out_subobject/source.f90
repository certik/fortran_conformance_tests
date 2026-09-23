! rule: S9.7.3.2-008
! covers: intent-out-actual-subobject-deallocated
! The allocatable component is allocated before invocation; INTENT(OUT) deallocates it before callee code.
program dealloc_intent_out_subobject
  implicit none
  type :: holder
    integer :: tag = -1
    integer, allocatable :: part(:)
  end type holder
  type(holder) :: actual
  integer :: stat, checks
  checks = 0
  allocate(actual%part(-7:-5), stat=stat)
  if (stat /= 0) error stop 'D9732:intent-out-subobject:allocate-stat'
  actual%tag = 227
  actual%part = [229, 233, 239]
  if (.not. allocated(actual%part)) error stop 'D9732:intent-out-subobject:before-allocated'
  checks = checks + 1
  if (lbound(actual%part,1) /= -7) error stop 'D9732:intent-out-subobject:before-lower'
  checks = checks + 1
  if (ubound(actual%part,1) /= -5) error stop 'D9732:intent-out-subobject:before-upper'
  checks = checks + 1
  if (actual%tag /= 227) error stop 'D9732:intent-out-subobject:before-tag'
  checks = checks + 1
  if (any(actual%part /= [229, 233, 239])) error stop 'D9732:intent-out-subobject:before-values'
  checks = checks + 1

  call reset_holder(actual, checks)

  if (.not. allocated(actual%part)) error stop 'D9732:intent-out-subobject:after-allocated'
  checks = checks + 1
  if (lbound(actual%part,1) /= 3) error stop 'D9732:intent-out-subobject:after-lower'
  checks = checks + 1
  if (ubound(actual%part,1) /= 5) error stop 'D9732:intent-out-subobject:after-upper'
  checks = checks + 1
  if (actual%tag /= 241) error stop 'D9732:intent-out-subobject:after-tag'
  checks = checks + 1
  if (any(actual%part /= [251, 257, 263])) error stop 'D9732:intent-out-subobject:after-values'
  checks = checks + 1
  if (checks /= 11) error stop 'D9732:intent-out-subobject:check-total'
  write(*,'(a)') 'DEALLOC INTENT OUT SUBOBJECT OK'
contains
  subroutine reset_holder(h, checks)
    type(holder), intent(out) :: h
    integer, intent(inout) :: checks
    integer :: stat
    if (allocated(h%part)) error stop 'D9732:intent-out-subobject:callee-entry-unallocated'
    checks = checks + 1
    allocate(h%part(3:5), stat=stat)
    if (stat /= 0) error stop 'D9732:intent-out-subobject:callee-allocate-stat'
    h%tag = 241
    h%part = [251, 257, 263]
    if (lbound(h%part,1) /= 3) error stop 'D9732:intent-out-subobject:callee-lower'
    if (ubound(h%part,1) /= 5) error stop 'D9732:intent-out-subobject:callee-upper'
  end subroutine reset_holder
end program dealloc_intent_out_subobject
