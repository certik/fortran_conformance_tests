! rule: S9.7.3.2-004
! covers: ordinary-unsaved-local-deallocated
! First invocation proves allocation; second invocation observes the unsaved local starts unallocated.
module dealloc_procedure_local_auto_m
  implicit none
  integer :: checks = 0
contains
  subroutine visit(pass)
    integer, intent(in) :: pass
    integer, allocatable :: scratch(:)
    integer :: stat
    if (allocated(scratch)) error stop 'D9732:proc-local:entry-unallocated'
    checks = checks + 1
    if (pass == 1) then
      allocate(scratch(-4:-2), stat=stat)
      if (stat /= 0) error stop 'D9732:proc-local:first-stat'
      scratch = [107, 109, 113]
      if (.not. allocated(scratch)) error stop 'D9732:proc-local:first-allocated'
      checks = checks + 1
      if (lbound(scratch,1) /= -4) error stop 'D9732:proc-local:first-lower'
      checks = checks + 1
      if (ubound(scratch,1) /= -2) error stop 'D9732:proc-local:first-upper'
      checks = checks + 1
      if (any(scratch /= [107, 109, 113])) error stop 'D9732:proc-local:first-values'
      checks = checks + 1
      return
    end if
    allocate(scratch(6:8), stat=stat)
    if (stat /= 0) error stop 'D9732:proc-local:second-stat'
    scratch = [127, 131, 137]
    if (lbound(scratch,1) /= 6) error stop 'D9732:proc-local:second-lower'
    checks = checks + 1
    if (ubound(scratch,1) /= 8) error stop 'D9732:proc-local:second-upper'
    checks = checks + 1
    if (any(scratch /= [127, 131, 137])) error stop 'D9732:proc-local:second-values'
    checks = checks + 1
  end subroutine visit
end module dealloc_procedure_local_auto_m

program dealloc_procedure_local_auto
  use dealloc_procedure_local_auto_m
  implicit none
  call visit(1)
  call visit(2)
  if (checks /= 9) error stop 'D9732:proc-local:check-total'
  write(*,'(a)') 'DEALLOC PROCEDURE LOCAL AUTO OK'
end program dealloc_procedure_local_auto
