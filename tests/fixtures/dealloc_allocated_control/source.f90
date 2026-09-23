! rule: S9.7.3.2-001
! covers: allocated-control-no-error
! A positive allocated state is established before DEALLOCATE; only ALLOCATED is queried after.
program dealloc_allocated_control
  implicit none
  integer, allocatable :: x(:)
  integer :: stat, checks
  checks = 0

  allocate(x(-9:-7), stat=stat)
  if (stat /= 0) error stop 'D9732:allocated:allocate-stat'
  x = [67, 71, 73]
  if (.not. allocated(x)) error stop 'D9732:allocated:before-allocated'
  checks = checks + 1
  if (lbound(x,1) /= -9) error stop 'D9732:allocated:before-lower'
  checks = checks + 1
  if (ubound(x,1) /= -7) error stop 'D9732:allocated:before-upper'
  checks = checks + 1
  if (any(x /= [67, 71, 73])) error stop 'D9732:allocated:before-values'
  checks = checks + 1

  deallocate(x, stat=stat)
  if (stat /= 0) error stop 'D9732:allocated:deallocate-stat'
  checks = checks + 1
  if (allocated(x)) error stop 'D9732:allocated:after-unallocated'
  checks = checks + 1

  allocate(x(4:6), stat=stat)
  if (stat /= 0) error stop 'D9732:allocated:reallocate-stat'
  x = [79, 83, 89]
  if (lbound(x,1) /= 4) error stop 'D9732:allocated:realloc-lower'
  checks = checks + 1
  if (ubound(x,1) /= 6) error stop 'D9732:allocated:realloc-upper'
  checks = checks + 1
  if (any(x /= [79, 83, 89])) error stop 'D9732:allocated:realloc-values'
  checks = checks + 1
  if (checks /= 9) error stop 'D9732:allocated:check-total'
  write(*,'(a)') 'DEALLOC ALLOCATED CONTROL OK'
end program dealloc_allocated_control
