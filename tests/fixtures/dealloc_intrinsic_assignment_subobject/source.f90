! rule: S9.7.3.2-009
! covers: intrinsic-assignment-noncoarray-subobject-before-assignment
! The left allocatable component is proved allocated before intrinsic assignment and unallocated after.
program dealloc_intrinsic_assignment_subobject
  implicit none
  type :: holder
    integer :: tag = -1
    integer, allocatable :: part(:)
  end type holder
  type(holder) :: lhs, rhs
  integer :: stat, checks
  checks = 0
  allocate(lhs%part(-6:-4), stat=stat)
  if (stat /= 0) error stop 'D9732:assignment:allocate-stat'
  lhs%tag = 269
  lhs%part = [271, 277, 281]
  rhs%tag = 283
  if (.not. allocated(lhs%part)) error stop 'D9732:assignment:before-allocated'
  checks = checks + 1
  if (lbound(lhs%part,1) /= -6) error stop 'D9732:assignment:before-lower'
  checks = checks + 1
  if (ubound(lhs%part,1) /= -4) error stop 'D9732:assignment:before-upper'
  checks = checks + 1
  if (lhs%tag /= 269) error stop 'D9732:assignment:before-tag'
  checks = checks + 1
  if (any(lhs%part /= [271, 277, 281])) error stop 'D9732:assignment:before-values'
  checks = checks + 1
  if (allocated(rhs%part)) error stop 'D9732:assignment:rhs-unallocated'
  checks = checks + 1

  lhs = rhs

  if (lhs%tag /= 283) error stop 'D9732:assignment:after-tag'
  checks = checks + 1
  if (allocated(lhs%part)) error stop 'D9732:assignment:after-component-unallocated'
  checks = checks + 1
  if (checks /= 8) error stop 'D9732:assignment:check-total'
  write(*,'(a)') 'DEALLOC INTRINSIC ASSIGNMENT SUBOBJECT OK'
end program dealloc_intrinsic_assignment_subobject
