! rule: S9.7.3.2-004
! covers: saved-local-control
! A SAVE allocatable is proved allocated on re-entry, contrasting the unsaved automatic case.
module dealloc_saved_local_control_m
  implicit none
  integer :: checks = 0
contains
  subroutine visit(pass)
    integer, intent(in) :: pass
    integer, allocatable, save :: retained(:)
    integer :: stat
    if (pass == 1) then
      if (allocated(retained)) error stop 'D9732:saved-local:first-entry'
      checks = checks + 1
      allocate(retained(-8:-6), stat=stat)
      if (stat /= 0) error stop 'D9732:saved-local:allocate-stat'
      retained = [139, 149, 151]
      if (.not. allocated(retained)) error stop 'D9732:saved-local:before-allocated'
      checks = checks + 1
      if (lbound(retained,1) /= -8) error stop 'D9732:saved-local:before-lower'
      checks = checks + 1
      if (ubound(retained,1) /= -6) error stop 'D9732:saved-local:before-upper'
      checks = checks + 1
      if (any(retained /= [139, 149, 151])) error stop 'D9732:saved-local:before-values'
      checks = checks + 1
      return
    end if
    if (.not. allocated(retained)) error stop 'D9732:saved-local:retained-allocated'
    checks = checks + 1
    if (lbound(retained,1) /= -8) error stop 'D9732:saved-local:retained-lower'
    checks = checks + 1
    if (ubound(retained,1) /= -6) error stop 'D9732:saved-local:retained-upper'
    checks = checks + 1
    if (any(retained /= [139, 149, 151])) error stop 'D9732:saved-local:retained-values'
    checks = checks + 1
    deallocate(retained, stat=stat)
    if (stat /= 0) error stop 'D9732:saved-local:cleanup-stat'
    checks = checks + 1
    if (allocated(retained)) error stop 'D9732:saved-local:cleanup-unallocated'
    checks = checks + 1
  end subroutine visit
end module dealloc_saved_local_control_m

program dealloc_saved_local_control
  use dealloc_saved_local_control_m
  implicit none
  call visit(1)
  call visit(2)
  if (checks /= 11) error stop 'D9732:saved-local:check-total'
  write(*,'(a)') 'DEALLOC SAVED LOCAL CONTROL OK'
end program dealloc_saved_local_control
